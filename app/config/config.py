import os

class Config:
    # 环境配置
    ENVIRONMENT = 'development' if os.path.expanduser('~') == '/Users/grassgod' else 'production'
    
    # OCR模型配置
    OCR_CONFIG = {
        'development': {
            'det_dir': '../model/v_0.1/det_infer/',
            'rec_dir': '../model/v_0.1/rec_infer/',
            'cls_dir': '../model/v_0.1/cls_infer/',
            'rec_dict_path': '/Users/grassgod/Documents/Code/GrassgodOCR/app/model/v_0.1/keys_v1.txt',
            'font_path': 'app/model/simfang.ttf'
        },
        'production': {
            'det_dir': '../model/v_0.1/det_infer/',
            'rec_dir': '../model/v_0.1/rec_infer/',
            'cls_dir': '../model/v_0.1/cls_infer/',
            'rec_dict_path': '/dev/shm/GrassgodOCR/app/model/v_0.1/keys_v1.txt',
            'font_path': 'app/model/simfang.ttf'
        }
    }
    
    # OCR参数配置
    OCR_PARAMS = {
        'use_angle_cls': True,
        'lang': 'ch',
        'use_gpu': True,
        'det_db_box_thresh': 0.3,
        'show_log': False
    }
    
    # OpenAI配置
    OPENAI_CONFIG = {
        'api_key': 'sk-a71fede4066d43009c248b96e9e1f197',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    }
    
    # 图像处理配置
    IMAGE_PROCESSING = {
        'default_threshold': 200
    }
    
    @classmethod
    def get_ocr_config(cls):
        return cls.OCR_CONFIG[cls.ENVIRONMENT] 