import re

def extract_money(content):
    # 匹配数字部分（含错误格式）
    match = re.search(r'-?\d{1,3}(?:[,.]\d{3})*(?:[,.]\d{2})?', content)
    if not match:
        return None
    
    # 统一处理分隔符
    amount_str = match.group(0)
    
    # 移除所有逗号和中间的小数点
    cleaned = re.sub(r'[,.]', '', amount_str)

    # 还原最后一个小数点（如果有）
    if '.' == amount_str[-3] or ',' == amount_str[-3]:
        last_dot_index = amount_str.rfind(r'[,.]')

        cleaned = f"{cleaned[:last_dot_index-1]}.{cleaned[last_dot_index-1:]}"
    
    return float(cleaned) if '.' in cleaned else int(cleaned)

# 测试案例
print(extract_money("-口价3.066.84元"))  # 输出 3866.84
print(extract_money("3,068.02"))        # 输出 3068.02
print(extract_money("3.866.84"))        # 输出 3866.84
print(extract_money("3,866,84")) 
print(extract_money("3.866,84")) 
print(extract_money("866,84")) 
print(extract_money("866")) 