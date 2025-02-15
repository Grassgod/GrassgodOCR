import os
from openai import OpenAI
import json
import time

client = OpenAI(
    api_key='sk-a71fede4066d43009c248b96e9e1f197',
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
def call_vl(img_path):
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

    result = json.loads(result)

    result = result['choices'][0]['message']['content']

    result = result.replace("```json\n","").replace("\n```","")

    result = json.loads(result)

    return result

# img_path = "https://img2024.cnblogs.com/blog/2948873/202502/2948873-20250207093241163-1721281799.jpg"

# result = call_vl(img_path)
# print(result)