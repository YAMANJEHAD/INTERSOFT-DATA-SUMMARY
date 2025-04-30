import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="Note Analyzer", layout="wide")
st.title("📊 INTERSOFT Analyzer")

# مجلد الملفات والسجل
UPLOAD_DIR = "uploaded_files"
LOG_FILE = "logs.csv"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# اسم المستخدم
username = st.text_input("🧑‍💻 Enter your name:", key="username", placeholder="Type your name here...")

# رفع ملف جديد
uploaded_file = st.file_uploader("📤 Upload Excel File", type=["xlsx"])

# الحالات المعروفة
known_cases = [
    "TERMINAL ID - WRONG DATE", "NO IMAGE FOR THE DEVICE", "WRONG DATE", "TERMINAL ID", "NO J.O",
    "DONE", "NO RETAILERS SIGNATURE", "UNCLEAR IMAGE", "NO ENGINEER SIGNATURE",
    "NO SIGNATURE", "PENDING", "NO INFORMATIONS", "MISSING INFORMATION"
]

# تصنيف الملاحظات
def classify_note(note):
    note = str(note).strip().upper()
    for case in known_cases:
        if case in note:
            return case
    return "OTHER"

# عند رفع ملف
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

    df['note_type'] = df['note'].apply(classify_note)
    df = df[~df['note_type'].isin(['DONE', 'NO J.O'])]

    st.success("✅ File processed successfully!")

    # عرض النتائج
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

    # تجهيز للتحميل
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for note_type in df['note_type'].unique():
            subset = df[df['note_type'] == note_type]
            subset[['terminal_id', 'technician_name', 'note_type', 'ticket_type']].to_excel(writer, sheet_name=note_type[:31], index=False)
        note_counts.reset_index().rename(columns={'index': 'note_type', 'note_type': 'count'}).to_excel(writer, sheet_name="Note Type Count", index=False)
        tech_note_group.to_excel(writer, sheet_name="Technician Notes Count", index=False)

    # حفظ الملف فعلياً
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{username.strip().replace(' ', '_')}.xlsx"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(output.getvalue())

    # زر التحميل
    st.download_button("📥 Download Summary Excel", output.getvalue(), filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # تحديث سجل الملفات
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

# ---- 🔻 الشريط الجانبي (الهيستوري) ----
st.sidebar.subheader("📁 Upload History")

try:
    logs_df = pd.read_csv(LOG_FILE)
    if not logs_df.empty:
        file_names = logs_df["File"].tolist()
        selected_file = st.sidebar.selectbox("📂 Choose a file", file_names)

        if selected_file:
            file_info = logs_df[logs_df["File"] == selected_file].iloc[0]
            st.sidebar.markdown(f"👤 Uploaded by: **{file_info['Username']}**")
            st.sidebar.markdown(f"📅 Date: {file_info['Date']}")
            st.sidebar.markdown(f"📝 Notes: {file_info['Note Count']}")
            st.sidebar.markdown(f"🔢 Unique Types: {file_info['Unique Note Types']}")

            selected_path = os.path.join(UPLOAD_DIR, selected_file)
            with open(selected_path, "rb") as f:
                st.sidebar.download_button("⬇️ Download", f.read(), file_name=selected_file)

            # زر الحذف
            if st.sidebar.button("❌ Delete this file"):
                os.remove(selected_path)
                logs_df = logs_df[logs_df["File"] != selected_file]
                logs_df.to_csv(LOG_FILE, index=False)
                st.sidebar.success("File deleted successfully. Please reload the app.")
    else:
        st.sidebar.info("No uploaded files yet.")
except FileNotFoundError:
    st.sidebar.info("No upload history found.")
