print("loading ocr.py")
from paddleocr import PaddleOCR
print("paddleocr loaded")
# from PIL import Image, ImageDraw
# import numpy as np
 
'''
自定义模型测试ocr方法
'''

det_dir = '../model/v4/ch_PP-OCRv4_det_infer/'
rec_dir = '../model/v4/ch_PP-OCRv4_rec_infer/'
cls_dir = '../model/v4/ch_ppocr_mobile_v2.0_cls_infer/'
rec_dict_dir = '../model/v4/ppocr_keys_v1.txt' 

def test_model_ocr(img):
    # paddleocr 目前支持的多语言语种可以通过修改lang参数进行切换
    # 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
    # 使用CPU预加载，不用GPU
    # 模型路径下必须包含model和params文件，目前开源的v3版本模型 已经是识别率很高的了
    # 还要更好的就要自己训练模型了。

    print("loading ocr model")
 
    ocr = PaddleOCR(det_model_dir = det_dir,
                    rec_model_dir = rec_dir,
                    cls_model_dir = cls_dir,
                    rec_char_dict_path = rec_dict_dir,
                    use_angle_cls=True, lang="ch", use_gpu=False)
    
    print("ocr model loaded")
 
    # 识别图片文件
    result = ocr.ocr(img, cls=True)
    return result
 
 
# 打印所有结果信息
def print_ocr_result(result):
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
 
 
# 转换图片
# def convert_image(image, threshold=None):
#     # 阈值 控制二值化程度，不能超过256，[200, 256]
#     # 适当调大阈值，可以提高文本识别率，经过测试有效。
#     if threshold is None:
#         threshold = 200
#     print('threshold : ', threshold)
#     # 首先进行图片灰度处理
#     image = image.convert("L")
#     pixels = image.load()
#     # 在进行二值化
#     for x in range(image.width):
#         for y in range(image.height):
#             if pixels[x, y] > threshold:
#                 pixels[x, y] = 255
#             else:
#                 pixels[x, y] = 0
#     return image
 
 
if __name__ == "__main__":
    img_path = r"/Users/grassgod/Documents/Code/GrassgodOCR/app/img/WechatIMG66.jpg"
    # 1，直接识别图片文本
    print('1，直接识别图片文本')
    result1 = test_model_ocr(img_path)
    # 打印所有结果信息
    print_ocr_result(result1)