import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime
import streamlit.components.v1 as components

# Set page configuration
st.set_page_config(page_title="Note Analyzer", layout="wide")
st.title("📊 INTERSOFT Analyzer")

# Define directories
LOG_FILE = "logs.csv"
DATA_DIR = "uploaded_files"
os.makedirs(DATA_DIR, exist_ok=True)

# Function to classify notes (case-insensitive)
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

# Time-ago formatter
def time_since(date_str):
    upload_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    delta = datetime.now() - upload_time
    seconds = delta.total_seconds()
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"

# Custom clock and animation
clock_html = """
<style>
/* Animation for the clock */
.clock-container {
    font-family: 'Courier New', monospace;
    font-size: 24px;
    color: #ffffff;
    background: linear-gradient(90deg, #f39c12, #e67e22);
    padding: 10px 20px;
    border-radius: 12px;
    width: fit-content;
    animation: pulse 2s infinite;
    margin-bottom: 20px;
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 9999;
}

/* Keyframe for pulse animation */
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(243, 156, 18, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(243, 156, 18, 0); }
    100% { box-shadow: 0 0 0 0 rgba(243, 156, 18, 0); }
}

/* Page animation */
@keyframes slideIn {
    0% { transform: translateX(100%); opacity: 0; }
    100% { transform: translateX(0); opacity: 1; }
}

/* Apply sliding effect to the page */
.page-container {
    animation: slideIn 1s ease-out;
    overflow: hidden;
}
</style>
<div class="clock-container">
    <span id="clock"></span>
</div>
<script>
function updateClock() {
    const now = new Date();
    document.getElementById('clock').innerText = now.toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();
</script>
"""

# Embed the clock animation
components.html(clock_html, height=100)

# Input username at the top
st.markdown("### 👤 Enter your name")
username = st.text_input("Name", placeholder="Enter your name here")

uploaded_file = st.file_uploader("📁 Upload Excel File", type=["xlsx"])
required_cols = ['NOTE', 'Terminal_Id', 'Technician_Name', 'Ticket_Type']

if uploaded_file and username:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet2")
    except:
        df = pd.read_excel(uploaded_file)

    # Normalize column names
    df.columns = [col.strip().upper() for col in df.columns]
    col_map = {col: col.title().replace("_", "") for col in required_cols}
    if not all(col in df.columns for col in required_cols):
        st.warning(f"Some required columns are missing. Found columns: {df.columns.tolist()}")
    else:
        df['Note_Type'] = df['NOTE'].apply(classify_note)
        df = df[~df['Note_Type'].isin(['DONE', 'NO J.O'])]

        st.success("✅ File processed successfully!")

        # Display visualizations
        st.subheader("📈 Notes per Technician")
        tech_counts = df.groupby('Technician_Name')['Note_Type'].count().sort_values(ascending=False)
        st.bar_chart(tech_counts)

        st.subheader("📊 Notes by Type")
        note_counts = df['Note_Type'].value_counts()
        st.bar_chart(note_counts)

        st.subheader("📋 Notes Data")
        st.dataframe(df[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']])

        st.subheader("📑 Notes per Technician by Type")
        tech_note_group = df.groupby(['Technician_Name', 'Note_Type']).size().reset_index(name='Count')
        st.dataframe(tech_note_group)

        # Save processed file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{username}_{uploaded_file.name}"
        save_path = os.path.join(DATA_DIR, filename)
        df.to_csv(save_path, index=False)

        # Save log
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

        # Prepare summary Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for note_type in df['Note_Type'].unique():
                subset = df[df['Note_Type'] == note_type]
                subset[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']].to_excel(writer, sheet_name=note_type[:31], index=False)
            note_counts.reset_index().rename(columns={'index': 'Note_Type', 'Note_Type': 'Count'}).to_excel(writer, sheet_name="Note Type Count", index=False)
            tech_note_group.to_excel(writer, sheet_name="Technician Notes Count", index=False)

        st.download_button("📥 Download Summary Excel", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ========== FILE HISTORY ========== #
st.sidebar.header("📚 File History")

if os.path.exists(LOG_FILE):
    logs_df = pd.read_csv(LOG_FILE)
    logs_df = logs_df.sort_values(by="Date", ascending=False)
    file_names = logs_df["File"].tolist()

    selected_file = st.sidebar.selectbox("Select a file to download or delete", file_names)

    if selected_file:
        file_info = logs_df[logs_df["File"] == selected_file].iloc[0]
        time_passed = time_since(file_info['Date'])

        st.sidebar.markdown(f"**👤 Username:** {file_info['Username']}")
        st.sidebar.markdown(f"**📅 Upload Time:** {file_info['Date']}")
        st.sidebar.markdown(f"**⏱️ Time Ago:** {time_passed}")
        st.sidebar.markdown(f"**📝 Notes:** {file_info['Note Count']}")
        st.sidebar.markdown(f"**🔢 Unique Types:** {file_info['Unique Note Types']}")

        file_path = os.path.join(DATA_DIR, selected_file)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.sidebar.download_button("⬇️ Download File", f, file_name=selected_file)

        if st.sidebar.button("❌ Delete this file"):
            os.remove(file_path)
            logs_df = logs_df[logs_df["File"] != selected_file]
            logs_df.to_csv(LOG_FILE, index=False)
            st.sidebar.success("File deleted successfully.")
            st.experimental_rerun()
else:
    st.sidebar.info("No file history yet.")
