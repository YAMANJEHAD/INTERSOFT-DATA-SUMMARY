import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

st.set_page_config(page_title="Note Analyzer", layout="wide")
st.title("\U0001F4CA INTERSOFT Analyzer")

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

# Input username at the top
st.markdown("### \U0001F464 Enter your name")
username = st.text_input("Name", placeholder="Enter your name here")

uploaded_file = st.file_uploader("\U0001F4C1 Upload Excel File", type=["xlsx"])

# Required columns
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
        missing = [k for k, v in col_mapping.items() if v is None]
        st.warning(f"Missing required columns: {missing}")
    else:
        df.rename(columns=col_mapping, inplace=True)
        if not all(col in df.columns for col in required_cols):
            st.warning("Still missing columns after rename.")
        else:
            df['Note_Type'] = df['NOTE'].apply(classify_note)
            df = df[~df['Note_Type'].isin(['DONE', 'NO J.O'])]

            st.success("\u2705 File processed successfully!")

            st.subheader("\U0001F4C8 Notes per Technician")
            tech_counts = df.groupby('TECHNICIAN_NAME')['Note_Type'].count().sort_values(ascending=False)
            st.bar_chart(tech_counts)

            st.subheader("\U0001F4CA Notes by Type")
            note_counts = df['Note_Type'].value_counts()
            st.bar_chart(note_counts)

            st.subheader("\U0001F4CB Notes Data")
            st.dataframe(df[['TERMINAL_ID', 'TECHNICIAN_NAME', 'Note_Type', 'TICKET_TYPE']])

            st.subheader("\U0001F4D1 Notes per Technician by Type")
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

            st.download_button("\U0001F4E5 Download Summary Excel", output.getvalue(), "summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ========== FILE HISTORY ========== #
st.sidebar.header("\U0001F4DA File History")

if os.path.exists(LOG_FILE):
    logs_df = pd.read_csv(LOG_FILE)
    logs_df = logs_df.sort_values(by="Date", ascending=False)
    file_names = logs_df["File"].tolist()

    st.sidebar.write("### \U0001F4C4 Processed Files")

    # Search
    search_query = st.sidebar.text_input("Search by username or file name")
    if search_query:
        logs_df = logs_df[logs_df['Username'].str.contains(search_query, case=False) |
                          logs_df['File'].str.contains(search_query, case=False)]

    st.sidebar.dataframe(
        logs_df[['Username', 'File', 'Date']]
        .rename(columns={
            'Username': '👤 Name',
            'File': '📄 File',
            'Date': '🕒 Uploaded At'
        }).reset_index(drop=True),
        use_container_width=True
    )

    selected_file = st.sidebar.selectbox("Select a file", logs_df['File'].unique().tolist())

    if selected_file:
        file_info = logs_df[logs_df["File"] == selected_file].iloc[0]
        time_passed = time_since(file_info['Date'])
        file_path = os.path.join(DATA_DIR, selected_file)

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 Username:** {file_info['Username']}")
        st.sidebar.markdown(f"**📅 Upload Time:** {file_info['Date']}")
        st.sidebar.markdown(f"**⏱️ Time Ago:** {time_passed}")

        # زر تحميل
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.sidebar.download_button("⬇️ Download", f, file_name=selected_file, use_container_width=True)

        # زر حذف
        if st.sidebar.button("🗑️ Delete", use_container_width=True):
            os.remove(file_path)
            logs_df = logs_df[logs_df["File"] != selected_file]
            logs_df.to_csv(LOG_FILE, index=False)
            st.sidebar.success("✅ File deleted successfully.")
            st.experimental_rerun()

        # زر بريفيو
        if st.sidebar.button("👁️ Preview", use_container_width=True):
            st.session_state['preview_file'] = selected_file
            st.rerun()

        if 'preview_file' in st.session_state and st.session_state['preview_file'] == selected_file:
            st.markdown(f"### 👁️ Preview of `{selected_file}`")
            preview_path = os.path.join(DATA_DIR, selected_file)
            try:
                preview_df = pd.read_csv(preview_path)
                st.dataframe(preview_df.head(50))
            except Exception as e:
                st.warning(f"⚠️ Unable to preview file: {e}")
else:
    st.sidebar.info("No file history yet.")
