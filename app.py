import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="SmartAttend: AI Attendance Regulator",
    page_icon="🎓",
    layout="wide"
)

# Clean, adaptive styling that works automatically on both Light and Dark themes
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: white !important;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 SmartAttend: AI Attendance Regulator")
st.markdown("---")

# 1. Load the dataset
try:
    df = pd.read_csv("Attendance_Schedule_Master.csv")
except FileNotFoundError:
    st.error("⚠️ Attendance_Schedule_Master.csv not found in the project folder!")
    st.stop()

# Clean up status column
df['Status_Clean'] = df['Status'].apply(lambda x: 1 if str(x).strip().lower() in ['present', 'p', '1'] else 0)

# 2. Strict Batch Filtering (Sidebar)
st.sidebar.header("⚙️ Control Panel")
if 'Batch' in df.columns:
    batches = df['Batch'].dropna().unique()
    selected_batch = st.sidebar.selectbox("Select Your Batch:", options=batches)
    filtered_df = df[df['Batch'] == selected_batch].copy()
else:
    filtered_df = df.copy()
    st.sidebar.info("No 'Batch' column found in CSV. Showing all records.")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Use the logger below to record daily attendance changes. Your metrics and safe skips update live.")

# 3. Interactive Attendance Logger by Subject & Date
st.subheader("✏️ Live Attendance Logger")
with st.container():
    if 'Subject' in filtered_df.columns and 'Date' in filtered_df.columns and 'Status' in filtered_df.columns:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            subjects = filtered_df['Subject'].unique()
            selected_subject = st.selectbox("Subject:", options=subjects)
        with col2:
            dates_for_subject = filtered_df[filtered_df['Subject'] == selected_subject]['Date'].unique()
            selected_date = st.selectbox("Date:", options=dates_for_subject)
        with col3:
            new_status = st.selectbox("Status:", options=["Present", "Absent"])
        with col4:
            st.write("")
            st.write("")
            update_btn = st.button("Apply Changes")

        if update_btn:
            match_idx = df[(df['Subject'] == selected_subject) & (df['Date'] == selected_date) & (df['Batch'] == selected_batch)].index
            if not match_idx.empty:
                df.loc[match_idx, 'Status'] = new_status
                df.to_csv("Attendance_Schedule_Master.csv", index=False)
                st.success(f"Successfully updated **{selected_subject}** on **{selected_date}** to **{new_status}**!")
                filtered_df = df[df['Batch'] == selected_batch].copy()
                filtered_df['Status_Clean'] = filtered_df['Status'].apply(lambda x: 1 if str(x).strip().lower() in ['present', 'p', '1'] else 0)
            else:
                st.warning("Could not find the matching record for this batch.")

st.markdown("---")

# 4. Aggregate Data for the Selected Batch Only
summary_df = filtered_df.groupby('Subject').agg(
    Total_Conducted=('Status', 'count'),
    Total_Attended=('Status_Clean', 'sum')
).reset_index()

summary_df['Attendance_Percentage'] = summary_df['Total_Attended'] / summary_df['Total_Conducted']
summary_df['Safe_Skips'] = ((summary_df['Total_Attended'] - (0.8 * summary_df['Total_Conducted'])) / 0.8).apply(lambda x: max(0, int(x)))
summary_df['Attendance_Percentage_Display'] = (summary_df['Attendance_Percentage'] * 100).round(2).astype(str) + '%'

# Summary Metrics Cards
total_cond = summary_df['Total_Conducted'].sum()
total_att = summary_df['Total_Attended'].sum()
overall_pct = (total_att / total_cond * 100) if total_cond > 0 else 0
total_safe_skips = summary_df['Safe_Skips'].sum()

m1, m2, m3 = st.columns(3)
m1.metric(label="📊 Overall Attendance", value=f"{overall_pct:.2f}%")
m2.metric(label="✅ Total Attended", value=f"{total_att} / {total_cond}")
m3.metric(label="🛡️ Total Safe Skips Available", value=total_safe_skips)

st.markdown("")

# Display Subject-wise Matrix Table
st.subheader(f"📈 Subject-wise Summary & Safe Skips — Batch {selected_batch}")
display_table = summary_df[['Subject', 'Total_Conducted', 'Total_Attended', 'Attendance_Percentage_Display', 'Safe_Skips']]
display_table.columns = ['Subject', 'Total Conducted', 'Total Attended', 'Attendance %', 'Safe Skips']
st.dataframe(display_table, use_container_width=True, hide_index=True)

# Display Full Raw Records
with st.expander(f"📋 View Full Raw Attendance Logs (Batch {selected_batch})"):
    raw_display = filtered_df[['Date', 'Day', 'Subject', 'Status']]
    st.dataframe(raw_display, use_container_width=True, hide_index=True)