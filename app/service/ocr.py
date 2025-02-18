from paddleocr import PaddleOCR, draw_ocr
# from PIL import Image, ImageDraw
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2
import numpy as np
import threading
from flask import jsonify
import requests
from io import BytesIO
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
# import numpy as np
 
'''
自定义模型测试ocr方法
'''

det_dir = '../model/v_0.1/det_infer/'
rec_dir = '../model/v_0.1/rec_infer/'
cls_dir = '../model/v_0.1/cls_infer/'
# rec_dict_dir = '/Users/grassgod/Documents/Code/GrassgodOCR/app/model/v_0.1/keys_v1.txt' 
rec_dict_dir = '/dev/shm/GrassgodOCR/app/model/v_0.1/keys_v1.txt'


# ocr_instances = [PaddleOCR(det_model_dir = det_dir,
#                     rec_model_dir = rec_dir,
#                     cls_model_dir = cls_dir,
#                     rec_char_dict_path = rec_dict_dir,
#                     use_angle_cls=True, lang="ch", use_gpu=True) for _ in range(5)]
# locks = [threading.Lock() for _ in range(5)]


 
 
# 打印所有结果信息
def postprocess_ocr_result(result):
    # print(result)
    for index in range(len(result)):
        rst = result[index]
        for line in rst:
            points = line[0]
            text = line[1][0]
            score = line[1][1]
            print('points : ', points)
            print('text : ', text)
            print('score : ', score)
        print('==========================================')

# 初始化PaddleOCR对象
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # 根据需要设置语言

def download_image(img_url):
    """
    从给定的URL下载图片并返回其二进制数据。
    """
    response = requests.get(img_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image from {img_url}")
    return response.content

def convert_to_ndarray(image_data):
    """
    将图片的二进制数据转换为numpy数组。
    """
    img = Image.open(BytesIO(image_data))
    img_array = np.array(img)
    return img_array
    

def model_ocr(ocr, img):
    # paddleocr 目前支持的多语言语种可以通过修改lang参数进行切换
    # 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
    # 使用CPU预加载，不用GPU
    # 模型路径下必须包含model和params文件，目前开源的v3版本模型 已经是识别率很高的了
    # 还要更好的就要自己训练模型了。

    """
    使用PaddleOCR对给定URL的图片进行OCR处理。
    """
    # 下载图片
    image_data = download_image(img)
    
    # 将图片数据转换为numpy数组
    img_array = convert_to_ndarray(image_data)
    
    # 使用PaddleOCR进行OCR处理
    result = ocr.ocr(img_array, cls=True)
    
    return result
 
 
# 转换图片
def convert_image(image, threshold=None):
    # 阈值 控制二值化程度，不能超过256，[200, 256]
    # 适当调大阈值，可以提高文本识别率，经过测试有效。
    if threshold is None:
        threshold = 200
    print('threshold : ', threshold)
    # 首先进行图片灰度处理
    image = image.convert("L")
    pixels = image.load()
    # 在进行二值化
    for x in range(image.width):
        for y in range(image.height):
            if pixels[x, y] > threshold:
                pixels[x, y] = 255
            else:
                pixels[x, y] = 0
    return image

def draw_ocr_result(img_path, result):
    from PIL import Image
    result = result[0]
    image = Image.open(img_path).convert('RGB')
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    im_show = draw_ocr(image, boxes, txts, scores, font_path='app/model/simfang.ttf')
    im_show = Image.fromarray(im_show)
    im_show.save('result.jpg')


def ocr_handler(img_path,current_index):
    # print(img_path, cusrrent_index)
    # img_file = None
    # with open(img_path, 'r') as f:
    #     img_file = f.readfile()
 
    # Get the index of the OCR instance to use
    # model_index = id(current_index) % len(ocr_instances)
    # ocr = ocr_instances[model_index]
    ocr = PaddleOCR(det_model_dir = det_dir,
                    rec_model_dir = rec_dir,
                    cls_model_dir = cls_dir,
                    rec_char_dict_path = rec_dict_dir,
                    use_angle_cls=True, lang="ch", use_gpu=True,det_db_box_thresh = 0.3)
 
    # Acquire the lock for the OCR instance
    # lock = locks[model_index]
    # lock.acquire()
    # print("model_index", model_index)
    try:
        result = model_ocr(ocr, img_path)
 
        return {'result': result}
    except Exception as e:
        print(e)
        # Release the lock after OCR processing is complete
        # lock.release()
 
# if __name__ == "__main__":
#     img_path = r"/Users/grassgod/Desktop/打车截图/微信图片_20250124144041.jpg"
#     print(ocr_handler(img_path,1))