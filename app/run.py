import os
import sys
from flask import Flask, request, jsonify

# 创建flask应用
app = Flask(__name__)


@app.route('/process', methods=['GET'])
def process():
    return 'Hello World!'

if __name__ == '__main__':
    # 打开flask服务
    app.run(host='0.0.0.0', port=8090, debug=True)