from app.service.ocr import ocr_handler
import re
import os
from openai import OpenAI
import json
import requests
from io import BytesIO
from app.utils.log_config import setup_logger
from app.config.config import Config

# 设置日志记录器
logger = setup_logger('taxi_service')

class TaxiService:
    def __init__(self):
        """初始化打车服务"""
        self.client = OpenAI(**Config.OPENAI_CONFIG)

    @staticmethod
    def format_number(text):
        """格式化数字"""
        return re.sub(r',|\.(?=.*\.)', '', text)

    @staticmethod
    def extract_money(content):
        """提取金额"""
        try:
            content = content.replace(' ', '').replace('，', ',').replace('。', '.')
            match = re.search(r'-?\d{1,3}(?:[,.]\d{3})*(?:[,.，。]\d{1,2})?', content)
            if not match:
                return None

            amount_str = match.group(0)
            cleaned = re.sub(r'[,.，。]', '', amount_str)

            if '.' in amount_str or ',' in amount_str or '，' in amount_str or '。' in amount_str:
                if '.' == amount_str[-3] or ',' == amount_str[-3] or '.' == amount_str[-2] or ',' == amount_str[-2] or '，' == amount_str[-2] or '。' == amount_str[-2] or '，' == amount_str[-3] or '。' == amount_str[-3]:
                    last_dot_index = amount_str.rfind(r'[,.，。]')
                    if '.' == amount_str[-3] or ',' == amount_str[-3] or '，' == amount_str[-3] or '。' == amount_str[-3]:
                        cleaned = f"{cleaned[:last_dot_index-1]}.{cleaned[last_dot_index-1:]}"
                    else:
                        cleaned = f"{cleaned[:last_dot_index]}.{cleaned[last_dot_index:]}"

            return cleaned
        except Exception as e:
            logger.error(f"Error extracting money: {str(e)}")
            return None

    @staticmethod
    def extract_discount(content):
        """提取折扣"""
        try:
            match = re.search(r'-(\d+(\.\d+)?)', content)
            return TaxiService.format_number(match.group(1)) if match else None
        except Exception as e:
            logger.error(f"Error extracting discount: {str(e)}")
            return None

    def get_from_to(self, img_path):
        """获取起点和终点信息"""
        try:
            completion = self.client.chat.completions.create(
                model="qwen-vl-plus",
                messages=[{
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
                            "image_url": {"url": img_path}
                        }
                    ]
                }]
            )

            result = completion.model_dump_json()
            result = json.loads(result)['choices'][0]['message']['content']
            result = result.replace("```json\n", "").replace("\n```", "")
            return json.loads(result)
        except Exception as e:
            logger.error(f"Error getting from/to information: {str(e)}")
            raise

    def process_car_info(self, search_key):
        """处理车辆信息"""
        req = []
        try:
            for i in search_key:
                if ("滴滴" in search_key[i]['content'] or 
                    "特惠快车" in search_key[i]['content'] or 
                    "六座商务" in search_key[i]['content']) and \
                   ("滴滴旗下品牌" not in search_key[i]['content']):
                    
                    logger.info(f"Found taxi type: {search_key[i]}")
                    ans = {}
                    ans["carType"] = '特惠快车' if search_key[i]['content'] == '惠特惠快车' else search_key[i]['content']
                    
                    base = search_key[i]
                    self._process_price_and_discount(search_key, base, ans)
                    req.append(ans)
            return req
        except Exception as e:
            logger.error(f"Error processing car info: {str(e)}")
            raise

    def _process_price_and_discount(self, search_key, base, ans):
        """处理价格和折扣信息"""
        try:
            for j in search_key:
                compare = search_key[j]
                if (compare['x_min'] > base['x_max'] and 
                    compare['y_min'] < base['y_max'] and 
                    compare['y_max'] > base['y_min']):
                    
                    logger.info(f"Found price info: {search_key[j]}")
                    ans['price'] = self.extract_money(compare['content'])
                    
                    # 查找折扣信息
                    min_dis = float('inf')
                    min_key = ''
                    for k in search_key:
                        compare2 = search_key[k]
                        if (compare2['x_min'] > base['x_max'] and 
                            -20 <= compare2['y_min'] - compare['y_max'] < min_dis):
                            min_dis = compare2['y_min'] - compare['y_max']
                            min_key = k
                    
                    if min_key and '-' in search_key[min_key]['content']:
                        ans['discount'] = self.extract_discount(search_key[min_key]['content'])
                        logger.info(f"Found discount: {search_key[min_key]['content']}")
                    break
        except Exception as e:
            logger.error(f"Error processing price and discount: {str(e)}")
            raise

    def call_taxi(self, img_path, request_idx):
        """打车服务主函数"""
        req_data = {}
        
        try:
            # 获取起点和终点信息
            result = self.get_from_to(img_path)
            logger.info(f"Get from/to result: {result}")
            
            req_data['from'] = result.get('出发地', '')
            req_data['to'] = result.get('目的地', '')

            # 获取OCR结果
            ocr_result = ocr_handler(img_path, request_idx)
            if 'error' in ocr_result:
                logger.error(f"OCR error: {ocr_result['error']}")
                req_data['status'] = 'analysisError'
                return req_data

            # 处理OCR结果
            search_key = self._process_ocr_result(ocr_result['result'][0])
            
            # 处理车辆信息
            req_data['cars'] = self.process_car_info(search_key)
            req_data['status'] = 'success'
            
            logger.info(f"Successfully processed request. Result: {req_data}")
            return req_data

        except Exception as e:
            logger.error(f"Error in call_taxi: {str(e)}")
            req_data['status'] = 'unknownError'
            return req_data

    def _process_ocr_result(self, ocr_result):
        """处理OCR结果"""
        search_key = {}
        try:
            for i, item in enumerate(ocr_result, 1):
                position = item[0]
                content = item[1][0]
                
                x = [p[0] for p in position]
                y = [p[1] for p in position]
                
                search_key[i] = {
                    'x_min': min(x),
                    'x_max': max(x),
                    'y_min': min(y),
                    'y_max': max(y),
                    'content': content
                }

                if "代驾" in content or "顺风车" in content:
                    raise Exception("代驾或顺风车")
                
                logger.info(f"OCR content: {content}, Position: x_min={min(x)}, x_max={max(x)}, y_min={min(y)}, y_max={max(y)}")
            
            return search_key
        except Exception as e:
            logger.error(f"Error processing OCR result: {str(e)}")
            raise

# 创建打车服务实例
taxi_service = TaxiService()

def call_taxi_handler(img_path, request_idx):
    """打车服务入口函数"""
    return taxi_service.call_taxi(img_path, request_idx)

# if __name__ == '__main__':
#     # 打开flask服务
#     img_url = 'https://img2024.cnblogs.com/blog/2948873/202502/2948873-20250207093241163-1721281799.jpg'
#     req = call_taxi(img_url, 1)

#     print(req)