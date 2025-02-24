from app.service.ocr import ocr_handler
import re
import os
from openai import OpenAI
import json
import requests
from io import BytesIO


def format_number(text):
    # 移除逗号和中间的小数点
    return re.sub(r',|\.(?=.*\.)', '', text)

def extract_money(content):
    # 匹配数字部分（含错误格式）
    match = re.search(r'-?\d{1,3}(?:[,.]\d{3})*(?:[,.]\d{1,2})?', content)
    if not match:
        return None
    
    # 统一处理分隔符
    amount_str = match.group(0)
    
    # 移除所有逗号和中间的小数点
    cleaned = re.sub(r'[,.]', '', amount_str)

    # 还原最后一个小数点（如果有）
    if '.' == amount_str[-3] or ',' == amount_str[-3] or '.' == amount_str[-2] or ',' == amount_str[-2]:
        last_dot_index = amount_str.rfind(r'[,.]')
        if '.' == amount_str[-3] or ',' == amount_str[-3]:
            cleaned = f"{cleaned[:last_dot_index-1]}.{cleaned[last_dot_index-1:]}"
        else:
            cleaned = f"{cleaned[:last_dot_index]}.{cleaned[last_dot_index:]}"
    
    # return float(cleaned) if '.' in cleaned else int(cleaned)
    return cleaned

def extract_discount(content):
    match = re.search(r'-(\d+(\.\d+)?)', content)
    if match:
        return format_number(match.group(1))
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
                        1.出发地:出发地是一个具体地址，非省市区
                        2.目的地:目的地是一个具体地址，非省市区
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

    result = {}

    try:
        result = get_from_to(img_path)
    except Exception as e:
        print(e)
        req_data['status'] = 'modelError'
        return req_data

    print(result)

    req_data['from'] = result.get('出发地', '')
    req_data['to'] = result.get('目的地','')

    try:

        ocr_result = ocr_handler(img_path, request_idx)
        ocr_result = ocr_result['result'][0]
    except Exception as e:
        print(e)
        print('ocr error')
        req_data['status'] = 'analysisError'
        return req_data

    search_key = {}

    # try :
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
        if  ("滴滴" in search_key[i]['content'] or "特惠快车" in search_key[i]['content'] or "六座商务" in search_key[i]['content']) and ("滴滴旗下品牌" not in search_key[i]['content']):
            print('===================')
            print(search_key[i])
            ans = {}
            if search_key[i]['content'] == '惠特惠快车':
                ans["carType"] = '特惠快车'
            else:
                ans["carType"] = search_key[i]['content']
            base = search_key[i]
            flag = 0
            for j in search_key:
                compare = search_key[j]
                if compare['x_min']>base['x_max']:
                    # 判断compare和base的y轴存在交叉
                    if compare['y_min']<base['y_max'] and compare['y_max']>base['y_min']:
                        # if '元' in compare['content']:
                        if flag == 0:
                            flag = 1
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
    # except Exception as e:
    #     print('search error')
    #     print(e)
    #     req_data['status'] = 'unknownError'
    #     return req_data
    req_data['cars'] = req 
    req_data['status'] = 'success'                
    return req_data

# if __name__ == '__main__':
#     # 打开flask服务
#     img_url = 'https://img2024.cnblogs.com/blog/2948873/202502/2948873-20250207093241163-1721281799.jpg'
#     req = call_taxi(img_url, 1)

#     print(req)