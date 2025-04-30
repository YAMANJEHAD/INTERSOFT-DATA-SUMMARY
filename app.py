import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime
from dateutil import parser  # جديد

st.set_page_config(page_title="Note Analyzer", layout="wide")
st.title("📊 INTERSOFT Analyzer")

LOG_FILE = "logs.csv"
DATA_DIR = "uploaded_files"
os.makedirs(DATA_DIR, exist_ok=True)

# ===== تصنيف الملاحظات =====
def classify_note(note):
    note = str(note).strip().upper()
    known_cases = {
        "TERMINAL ID - WRONG DATE", "NO IMAGE FOR THE DEVICE", "WRONG DATE", "TERMINAL ID",
        "NO J.O", "DONE", "NO RETAILERS SIGNATURE", "UNCLEAR IMAGE",
        "NO ENGINEER SIGNATURE", "NO SIGNATURE", "PENDING", "NO INFORMATIONS", "MISSING INFORMATION"
    }
    for case in known_cases:
        if case in note:
            return case
    return "MISSING INFORMATION"

# ===== حساب الوقت منذ الرفع =====
def time_since(date_str):
    try:
        upload_time = parser.parse(str(date_str))  # تعديل هنا
        delta = datetime.now() - upload_time
        seconds = delta.total_seconds()
        if seconds < 60:
            return f"{int(seconds)} ثانية"
        elif seconds < 3600:
            return f"{int(seconds // 60)} دقيقة"
        elif seconds < 86400:
            return f"{int(seconds // 3600)} ساعة"
        else:
            return f"{int(seconds // 86400)} يوم"
    except Exception:
        return "تاريخ غير صالح"

# ===== اسم المستخدم =====
st.markdown("### 👤 أدخل اسمك")
username = st.text_input("الاسم", placeholder="اكتب اسمك هنا")

uploaded_file = st.file_uploader("📁 رفع ملف Excel", type=["xlsx"])

required_cols = ['NOTE', 'TERMINAL_ID', 'TECHNICIAN_NAME', 'TICKET_TYPE']

if uploaded_file and username:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet2")
    except:
        df = pd.read_excel(uploaded_file)

    df.columns = [col.strip().upper() for col in df.columns]

    col_mapping = {col: None for col in required_cols}
    for req_col in required_cols:
        match_col = next((col for col in df.columns if req_col in col), None)
        if match_col:
            col_mapping[req_col] = match_col

    if None in col_mapping.values():
        missing_cols = [col for col, val in col_mapping.items() if val is None]
        st.warning(f"بعض الأعمدة مفقودة: {missing_cols}")
    else:
        df.rename(columns=col_mapping, inplace=True)

        df['Note_Type'] = df['NOTE'].apply(classify_note)
        df = df[~df['Note_Type'].isin(['DONE', 'NO J.O'])]

        st.success("✅ تم تحليل الملف بنجاح!")

        st.subheader("📈 عدد الملاحظات لكل فني")
        tech_counts = df.groupby('TECHNICIAN_NAME')['Note_Type'].count().sort_values(ascending=False)
        st.bar_chart(tech_counts)

        st.subheader("📊 عدد الملاحظات حسب النوع")
        note_counts = df['Note_Type'].value_counts()
        st.bar_chart(note_counts)

        st.subheader("📋 البيانات")
        st.dataframe(df[['TERMINAL_ID', 'TECHNICIAN_NAME', 'Note_Type', 'TICKET_TYPE']])

        st.subheader("📑 توزيع الملاحظات لكل فني حسب النوع")
        tech_note_group = df.groupby(['TECHNICIAN_NAME', 'Note_Type']).size().reset_index(name='Count')
        st.dataframe(tech_note_group)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{username}_{uploaded_file.name}"
        save_path = os.path.join(DATA_DIR, filename)
        df.to_csv(save_path, index=False)

        log_data = pd.DataFrame([{
            "Username": username,
            "File": filename,
            "Date": timestamp,
            "Note Count": len(df),
            "Unique Note Types": df['Note_Type'].nunique()
        }])
        if os.path.exists(LOG_FILE):
            log_data.to_csv(LOG_FILE, mode='a', header=False, index=False)
        else:
            log_data.to_csv(LOG_FILE, index=False)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for note_type in df['Note_Type'].unique():
                subset = df[df['Note_Type'] == note_type]
                subset[['TERMINAL_ID', 'TECHNICIAN_NAME', 'Note_Type', 'TICKET_TYPE']].to_excel(writer, sheet_name=note_type[:31], index=False)
            note_counts.reset_index().rename(columns={'index': 'Note_Type', 'Note_Type': 'Count'}).to_excel(writer, sheet_name="Note Type Count", index=False)
            tech_note_group.to_excel(writer, sheet_name="Technician Notes Count", index=False)

        st.download_button("📥 تحميل ملف التقرير", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ========== 📚 سجل الملفات ========== #
st.sidebar.header("📂 سجل الملفات")

if os.path.exists(LOG_FILE):
    logs_df = pd.read_csv(LOG_FILE)
    logs_df = logs_df.sort_values(by="Date", ascending=False)
    file_names = logs_df["File"].tolist()

    selected_file = st.sidebar.selectbox("اختر ملف:", file_names)

    if selected_file:
        file_info = logs_df[logs_df["File"] == selected_file].iloc[0]
        time_passed = time_since(file_info['Date'])

        st.sidebar.markdown(f"**👤 المستخدم:** {file_info['Username']}")
        st.sidebar.markdown(f"**📅 وقت الرفع:** {file_info['Date']}")
        st.sidebar.markdown(f"**⏱️ منذ:** {time_passed}")
        st.sidebar.markdown(f"**📝 عدد الملاحظات:** {file_info['Note Count']}")
        st.sidebar.markdown(f"**🔢 أنواع فريدة:** {file_info['Unique Note Types']}")

        file_path = os.path.join(DATA_DIR, selected_file)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.sidebar.download_button("⬇️ تحميل الملف", f, file_name=selected_file)

            if st.sidebar.button("❌ حذف الملف"):
                os.remove(file_path)
                logs_df = logs_df[logs_df["File"] != selected_file]
                logs_df.to_csv(LOG_FILE, index=False)
                st.sidebar.success("✅ تم حذف الملف.")
                st.experimental_rerun()
else:
    st.sidebar.info("لا يوجد سجل بعد.")
