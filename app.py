import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import os
from datetime import datetime
import streamlit.components.v1 as components
import json

# Set the page config
st.set_page_config(page_title="Note Analyzer", layout="wide")

# Define the history file location
history_file = "file_history.json"

# Function to load history
def load_history():
    if os.path.exists(history_file):
        with open(history_file, "r") as file:
            return json.load(file)
    else:
        return {}

# Function to save history
def save_history(history):
    with open(history_file, "w") as file:
        json.dump(history, file)

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

# If a file is uploaded, process it
if uploaded_file:
    # Get the user's name input
    user_name = st.text_input("Enter your name:", "")

    if user_name:
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

            # Save file analysis result to history
            history = load_history()
            file_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
            history[file_id] = {
                "filename": uploaded_file.name,
                "upload_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "user_name": user_name
            }
            save_history(history)

            # Downloadable summary Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for note_type in df['Note_Type'].unique():
                    subset = df[df['Note_Type'] == note_type]
                    subset[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']].to_excel(writer, sheet_name=note_type[:31], index=False)
                note_counts.reset_index().rename(columns={'index': 'Note_Type', 'Note_Type': 'Count'}).to_excel(writer, sheet_name="Note Type Count", index=False)
                tech_note_group.to_excel(writer, sheet_name="Technician Notes Count", index=False)
            st.download_button("📥 Download Summary Excel", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Show file history with option to download
st.subheader("📜 File History")
history = load_history()

# Display file history with download options
if history:
    history_df = pd.DataFrame.from_dict(history, orient="index")
    st.dataframe(history_df)

    selected_file = st.selectbox("Select a file to download:", history_df.index)

    if selected_file:
        st.write(f"Selected File: {history[selected_file]['filename']}")
        download_button = st.download_button(
            label="Download File",
            data=open(history[selected_file]['filename'], "rb").read(),
            file_name=history[selected_file]['filename'],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Delete file from history
        if st.button("Delete this file from history"):
            del history[selected_file]
            save_history(history)
            st.success("File deleted from history.")
else:
    st.write("No files in history.")
