import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from datetime import datetime
import os
import json
import uuid

# Set the page config
st.set_page_config(page_title="Note Analyzer", layout="wide")

# Add custom animation styles and clock to the page
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

/* Centering uploader info and reducing font size */
.upload-info {
    text-align: center;
    font-size: 12px;
    margin-top: 20px;
}

/* Adjusting table history style */
.history-table {
    margin-top: 40px;
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

# Embed the clock animation and page effect
components.html(clock_html, height=100)

# Page title and other content
st.title("📊 INTERSOFT Analyzer ")

# File uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

required_cols = ['NOTE', 'Terminal_Id', 'Technician_Name', 'Ticket_Type']

# Function to classify the note
def classify_note(note):
    note = str(note).strip().upper()
    if "TERMINAL ID - WRONG DATE" in note:
        return "TERMINAL ID - WRONG DATE"
    elif "NO IMAGE FOR THE DEVICE" in note:
        return "NO IMAGE FOR THE DEVICE"
    elif "WRONG DATE" in note:
        return "WRONG DATE"
    elif "TERMINAL ID" in note:
        return "TERMINAL ID"
    elif "NO J.O" in note:
        return "NO J.O"
    elif "DONE" in note:
        return "DONE"
    elif "NO RETAILERS SIGNATURE" in note:
        return "NO RETAILERS SIGNATURE"
    elif "UNCLEAR IMAGE" in note:
        return "UNCLEAR IMAGE"
    elif "NO ENGINEER SIGNATURE" in note:
        return "NO ENGINEER SIGNATURE"
    elif "NO SIGNATURE" in note:
        return "NO SIGNATURE"
    elif "PENDING" in note:
        return "PENDING"
    elif "NO INFORMATIONS" in note:
        return "NO INFORMATIONS"
    elif "MISSING INFORMATION" in note:
        return "MISSING INFORMATION"
    else:
        return "MISSING INFORMATION"

# Load upload history from a JSON file
HISTORY_FILE = "upload_history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        upload_history = json.load(f)
else:
    upload_history = []

st.markdown("---")
st.header("📂 File Upload History")

# Input uploader name and date before uploading
with st.form("upload_form"):
    uploader_name = st.text_input("Enter your name", "")
    upload_date = st.date_input("Select upload date", datetime.today())
    submitted = st.form_submit_button("Submit Info")

if submitted and not uploader_name:
    st.warning("Please enter your name before uploading a file.")
    st.stop()

# Save upload log after successful file upload
if uploaded_file and uploader_name:
    file_id = str(uuid.uuid4())  # unique identifier for the file
    filename = uploaded_file.name
    log_entry = {
        "id": file_id,
        "filename": filename,
        "uploader": uploader_name,
        "date": str(upload_date)
    }
    if not any(item["filename"] == filename for item in upload_history):
        upload_history.append(log_entry)
        with open(HISTORY_FILE, "w") as f:
            json.dump(upload_history, f)

# If a file is uploaded, process it
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet2")
    except:
        df = pd.read_excel(uploaded_file)

    if not all(col in df.columns for col in required_cols):
        st.error(f"Missing required columns. Available: {list(df.columns)}")
    else:
        df['Note_Type'] = df['NOTE'].apply(classify_note)
        df = df[~df['Note_Type'].isin(['DONE', 'NO J.O'])]

        st.success("✅ File processed successfully!")

        # Show charts
        st.subheader("📈 Notes per Technician")
        tech_counts = df.groupby('Technician_Name')['Note_Type'].count().sort_values(ascending=False)
        st.bar_chart(tech_counts)

        st.subheader("📊 Notes by Type")
        note_counts = df['Note_Type'].value_counts()
        st.bar_chart(note_counts)

        st.subheader("📋 Data Table")
        st.dataframe(df[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']])

        # Group by technician and note type
        st.subheader("📑 Notes per Technician by Type")
        tech_note_group = df.groupby(['Technician_Name', 'Note_Type']).size().reset_index(name='Count')
        st.dataframe(tech_note_group)

        # Downloadable summary Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for note_type in df['Note_Type'].unique():
                subset = df[df['Note_Type'] == note_type]
                subset[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']].to_excel(writer, sheet_name=note_type[:31], index=False)
            note_counts.reset_index().rename(columns={'index': 'Note_Type', 'Note_Type': 'Count'}).to_excel(writer, sheet_name="Note Type Count", index=False)
            tech_note_group.to_excel(writer, sheet_name="Technician Notes Count", index=False)
        st.download_button("📥 Download Summary Excel", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Show history table
if upload_history:
    st.subheader("📝 Uploaded Files")
    df_history = pd.DataFrame(upload_history)
    selected_row = st.radio("Select a file", df_history["filename"])

    st.dataframe(df_history, use_container_width=True, height=400)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🧾 Preview File"):
            try:
                df_selected = pd.read_excel(selected_row)
                st.dataframe(df_selected.head())
            except Exception as e:
                st.error(f"Could not open file: {e}")

    with col2:
        if st.button("❌ Delete File"):
            upload_history = [entry for entry in upload_history if entry["filename"] != selected_row]
            try:
                os.remove(selected_row)
            except FileNotFoundError:
                pass
            with open(HISTORY_FILE, "w") as f:
                json.dump(upload_history, f)
            st.success(f"File '{selected_row}' deleted successfully.")
            st.experimental_rerun()

# Display uploader info centered and small font
if uploader_name:
    st.markdown(f"""
    <div class="upload-info">
        <p><strong>Uploader: </strong>{uploader_name}</p>
        <p><strong>Date: </strong>{upload_date}</p>
    </div>
    """, unsafe_allow_html=True)
