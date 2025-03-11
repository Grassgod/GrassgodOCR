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
from app.utils.log_config import setup_logger
from app.config.config import Config

# 设置日志记录器
logger = setup_logger('ocr_service')


class OCRService:
    def __init__(self):
        """初始化OCR服务"""
        config = Config.get_ocr_config()
        self.ocr = PaddleOCR(
            det_model_dir=config['det_dir'],
            rec_model_dir=config['rec_dir'],
            cls_model_dir=config['cls_dir'],
            rec_char_dict_path=config['rec_dict_path'],
            **Config.OCR_PARAMS
        )
        self.font_path = config['font_path']
        self.logger = logger  # 使用类实例变量存储logger
        
    @staticmethod
    def download_image(img_url):
        """从URL下载图片并返回二进制数据"""
        try:
            response = requests.get(img_url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image from {img_url}: {str(e)}")
            raise

    @staticmethod
    def convert_to_ndarray(image_data):
        """将图片二进制数据转换为numpy数组"""
        try:
            img = Image.open(BytesIO(image_data))
            return np.array(img)
        except Exception as e:
            logger.error(f"Failed to convert image to array: {str(e)}")
            raise

    def process_image(self, img_array):
        """处理图像并返回OCR结果"""
        try:
            result = self.ocr.ocr(img_array, cls=True)
            return result
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise

    @staticmethod
    def convert_image(image, threshold=None):
        """图像二值化处理"""
        try:
            threshold = threshold or Config.IMAGE_PROCESSING['default_threshold']
            logger.info(f"Converting image with threshold: {threshold}")
            
            image = image.convert("L")
            pixels = image.load()
            
            for x in range(image.width):
                for y in range(image.height):
                    pixels[x, y] = 255 if pixels[x, y] > threshold else 0
                    
            return image
        except Exception as e:
            logger.error(f"Image conversion failed: {str(e)}")
            raise

    def draw_result(self, img_path, result):
        """绘制OCR结果到图像上"""
        try:
            result = result[0]
            image = Image.open(img_path).convert('RGB')
            boxes = [line[0] for line in result]
            txts = [line[1][0] for line in result]
            scores = [line[1][1] for line in result]
            
            im_show = draw_ocr(image, boxes, txts, scores, font_path=self.font_path)
            im_show = Image.fromarray(im_show)
            im_show.save('result.jpg')
            logger.info("OCR result image saved successfully")
        except Exception as e:
            logger.error(f"Failed to draw OCR result: {str(e)}")
            raise

    def handle_ocr(self, img_path):
        """OCR处理主函数"""
        try:
            # 下载并处理图片
            image_data = self.download_image(img_path)
            img_array = self.convert_to_ndarray(image_data)
            
            # 执行OCR识别
            result = self.process_image(img_array)
            
            logger.info("OCR processing completed successfully")
            return {'result': result}
            
        except Exception as e:
            logger.error(f"OCR handling failed: {str(e)}")
            raise

# 创建OCR服务实例
ocr_service = OCRService()

def ocr_handler(img_path, current_index):
    """OCR处理入口函数"""
    try:
        return ocr_service.handle_ocr(img_path)
    except Exception as e:
        logger.error(f"OCR handler failed: {str(e)}")
        return {'error': str(e)}