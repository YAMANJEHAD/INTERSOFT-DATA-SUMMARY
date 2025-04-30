import os
import pandas as pd
import streamlit as st
from datetime import datetime

# إعداد المسارات
UPLOAD_FOLDER = "uploads"
LOG_FILE = "logs.csv"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# التأكد من وجود ملف السجل أو إصلاحه في حال كان تالف
def load_or_initialize_logs():
    try:
        logs_df = pd.read_csv(LOG_FILE)
        if not set(["Username", "File", "Note Count", "Unique Note Types"]).issubset(logs_df.columns):
            raise ValueError("Invalid log format")
    except Exception:
        logs_df = pd.DataFrame(columns=["Username", "File", "Note Count", "Unique Note Types"])
        logs_df.to_csv(LOG_FILE, index=False)
        st.sidebar.warning("🛠️ Log file was corrupted and has been reset.")
    return logs_df

# حفظ ملف جديد وتحليل محتواه
def handle_uploaded_file(uploaded_file, username):
    filepath = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    try:
        df = pd.read_csv(filepath)
        note_count = len(df)
        unique_types = df['Type'].nunique() if 'Type' in df.columns else 0
        logs_df = load_or_initialize_logs()
        new_log = pd.DataFrame([{
            "Username": username,
            "File": uploaded_file.name,
            "Note Count": note_count,
            "Unique Note Types": unique_types
        }])
        logs_df = pd.concat([logs_df, new_log], ignore_index=True)
        logs_df.to_csv(LOG_FILE, index=False)
        st.success("✅ File uploaded and analyzed successfully.")
    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")

# حذف سجل من السجل
def delete_log_entry(filename):
    logs_df = load_or_initialize_logs()
    logs_df = logs_df[logs_df["File"] != filename]
    logs_df.to_csv(LOG_FILE, index=False)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    st.success(f"🗑️ File '{filename}' has been deleted from logs and disk.")

# واجهة Streamlit
st.set_page_config(page_title="File Log Manager", layout="wide")
st.title("📂 File Upload & Log Viewer")

# تحميل السجلات
logs_df = load_or_initialize_logs()

# تحميل ملف جديد
st.sidebar.header("📤 Upload a File")
username = st.sidebar.text_input("Enter your username:")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file and username:
    handle_uploaded_file(uploaded_file, username)

# عرض السجلات
st.subheader("📝 Uploaded File Logs")

if logs_df.empty:
    st.info("No logs available.")
else:
    for i, row in logs_df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        col1.markdown(f"**👤 Username:** {row['Username']}")
        col2.markdown(f"**📄 File:** {row['File']}")
        col3.markdown(f"**🧮 Notes:** {row['Note Count']}")
        col4.markdown(f"**🔢 Unique Types:** {row['Unique Note Types']}")
        if col5.button("🗑️ Delete", key=f"delete_{i}"):
            delete_log_entry(row['File'])
            st.experimental_rerun()
