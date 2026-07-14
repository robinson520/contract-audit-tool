import yaml
from utils.text_helper import keyword_match, multi_all_match
from utils.regex_extract import extract_all_date, extract_money, check_backdate
import os

# 加载规则
def load_rules():
    rule_path = os.path.join("config", "rules.yaml")
    with open(rule_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

RULES = load_rules()

def full_audit(contract_text: str):
    risk_result = []

    # ====================== 1. 前置审批核查 ======================
    r1 = RULES["pre_audit"]
    has_audit = keyword_match(contract_text, r1["must_keywords"])
    if not has_audit:
        risk_result.append({
            "risk_level": r1["risk_level"],
            "module": "一、合同事项前置审批核查",
            "problem": "合同未提及立项/采购/投资前置审批材料，无审批文件不得通过审核",
            "suggest": "补齐对应前置审批附件，完成立项、采购、投资等前置流程后再发起合同审批"
        })

    # ====================== 2. 相对方资质核查 ======================
    r2 = RULES["party_info"]
    miss_legal = multi_all_match(contract_text, r2["legal_person_req"])
    if miss_legal:
        risk_result.append({
            "risk_level": r2["risk_level_miss"],
            "module": "二、合同相对方资质与基础信息核查",
            "problem": f"法人主体缺失基础信息：{','.join(miss_legal)}",
            "suggest": "完整填写乙方全称、注册地址、法定代表人；首次合作需提供加盖公章营业执照副本"
        })
    if keyword_match(contract_text, r2["industry_qual_keywords"]) is False:
        risk_result.append({
            "risk_level": r2["risk_level_base"],
            "module": "二、合同相对方资质与基础信息核查",
            "problem": "未约定对方承诺具备完整有效行业经营资质",
            "suggest": "增加条款约定相对方承诺持有对应业务法定从业许可、资质文件"
        })
    if keyword_match(contract_text, r2["related_keywords"]):
        risk_result.append({
            "risk_level": r2["risk_level_miss"],
            "module": "二、合同相对方资质与基础信息核查",
            "problem": "识别为关联方交易，未提及关联交易专项审批",
            "suggest": "业务部门提前在关联交易系统完成识别，单独履行关联交易审批流程"
        })
    if keyword_match(contract_text, ["代理人", "代理签约"]) and not keyword_match(contract_text, r2["agent_keywords"]):
        risk_result.append({
            "risk_level": r2["risk_level_miss"],
            "module": "二、合同相对方资质与基础信息核查",
            "problem": "代理人签约，但未核验代理授权文件、未约定代理权限承诺",
            "suggest": "收取完整授权委托书，合同增加代理人合法签约权限承诺条款"
        })

    # ====================== 3. 合同标的审核 ======================
    r3 = RULES["subject"]
    miss_subject = multi_all_match(contract_text, r3["must_keywords"])
    if miss_subject:
        risk_result.append({
            "risk_level": r3["risk_level"],
            "module": "三、合同标的条款审核",
            "problem": f"标的及验收关键信息缺失：{','.join(miss_subject)}",
            "suggest": "补充标的物名称、规格、数量，完整约定验收标准、时间、主体、方式"
        })

    # ====================== 4. 期限&倒签核查 ======================
    r4 = RULES["term_check"]
    all_dates = extract_all_date(contract_text)
    sign_key = ["签订日期", "本合同签订于"]
    perform_key = ["履行期限", "服务起始", "供货起始"]
    sign_dates = []
    perform_dates = []
    if keyword_match(contract_text, sign_key):
        sign_dates = all_dates
    if keyword_match(contract_text, perform_key):
        perform_dates = all_dates
    if check_backdate(sign_dates, perform_dates):
        risk_result.append({
            "risk_level": r4["risk_backdate"],
            "module": "四、合同生效及履行期限审核",
            "problem": "存在合同倒签，履行起始时间早于合同签订日期",
            "suggest": "退回主办部门调整履行期限或签订日期，禁止倒签合同"
        })
    if keyword_match(contract_text, ["自动续期", "到期自动顺延"]) and not keyword_match(contract_text, ["任意解除权", "限价约束"]):
        risk_result.append({
            "risk_level": r4["risk_auto_renew"],
            "module": "四、合同生效及履行期限审核",
            "problem": "设置自动续期，但未约定我方任意解除权、限价保护性条款",
            "suggest": "删除自动续期；确需保留需补充我方任意解除、价格上限约束条款并专项说明理由"
        })

    # ====================== 5. 价款支付条款 ======================
    r5 = RULES["price_pay"]
    nums, caps = extract_money(contract_text)
    if len(nums) == 0 or len(caps) == 0:
        risk_result.append({
            "risk_level": r5["risk_level"],
            "module": "五、合同价款与支付条款审核",
            "problem": "合同未同时标注大小写金额",
            "suggest": "补充大写人民币金额，大小写保持一致"
        })
    if not keyword_match(contract_text, ["含税", "不含税"]):
        risk_result.append({
            "risk_level": r5["risk_level"],
            "module": "五、合同价款与支付条款审核",
            "problem": "未明确价款是否含税",
            "suggest": "明确标注本合同价款为含税/不含税价格"
        })
    if keyword_match(contract_text, ["预付款"]) and not keyword_match(contract_text, ["压缩预付款比例"]):
        risk_result.append({
            "risk_level": r5["risk_level"],
            "module": "五、合同价款与支付条款审核",
            "problem": "约定预付款，未大幅压缩预付款比例",
            "suggest": "原则取消预付款；确需支付降低预付款比例，绑定阶段性交付成果"
        })
    if not keyword_match(contract_text, ["先开具发票后付款", "先票后款"]):
        risk_result.append({
            "risk_level": r5["risk_level"],
            "module": "五、合同价款与支付条款审核",
            "problem": "未采用先开票后付款模式",
            "suggest": "统一约定对方开具合规发票后我方再支付对应款项，分批次付款需分批开票"
        })

    # ====================== 6. 保密条款 ======================
    r6 = RULES["secret_clause"]
    if not keyword_match(contract_text, r6["standard_text"]):
        risk_result.append({
            "risk_level": r6["risk_level"],
            "module": "六、保密条款审核",
            "problem": "合同未嵌入公司标准保密示范条款",
            "suggest": "按业务场景选用对应保密协议；中介合同强制加载保密条款，必要时补充个人保密承诺书"
        })

    # ====================== 7. 数据保护条款 ======================
    r7 = RULES["data_clause"]
    if keyword_match(contract_text, r7["scene"]) and not keyword_match(contract_text, r7["standard_text"]):
        risk_result.append({
            "risk_level": r7["risk_level"],
            "module": "七、数据保护条款审核",
            "problem": "涉及数据委托/对外处理，但未配套标准数据保护条款与数据处理协议",
            "suggest": "匹配对应数据保护示范文本，要求相对方单独签署配套数据处理协议"
        })

    # ====================== 8. 反商业贿赂（强制） ======================
    r8 = RULES["anti_bribery"]
    if not keyword_match(contract_text, r8["standard_keywords"]):
        risk_result.append({
            "risk_level": r8["risk_level"],
            "module": "八、反腐败与反商业贿赂条款审核",
            "problem": "缺失必备双反标准示范条款",
            "suggest": "全系统合同必须加载双反条款；无法使用标准文本需在签报完整列明原因随审批提交"
        })

    # ====================== 9. 权利义务 ======================
    r9 = RULES["right_duty"]
    miss_right = multi_all_match(contract_text, r9["keyword"])
    if miss_right:
        risk_result.append({
            "risk_level": r9["risk_level"],
            "module": "九、双方权利义务条款审核",
            "problem": f"缺失合同变更、解除规范约定：{','.join(miss_right)}",
            "suggest": "清晰划分双方权责，约定变更、解除需书面通知、双方协商一致，禁止单方随意变更解除"
        })

    # ====================== 10. 分包转包限制 ======================
    r10 = RULES["subcontract"]
    if keyword_match(contract_text, ["外包", "信息科技外包"]) and keyword_match(contract_text, ["转包"]) and not keyword_match(contract_text, ["不得转包", "禁止转包"]):
        risk_result.append({
            "risk_level": r10["risk_level"],
            "module": "十、分包与转包限制条款审核",
            "problem": "信息科技外包未禁止整体、变相转包",
            "suggest": "增加禁止转包条款；如需分包补充三项约束：核心业务不得分包、总包全责、分包变更报批"
        })

    # ====================== 11. 履约担保 ======================
    r11 = RULES["performance_guarantee"]
    if keyword_match(contract_text, r11["trigger_scene"]) and not keyword_match(contract_text, ["履约担保", "担保形式"]):
        risk_result.append({
            "risk_level": r11["risk_level"],
            "module": "十一、履约担保条款审核",
            "problem": "合同金额大/对方履约弱/高风险项目，未设置履约担保专项条款",
            "suggest": "补充担保条款，明确担保形式、范围、有效期、担保触发机制"
        })

    # ====================== 12. 质保金 ======================
    r12 = RULES["quality_deposit"]
    if not keyword_match(contract_text, r12["keywords"]):
        risk_result.append({
            "risk_level": r12["risk_level"],
            "module": "十二、质保金条款审核",
            "problem": "未约定质保期、质保金相关规则",
            "suggest": "设置质保金，绑定质保期返还规则，明确质保起算时点、服务覆盖范围"
        })

    # ====================== 13. 知识产权 ======================
    r13 = RULES["ip_right"]
    if keyword_match(contract_text, ["定制开发", "软件开发"]) and not keyword_match(contract_text, ["知识产权归我方", "源代码"]):
        risk_result.append({
            "risk_level": r13["risk_level"],
            "module": "十三、知识产权条款审核",
            "problem": "定制开发软件未约定知识产权归属、源码交付、第三方授权约束",
            "suggest": "约定定制成果全部知识产权归我方，交付完整源码技术文档，开发方自行解决第三方知识产权授权"
        })
    if not keyword_match(contract_text, ["我方无限制使用", "对方不得擅自转让成果"]):
        risk_result.append({
            "risk_level": r13["risk_level"],
            "module": "十三、知识产权条款审核",
            "problem": "未约定我方需求产出成果使用权、对方转让披露限制",
            "suggest": "补充约定我方可无限制使用、对外披露成果，未经我方许可合作方不得转让许可成果"
        })

    # ====================== 14. 违约责任 ======================
    r14 = RULES["breach"]
    breach_key = ["违约金", "赔偿损失", "返还全部款项", "扣款抵扣", "重做退货"]
    miss_breach = multi_all_match(contract_text, breach_key)
    if miss_breach:
        risk_result.append({
            "risk_level": r14["risk_level"],
            "module": "十四、违约责任条款审核",
            "problem": f"违约责任类型缺失：{','.join(miss_breach)}",
            "suggest": "匹配每项义务设置违约金、损失补足、款项返还、抵扣、重做更换等补救责任"
        })

    # ====================== 15. 责任限额 ======================
    r15 = RULES["limit_liability"]
    if keyword_match(contract_text, ["责任限额", "赔偿上限"]) and not keyword_match(contract_text, ["故意重大过失不适用限额", "知识产权侵权不限额"]):
        risk_result.append({
            "risk_level": r15["risk_level"],
            "module": "十五、责任限额条款审核",
            "problem": "设置责任限额，但未约定五类除外情形",
            "suggest": "补充：故意/重大过失、知识产权侵权、保密违约、人身伤亡、法定责任不受限额约束；限额仅适用于普通违约损失"
        })

    # ====================== 16. 通知送达 ======================
    r16 = RULES["notice"]
    miss_notice = multi_all_match(contract_text, r16["must"])
    if miss_notice:
        risk_result.append({
            "risk_level": r16["risk_level"],
            "module": "十六、通知送达条款审核",
            "problem": f"送达规则缺失：{','.join(miss_notice)}",
            "suggest": "统一约定送达地址、联系人、快递送达有效，地址变更需书面告知"
        })

    # ====================== 17. 争议解决 ======================
    r17 = RULES["dispute"]
    if keyword_match(contract_text, ["仲裁", "诉讼"]) and keyword_match(contract_text, ["同时选择仲裁和诉讼"]):
        risk_result.append({
            "risk_level": r17["risk_level"],
            "module": "十七、适用法律与争议解决条款审核",
            "problem": "同时约定仲裁+诉讼两种争议解决方式，条款无效",
            "suggest": "二选一，仅保留仲裁或诉讼；诉讼优先约定我方所在地管辖法院，不突破专属管辖"
        })
    if not keyword_match(contract_text, ["适用中华人民共和国法律"]):
        risk_result.append({
            "risk_level": r17["risk_level"],
            "module": "十七、适用法律与争议解决条款审核",
            "problem": "国内合同未约定适用中华人民共和国法律",
            "suggest": "国内合同统一约定适用中国法律；涉外合同优先仲裁、适用中国法律"
        })

    # ====================== 18. 合同附件 ======================
    r18 = RULES["attachment"]
    if keyword_match(contract_text, ["附件"]) and not keyword_match(contract_text, ["附件与正文具有同等效力", "文件解释优先级"]):
        risk_result.append({
            "risk_level": r18["risk_level"],
            "module": "十八、合同附件审核",
            "problem": "存在附件但未约定附件效力、整套文件解释顺序",
            "suggest": "明确附件完整性，约定后签署文件解释效力优先于前置文件"
        })

    # ====================== 19. 补充协议 ======================
    r19 = RULES["supplement"]
    if keyword_match(contract_text, ["补充协议"]) and not keyword_match(contract_text, ["原合同保持一致", "不冲突原合同"]):
        risk_result.append({
            "risk_level": r19["risk_level"],
            "module": "十九、补充协议（续签、变更）审核",
            "problem": "补充协议未约定与原合同衔接一致，存在冲突风险",
            "suggest": "审核时附完整原合同文本，补充条款不得与原合同矛盾冲突"
        })

    # ====================== 20. 签章规范 ======================
    r20 = RULES["seal"]
    if keyword_match(contract_text, ["授权代表签署"]) and not keyword_match(contract_text, ["授权委托书", "授权有效期"]):
        risk_result.append({
            "risk_level": r20["risk_level"],
            "module": "二十、合同签章规范审核",
            "problem": "授权代表签约，但未核验授权委托书、授权期限",
            "suggest": "核验授权范围包含签约权限，有效期覆盖签约当日；落款需公章+法定代表人签字"
        })
    if not keyword_match(contract_text, ["签订地为我方所在地", "本合同签订于XX公司"]):
        risk_result.append({
            "risk_level": r20["risk_level"],
            "module": "二十、合同签章规范审核",
            "problem": "未统一约定合同签订地为我方公司所在地",
            "suggest": "合同落款增加条款：本合同签订地为我方公司住所地"
        })

    return risk_result