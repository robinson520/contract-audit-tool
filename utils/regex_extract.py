import re
from datetime import datetime

# 提取日期
DATE_PATTERN = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
# 阿拉伯金额
NUM_MONEY_PATTERN = re.compile(r"¥?(\d{1,3}(,\d{3})*(\.\d{1,2})?)")
# 大写金额
CAP_MONEY_PATTERN = re.compile(r"[零壹贰叁肆伍陆柒捌玖拾佰仟万亿]+元")

def extract_all_date(text: str) -> list:
    res = DATE_PATTERN.findall(text)
    date_list = []
    for y, m, d in res:
        try:
            dt = datetime(int(y), int(m), int(d))
            date_list.append(dt)
        except:
            continue
    return date_list

def extract_money(text: str):
    num_list = NUM_MONEY_PATTERN.findall(text)
    cap_list = CAP_MONEY_PATTERN.findall(text)
    num_clean = [i[0] for i in num_list]
    return num_clean, cap_list

def check_backdate(sign_date_list: list, perform_start_list: list) -> bool:
    """判断是否倒签：履行起始日早于签订日期"""
    if not sign_date_list or not perform_start_list:
        return False
    earliest_perform = min(perform_start_list)
    latest_sign = max(sign_date_list)
    return earliest_perform < latest_sign