import streamlit as st
import os
from core.doc_parser import parse_contract
from core.audit_all import full_audit
from core.report_export import export_excel

st.set_page_config(page_title="合同智能审核工具", layout="wide")
st.title("合同智能审核系统（覆盖全部20项审查要点）")

upload_file = st.file_uploader("上传合同文件（支持docx / pdf）", type=["docx", "pdf"])

if upload_file is not None:
    # 临时保存文件
    temp_path = f"temp_{upload_file.name}"
    with open(temp_path, "wb") as f:
        f.write(upload_file.read())
    st.success("文件上传完成，正在解析并执行全维度审核...")

    try:
        text = parse_contract(temp_path)
        risk_data = full_audit(text)
        os.remove(temp_path)

        st.subheader("审核结果汇总")
        if len(risk_data) == 0:
            st.success("✅ 本合同未检测到风险，全部20项审查要点均符合规范")
        else:
            st.error(f"共检测到 {len(risk_data)} 项合同风险，请逐项整改")
            # 展示表格
            st.dataframe(risk_data, use_container_width=True)
            # 导出Excel
            save_file = export_excel(risk_data)
            with open(save_file, "rb") as f:
                st.download_button(
                    label="下载Excel审核报告",
                    data=f.read(),
                    file_name="合同审核报告.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"审核失败：{str(e)}")