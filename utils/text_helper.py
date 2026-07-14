import jieba

def clean_text(raw_text: str) -> str:
    """清洗合同文本，去除换行、空格、特殊符号"""
    text = raw_text.replace("\n", "").replace(" ", "").replace("\t", "")
    return text

def keyword_match(text: str, keyword_list: list) -> bool:
    """多关键词匹配，任一命中返回True"""
    for kw in keyword_list:
        if kw in text:
            return True
    return False

def multi_all_match(text: str, keyword_list: list) -> list:
    """返回缺失的关键词列表"""
    miss = []
    for kw in keyword_list:
        if kw not in text:
            miss.append(kw)
    return miss