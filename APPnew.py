import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from datetime import datetime

# Page config
st.set_page_config(page_title="Note Analyzer", layout="wide")

# Custom HTML & CSS: Enhanced design for clock
clock_html = """
<style>
body {
    background: #f4f7f9;
}
.clock-container {
    font-family: 'Courier New', monospace;
    font-size: 22px;
    color: #fff;
    background: linear-gradient(135deg, #1abc9c, #16a085);
    padding: 12px 25px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: pulse 2s infinite;
    position: fixed;
    top: 15px;
    right: 25px;
    z-index: 9999;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(26, 188, 156, 0.4); }
    70% { box-shadow: 0 0 0 15px rgba(26, 188, 156, 0); }
    100% { box-shadow: 0 0 0 0 rgba(26, 188, 156, 0); }
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

# Embed HTML
components.html(clock_html, height=100)

# Page title
st.title("📊 INTERSOFT Analyzer")

# File uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

required_cols = ['NOTE', 'Terminal_Id', 'Technician_Name', 'Ticket_Type']

# Updated classification function
def classify_note(note):
    note = str(note).strip().upper()
    if "TERMINAL ID - WRONG DATE" in note:
        return "TERMINAL ID - WRONG DATE"
    elif "NO IMAGE FOR THE DEVICE" in note:
        return "NO IMAGE FOR THE DEVICE"
    elif "IMAGE FOR THE DEVICE ONLY" in note:
        return "IMAGE FOR THE DEVICE ONLY"
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
    elif "NO BILL" in note:
        return "NO BILL"
    elif "NOT ACTIVE" in note:
        return "NOT ACTIVE"
    else:
        return "MISSING INFORMATION"

# Process file
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

        # Charts
        st.subheader("📈 Notes per Technician")
        tech_counts = df.groupby('Technician_Name')['Note_Type'].count().sort_values(ascending=False)
        st.bar_chart(tech_counts)

        st.subheader("📊 Notes by Type")
        note_counts = df['Note_Type'].value_counts()
        st.bar_chart(note_counts)

        st.subheader("📋 Data Table")
        st.dataframe(df[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']])

        st.subheader("📑 Notes per Technician by Type")
        tech_note_group = df.groupby(['Technician_Name', 'Note_Type']).size().reset_index(name='Count')
        st.dataframe(tech_note_group)

        # Excel export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for note_type in df['Note_Type'].unique():
                subset = df[df['Note_Type'] == note_type]
                subset[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']].to_excel(writer, sheet_name=note_type[:31], index=False)
            note_counts.reset_index().rename(columns={'index': 'Note_Type', 'Note_Type': 'Count'}).to_excel(writer, sheet_name="Note Type Count", index=False)
            tech_note_group.to_excel(writer, sheet_name="Technician Notes Count", index=False)
        st.download_button("📥 Download Summary Excel", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
