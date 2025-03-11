import os
import sys
from flask import Flask, request, jsonify
from functools import wraps

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.service.ocr import ocr_handler
from app.service.call_taxi import call_taxi_handler
from app.utils.log_config import setup_logger

# 设置日志记录器
logger = setup_logger('flask_app')

# 创建flask应用
app = Flask(__name__)

def validate_request(req_data):
    """验证请求参数"""
    if not req_data:
        return False, "请求数据不能为空"
    
    if 'img_path' not in req_data:
        return False, "缺少必要参数：img_path"
        
    if not isinstance(req_data['img_path'], str):
        return False, "img_path必须是字符串"
        
    if not req_data['img_path'].startswith(('http://', 'https://')):
        return False, "img_path必须是有效的URL"
        
    return True, ""

@app.errorhandler(Exception)
def handle_error(error):
    """全局错误处理"""
    logger.error(f"Unexpected error: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': str(error)
    }), 500

@app.route('/process', methods=['POST'])
def process():
    """OCR处理接口"""
    try:
        logger.info("Received OCR process request")
        req_data = request.get_json()
        
        # 验证请求参数
        is_valid, error_msg = validate_request(req_data)
        if not is_valid:
            logger.error(f"Invalid request: {error_msg}")
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400

        img_path = req_data['img_path']
        logger.info(f"Processing image: {img_path}")
        
        result = ocr_handler(img_path, request._get_current_object())
        
        if 'error' in result:
            logger.error(f"OCR processing failed: {result['error']}")
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 500
            
        logger.info("OCR processing completed successfully")
        return jsonify({
            'status': 'success',
            'data': result
        })

    except Exception as e:
        logger.error(f"Error in process endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/call_didi', methods=['POST'])
def call_didi():
    """打车服务接口"""
    try:
        logger.info("Received call_didi request")
        req_data = request.get_json()
        
        # 验证请求参数
        is_valid, error_msg = validate_request(req_data)
        if not is_valid:
            logger.error(f"Invalid request: {error_msg}")
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400

        img_path = req_data['img_path']
        logger.info(f"Processing taxi request for image: {img_path}")
        
        result = call_taxi_handler(img_path, request._get_current_object())
        
        if result.get('status') != 'success':
            logger.error(f"Taxi service failed: {result}")
            logger.error(f"Taxi service failed: {result.get('status', 'Unknown error')}")
            logger.error(f"Taxi service img_path: {img_path}")
            return jsonify({
                'status': 'error',
                'message': result.get('status', 'Unknown error')
            }), 500
            
        logger.info("Taxi service completed successfully")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in call_didi endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    # 打开flask服务
    app.run(host='0.0.0.0', port=8113, debug=True)