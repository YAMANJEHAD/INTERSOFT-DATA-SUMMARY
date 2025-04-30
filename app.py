import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Note Analyzer", layout="wide")
st.title("📊 INTERSOFT Analyzer ")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

required_cols = ['NOTE', 'Terminal_Id', 'Technician_Name', 'Ticket_Type']

known_cases = [
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
]

def classify_note(note):
    try:
        note = str(note).strip().upper()
    except:
        return "UNKNOWN CASE"
    
    for case in known_cases:
        if case in note:
            return case
    return "UNKNOWN CASE"

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet2")
    except:
        df = pd.read_excel(uploaded_file)

    if not all(col in df.columns for col in required_cols):
        st.error(f"Missing required columns. Available: {list(df.columns)}")
    else:
        df['Note_Type'] = df['NOTE'].apply(classify_note)
        
        # Filter out DONE and NO J.O only
        df_filtered = df[~df['Note_Type'].isin(['DONE', 'NO J.O'])]

        st.success("✅ File processed successfully!")

        # 📊 Bar Chart: Notes per Technician
        st.subheader("📈 Notes per Technician")
        tech_counts = df_filtered.groupby('Technician_Name')['Note_Type'].count().sort_values(ascending=False)
        st.bar_chart(tech_counts)

        # 📊 Bar Chart: Notes by Type
        st.subheader("📊 Notes by Type")
        note_counts = df_filtered['Note_Type'].value_counts()
        st.bar_chart(note_counts)

        # 📋 Data Table: All Notes
        st.subheader("📋 Data Table")
        st.dataframe(df_filtered[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']])

        # 📑 Notes per Technician by Type
        st.subheader("📑 Notes per Technician by Type")
        tech_note_group = df_filtered.groupby(['Technician_Name', 'Note_Type']).size().reset_index(name='Count')
        st.dataframe(tech_note_group)

        # 📂 Show "UNKNOWN CASE" in its own section
        unknown_df = df_filtered[df_filtered['Note_Type'] == "UNKNOWN CASE"]
        if not unknown_df.empty:
            st.subheader("🚨 Unknown Cases Detected")
            st.warning(f"{len(unknown_df)} unknown notes found that don’t match any predefined categories.")
            st.dataframe(unknown_df[['Terminal_Id', 'Technician_Name', 'NOTE', 'Ticket_Type']])

        # 📥 Downloadable Summary Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for note_type in df_filtered['Note_Type'].unique():
                subset = df_filtered[df_filtered['Note_Type'] == note_type]
                subset[['Terminal_Id', 'Technician_Name', 'Note_Type', 'Ticket_Type']].to_excel(writer, sheet_name=note_type[:31], index=False)
            note_counts.reset_index().rename(columns={'index': 'Note_Type', 'Note_Type': 'Count'}).to_excel(writer, sheet_name="Note Type Count", index=False)
            tech_note_group.to_excel(writer, sheet_name="Technician Notes Count", index=False)
            if not unknown_df.empty:
                unknown_df[['Terminal_Id', 'Technician_Name', 'NOTE', 'Ticket_Type']].to_excel(writer, sheet_name="Unknown Cases", index=False)

        st.download_button("📥 Download Summary Excel", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
