from app.service.ocr import ocr_handler
import re
import os
from openai import OpenAI
import json


def extract_money(content):
    match = re.search(r'((\d{1,3}(,\d{3})*)|(\d+))(\.\d+)?元', content)
    if match:
        # 提取匹配的完整金额字符串，并移除千位分隔符
        amount_str = match.group(0).replace(',', '').replace('元', '')
        return amount_str
    return None

def extract_discount(content):
    match = re.search(r'-(\d+(\.\d+)?)元', content)
    if match:
        return match.group(1)
    return None

client = OpenAI(
    api_key='sk-a71fede4066d43009c248b96e9e1f197',
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def get_from_to(img_path):
    completion = client.chat.completions.create(
        model="qwen-vl-plus",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": '''
                        你是一个信息提取员,请根据图片提取以下信息:
                        1.出发地 
                        2.目的地 
                        结果按照JSON输出,回答只包含一个JSON, 不带有任何解释信息.
                        这个JSON的标准格式为:{"出发地":"地址","目的地":"地址"}
                        请注意, 不要编造任何数据, 请严格按照图片上内容输出, 不需要任何解释信息
                        如果图片上没有相关信息, 值为空. 
                        '''
                    },
                    {
                        "type": "image_url", 
                        "image_url": {
                            "url": img_path
                        }
                    }
                ]
            }
        ]
    )

    result = completion.model_dump_json()
    result = json.loads(result)['choices'][0]['message']['content'].replace("```json\n","").replace("\n```","")
    result = json.loads(result)
    return result


def call_taxi(img_path, request_idx):

    req_data = {}

    result = get_from_to(img_path)

    req_data['from'] = result['出发地']
    req_data['to'] = result['目的地']

    ocr_result = ocr_handler(img_path, request_idx)
    ocr_result = ocr_result['result'][0]

    search_key = {}

    count = 0
    for i in ocr_result:
        count += 1
        position = i[0]
        content = i[1][0]
        score = i[1][1]
        # print(position)

        # 找到x和y的最大最小
        x = [i[0] for i in position]
        y = [i[1] for i in position]
        x_min = min(x) 
        x_max = max(x)
        y_min = min(y)
        y_max = max(y)
        # 确定x和y的最大最小
        print(content,x_min, x_max, y_min, y_max)
        search_key[count] = {
            'x_min': x_min,
            'x_max': x_max,
            'y_min': y_min,
            'y_max': y_max,
            'content': content
        }
    # print(search_key)
    req = []
    for i in search_key:
        if  ("滴滴" in search_key[i]['content'] or "特惠" in search_key[i]['content'] or "六座商务" in search_key[i]['content']) and ("滴滴旗下品牌" not in search_key[i]['content']):
            print('===================')
            print(search_key[i])
            ans = {}
            ans["carType"] = search_key[i]['content']
            base = search_key[i]
            for j in search_key:
                compare = search_key[j]
                if compare['x_min']>base['x_max']:
                    # 判断compare和base的y轴存在交叉
                    if compare['y_min']<base['y_max'] and compare['y_max']>base['y_min']:
                        if '-' not in compare['content'] and '元' in compare['content']:
                            print(j,search_key[j])
                            ans['price'] = extract_money(compare['content'])
                            min_dis = 100000
                            min_key = ''
                            for k in search_key:
                                compare2 = search_key[k]
                                if compare2['x_min']>base['x_max'] and compare2['y_min']-compare['y_max']>=-20 and compare2['y_min']-compare['y_max']<min_dis:
                                    min_dis = compare2['y_min']-compare['y_max']
                                    min_key = k
                                    print('更新', compare2)
                            if min_key != '' and '-' in search_key[min_key]['content']:
                                ans['discount'] = extract_discount(search_key[min_key]['content'])
                            print(search_key[min_key]['content'])
            req.append(ans)

    req_data['cars'] = req                 
    return req_data

# if __name__ == '__main__':
#     # 打开flask服务
#     img_url = 'https://img2024.cnblogs.com/blog/2948873/202502/2948873-20250207093241163-1721281799.jpg'
#     req = call_taxi(img_url, 1)

#     print(req)