import streamlit as st
import pandas as pd
import os

# إعدادات الصفحة
st.set_page_config(page_title="Note Analyzer", layout="wide")
st.title("📊 INTERSOFT Analyzer")

# تعريف المجلدات
LOG_FILE = "logs.csv"
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

            # إضافة السجل
            log_data = pd.DataFrame([{
                "Username": username,
                "File": filename,
                "Note Count": len(df),
                "Unique Note Types": df['Note_Type'].nunique()
            }])
            if os.path.exists(LOG_FILE):
                log_data.to_csv(LOG_FILE, mode='a', header=False, index=False)
            else:
                log_data.to_csv(LOG_FILE, index=False)

            # إعداد ملف Excel للتحميل
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for note_type in df['Note_Type'].unique():
                    subset = df[df['Note_Type'] == note_type]
                    subset[['TERMINAL_ID', 'TECHNICIAN_NAME', 'Note_Type', 'TICKET_TYPE']].to_excel(writer, sheet_name=note_type[:31], index=False)

            st.download_button("📥 Download Summary Excel", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ========== تاريخ الملفات ========== #
st.sidebar.header("📚 File History")

if os.path.exists(LOG_FILE):
    logs_df = pd.read_csv(LOG_FILE)
    logs_df = logs_df.sort_values(by="File", ascending=False)
    file_names = logs_df["File"].tolist()

    selected_file = st.sidebar.selectbox("Select a file to download or delete", file_names)

    if selected_file:
        file_info = logs_df[logs_df["File"] == selected_file].iloc[0]

        st.sidebar.markdown(f"**👤 Username:** {file_info['Username']}")
        st.sidebar.markdown(f"**📝 Notes:** {file_info['Note Count']}")
        st.sidebar.markdown(f"**🔢 Unique Types:** {file_info['Unique Note Types']}")

        file_path = os.path.join(DATA_DIR, selected_file)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.sidebar.download_button("⬇️ Download File", f, file_name=selected_file)

        # خيار الحذف
        if st.sidebar.button("❌ Delete this file"):
            os.remove(file_path)
            logs_df = logs_df[logs_df["File"] != selected_file]
            logs_df.to_csv(LOG_FILE, index=False)
            st.sidebar.success("File deleted successfully.")
            st.experimental_rerun()
else:
    st.sidebar.info("No file history yet.")
