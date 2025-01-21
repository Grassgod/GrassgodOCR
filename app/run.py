import os
import sys
from flask import Flask, request, jsonify
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.service.ocr import ocr_handler

# 创建flask应用
app = Flask(__name__)


@app.route('/process', methods=['POST'])
def process():
    print('request:', request)
    req_data = request.get_json()
    img_path = req_data['img_path']
    return jsonify(ocr_handler(img_path,request._get_current_object()))
   

if __name__ == '__main__':
    # 打开flask服务
    app.run(host='0.0.0.0', port=8090, debug=True)