import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    # 创建日志目录
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建主logger
    logger = logging.getLogger('taxi_service')
    logger.setLevel(logging.DEBUG)

    # 正常日志文件处理器
    info_handler = RotatingFileHandler(
        'logs/info.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO)
    info_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    info_handler.setFormatter(info_formatter)

    # 错误日志文件处理器
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_formatter)

    # 添加处理器到logger
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

    return logger 