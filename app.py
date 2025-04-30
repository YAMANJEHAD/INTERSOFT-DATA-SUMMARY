import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Note Analyzer", layout="wide")
st.title("📊 INTERSOFT Analyzer")

# مجلد حفظ الملفات
UPLOAD_DIR = "uploaded_files"
LOG_FILE = "logs.csv"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# اسم المستخدم أعلى الصفحة
username = st.text_input("🧑‍💻 Enter your name:", key="username", placeholder="Type your name here...")

# رفع الملف
uploaded_file = st.file_uploader("📤 Upload Excel File", type=["xlsx"])

# الحالات المعروفة لتصنيف الملاحظات
known_cases = [
    "TERMINAL ID - WRONG DATE", "NO IMAGE FOR THE DEVICE", "WRONG DATE", "TERMINAL ID", "NO J.O",
    "DONE", "NO RETAILERS SIGNATURE", "UNCLEAR IMAGE", "NO ENGINEER SIGNATURE",
    "NO SIGNATURE", "PENDING", "NO INFORMATIONS", "MISSING INFORMATION"
]

# دالة التصنيف
def classify_note(note):
    note = str(note).strip().upper()
    for case in known_cases:
        if case in note:
            return case
    return "OTHER"

# معالجة الملف
if uploaded_file and username.strip():
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet2")
    except:
        df = pd.read_excel(uploaded_file)

    df.columns = [col.lower().strip() for col in df.columns]
    required_cols = ['note', 'terminal_id', 'technician_name', 'ticket_type']

    if not all(col in df.columns for col in required_cols):
        st.error(f"⚠️ Missing required columns. Expected: {required_cols}. Found: {list(df.columns)}")
        st.stop()

    # تصنيف الملاحظات
    df['note_type'] = df['note'].apply(classify_note)
    df = df[~df['note_type'].isin(['DONE', 'NO J.O'])]

    st.success("✅ File processed successfully!")

    # عرض الرسوم البيانية
    st.subheader("📈 Notes per Technician")
    tech_counts = df.groupby('technician_name')['note_type'].count().sort_values(ascending=False)
    st.bar_chart(tech_counts)

    st.subheader("📊 Notes by Type")
    note_counts = df['note_type'].value_counts()
    st.bar_chart(note_counts)

    st.subheader("📋 Data Table")
    st.dataframe(df[['terminal_id', 'technician_name', 'note_type', 'ticket_type']])

    st.subheader("📑 Notes per Technician by Type")
    tech_note_group = df.groupby(['technician_name', 'note_type']).size().reset_index(name='Count')
    st.dataframe(tech_note_group)

    # حفظ الملخص للتنزيل
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for note_type in df['note_type'].unique():
            subset = df[df['note_type'] == note_type]
            subset[['terminal_id', 'technician_name', 'note_type', 'ticket_type']].to_excel(writer, sheet_name=note_type[:31], index=False)
        note_counts.reset_index().rename(columns={'index': 'note_type', 'note_type': 'count'}).to_excel(writer, sheet_name="Note Type Count", index=False)
        tech_note_group.to_excel(writer, sheet_name="Technician Notes Count", index=False)

    # حفظ الملخص كملف فعلي
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{username.strip().replace(' ', '_')}.xlsx"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(output.getvalue())

    st.download_button("📥 Download Summary Excel", output.getvalue(), filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # سجل التحميل
    log_entry = {
        "Username": username.strip(),
        "File": filename,
        "Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Note Count": len(df),
        "Unique Note Types": df['note_type'].nunique()
    }

    try:
        log_df = pd.read_csv(LOG_FILE)
    except FileNotFoundError:
        log_df = pd.DataFrame(columns=log_entry.keys())

    log_df = pd.concat([log_df, pd.DataFrame([log_entry])], ignore_index=True)
    log_df.to_csv(LOG_FILE, index=False)

# عرض السجل الجانبي وتحميل الملفات القديمة
st.sidebar.subheader("📁 Upload History")
try:
    logs_df = pd.read_csv(LOG_FILE)
    st.sidebar.dataframe(logs_df)

    # اختيار ملف من الملفات السابقة
    file_list = logs_df["File"].unique().tolist()
    selected_file = st.sidebar.selectbox("📂 Download Previous File", file_list)
    if selected_file:
        selected_path = os.path.join(UPLOAD_DIR, selected_file)
        with open(selected_path, "rb") as f:
            st.sidebar.download_button("⬇️ Download Selected File", f.read(), file_name=selected_file)
except FileNotFoundError:
    st.sidebar.info("No uploads yet.")
