import streamlit as st
import pandas as pd
import os
import io

# إعدادات الصفحة
st.set_page_config(page_title="Note Analyzer", layout="wide")
st.title("📊 INTERSOFT Analyzer")

# تعريف المجلدات
DATA_DIR = "uploaded_files"
os.makedirs(DATA_DIR, exist_ok=True)

# دالة لتصنيف الملاحظات
def classify_note(note):
    note = str(note).strip().upper()
    known_cases = {
        "TERMINAL ID - WRONG DATE",
        "NO IMAGE FOR THE DEVICE",
        "WRONG DATE",
        "TERMINAL ID",
        "NO J.O",
        "DONE",
        "NO RETAILERS SIGNATURE",
        "UNCLEAR IMAGE",
        "NO ENGINEER SIGNATURE",
        "NO SIGNATURE",
        "PENDING",
        "NO INFORMATIONS",
        "MISSING INFORMATION"
    }
    for case in known_cases:
        if case in note:
            return case
    return "MISSING INFORMATION"

# إدخال اسم المستخدم
st.markdown("### 👤 Enter your name")
username = st.text_input("Name", placeholder="Enter your name here")

# رفع الملف
uploaded_file = st.file_uploader("📁 Upload Excel File", type=["xlsx"])

# الأعمدة المطلوبة
required_cols = ['NOTE', 'TERMINAL_ID', 'TECHNICIAN_NAME', 'TICKET_TYPE']

if uploaded_file and username:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet2")
    except:
        df = pd.read_excel(uploaded_file)

    # تطبيع أسماء الأعمدة
    df.columns = [col.strip().upper() for col in df.columns]

    # محاولة لمطابقة الأعمدة المطلوبة
    col_mapping = {
        'NOTE': None,
        'TERMINAL_ID': None,
        'TECHNICIAN_NAME': None,
        'TICKET_TYPE': None
    }

    for req_col in required_cols:
        match_col = next((col for col in df.columns if req_col in col), None)
        if match_col:
            col_mapping[req_col] = match_col

    # إذا كانت بعض الأعمدة مفقودة
    if None in col_mapping.values():
        missing_cols = [col for col, value in col_mapping.items() if value is None]
        st.warning(f"Some required columns are missing or could not be matched: {missing_cols}")
    else:
        df.rename(columns=col_mapping, inplace=True)

        # إذا كانت الأعمدة المطلوبة موجودة
        if not all(col in df.columns for col in required_cols):
            st.warning(f"Some required columns are still missing. Found columns: {df.columns.tolist()}")
        else:
            # تصنيف الملاحظات
            df['Note_Type'] = df['NOTE'].apply(classify_note)
            df = df[~df['Note_Type'].isin(['DONE', 'NO J.O'])]

            st.success("✅ File processed successfully!")

            # عرض البيانات
            st.subheader("📋 Notes Data")
            st.dataframe(df[['TERMINAL_ID', 'TECHNICIAN_NAME', 'Note_Type', 'TICKET_TYPE']])

            # حفظ الملف
            filename = f"{username}_{uploaded_file.name}"
            save_path = os.path.join(DATA_DIR, filename)
            df.to_csv(save_path, index=False)

            # إعداد ملف Excel للتحميل
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for note_type in df['Note_Type'].unique():
                    subset = df[df['Note_Type'] == note_type]
                    subset[['TERMINAL_ID', 'TECHNICIAN_NAME', 'Note_Type', 'TICKET_TYPE']].to_excel(writer, sheet_name=note_type[:31], index=False)

            st.download_button("📥 Download Summary Excel", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
