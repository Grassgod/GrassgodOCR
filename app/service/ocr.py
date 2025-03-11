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
import paddle
import logging

# 设置日志记录器
logger = setup_logger('ocr_service')

# 设置环境变量
os.environ['FLAGS_call_stack_level'] = '2'
os.environ['FLAGS_allocator_strategy'] = 'naive_best_fit'
os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0.5'
os.environ['FLAGS_initial_gpu_memory_in_mb'] = '500'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

class OCRService:
    def __init__(self):
        """初始化OCR服务"""
        self.logger = logging.getLogger(__name__)
        
        # 检查CUDA是否可用
        try:
            if not paddle.device.is_compiled_with_cuda():
                self.logger.warning("PaddlePaddle未编译CUDA支持，将使用CPU模式")
                self.use_gpu = False
            else:
                paddle.device.set_device('gpu')
                # 设置GPU内存策略
                paddle.device.cuda.set_memory_fraction(0.5)
                self.use_gpu = True
                self.logger.info(f"使用GPU设备: {paddle.device.get_device()}")
        except Exception as e:
            self.logger.warning(f"GPU初始化失败，将使用CPU模式: {str(e)}")
            self.use_gpu = False

        # try:
        #     # 初始化OCR引擎
        #     self.ocr = PaddleOCR(
        #         use_angle_cls=True,
        #         use_gpu=self.use_gpu,
        #         lang='ch',
        #         show_log=False,
        #         use_mp=True,
        #         total_process_num=1,
        #         cpu_threads=4 if not self.use_gpu else 1
        #     )
        #     self.logger.info("OCR引擎初始化成功")
        # except Exception as e:
        #     self.logger.error(f"OCR引擎初始化失败: {str(e)}")
        #     raise

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
            # 确保输入图像格式正确
            if not isinstance(img_array, np.ndarray):
                raise ValueError("输入必须是numpy数组")

            # 图像预处理
            if img_array.ndim == 2:  # 如果是灰度图
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:  # 如果是RGBA
                img_array = img_array[:, :, :3]

            # 执行OCR识别
            with paddle.no_grad():  # 禁用梯度计算
                ocr = PaddleOCR(
                    use_angle_cls=True,
                    use_gpu=self.use_gpu,
                    lang='ch',
                    show_log=False,
                    use_mp=True,
                    total_process_num=1,
                    cpu_threads=4 if not self.use_gpu else 1
                )
                self.logger.info("OCR引擎初始化成功")
                result = ocr.ocr(img_array, cls=True)

            if not result:
                self.logger.warning("未检测到文本")
                return []

            # 处理结果
            # processed_result = []
            # try:
            #     for line in result[0]:  # result[0]包含了所有检测到的文本行
            #         if isinstance(line, (list, tuple)) and len(line) >= 2:
            #             box = line[0]  # 文本框坐标
            #             text_info = line[1]  # 文本信息和置信度
            #             if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
            #                 text = text_info[0]  # 文本内容
            #                 confidence = float(text_info[1])  # 置信度
            #                 if confidence > 0.5:  # 过滤低置信度的结果
            #                     processed_result.append({
            #                         'text': text,
            #                         'confidence': confidence,
            #                         'box': box
            #                     })
            # except Exception as e:
            #     self.logger.error(f"处理OCR结果时出错: {str(e)}")
            #     return []

            return result

        except Exception as e:
            self.logger.error(f"OCR处理失败: {str(e)}")
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

    def __del__(self):
        """清理资源"""
        try:
            paddle.device.cuda.empty_cache()
        except:
            pass

# 创建OCR服务实例
ocr_service = OCRService()

def ocr_handler(img_path, current_index):
    """OCR处理入口函数"""
    try:
        return ocr_service.handle_ocr(img_path)
    except Exception as e:
        logger.error(f"OCR handler failed: {str(e)}")
        return {'error': str(e)}