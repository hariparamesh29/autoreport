import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Project Report", layout="wide")
st.title("📊 Project Progress Dashboard with Gemini AI")

# --- GEMINI API SETUP ---
GEMINI_API_KEY = "AIzaSyAEZnp0jG8nWkiw3iPZ6Zf4DEDMzMTb5QI"  # 🔒 Don't share this key publicly

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("📁 Upload Task Data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file and GEMINI_API_KEY:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

    # Print column names for debugging
    st.write("📄 Uploaded Columns:", df.columns.tolist())

    required_columns = ["Task Name", "Assigned To", "Start Date", "End Date", "Status"]
    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
    else:
        # Convert dates
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

        st.subheader("📋 Task Data")
        st.dataframe(df, use_container_width=True)

        # --- FILTERS ---
        st.sidebar.header("🔍 Filters")
        status_filter = st.sidebar.multiselect("Status", df["Status"].dropna().unique(), default=df["Status"].dropna().unique())
        assignee_filter = st.sidebar.multiselect("Team Member", df["Assigned To"].dropna().unique(), default=df["Assigned To"].dropna().unique())
        filtered_df = df[df["Status"].isin(status_filter) & df["Assigned To"].isin(assignee_filter)]

        # --- KPIs ---
        st.subheader("📌 Key Project Metrics")
        total_tasks = len(filtered_df)
        completed_tasks = len(filtered_df[filtered_df['Status'].str.lower() == 'completed'])
        overdue_tasks = len(filtered_df[filtered_df['End Date'] < datetime.now()])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", total_tasks)
        col2.metric("Completed", completed_tasks)
        col3.metric("Overdue", overdue_tasks)

        # --- CHARTS ---
        st.subheader("📊 Task Status Overview")
        st.plotly_chart(px.pie(filtered_df, names='Status', title='Status Distribution'), use_container_width=True)

        st.subheader("🗓 Gantt Chart")
        gantt_df = filtered_df.copy()
        gantt_df['Duration'] = (gantt_df['End Date'] - gantt_df['Start Date']).dt.days
        gantt = px.timeline(gantt_df, x_start='Start Date', x_end='End Date', y='Task Name', color='Status')
        gantt.update_yaxes(autorange='reversed')
        st.plotly_chart(gantt, use_container_width=True)

        st.subheader("👥 Team Member Task Load")
        team_df = filtered_df.groupby('Assigned To').size().reset_index(name='Task Count')
        st.plotly_chart(px.bar(team_df, x='Assigned To', y='Task Count', title='Tasks by Team Member'), use_container_width=True)

        # --- GEMINI AI SUMMARY ---
        st.subheader("🧠 AI Summary")
        if st.button("Generate Report Summary with Gemini"):
            summary_prompt = f"""
            You are an AI assistant. Based on the following project task data:
            - Total Tasks: {total_tasks}
            - Completed Tasks: {completed_tasks}
            - Overdue Tasks: {overdue_tasks}
            - Team Workload: {team_df.to_dict(orient='records')}

            Provide a concise 3-4 sentence project summary in a professional tone.
            """
            with st.spinner("Generating summary..."):
                response = model.generate_content(summary_prompt)
                st.success("Summary Generated:")
                st.write(response.text)

else:
    if not uploaded_file:
        st.info("Please upload a project CSV or Excel file.")
    if not GEMINI_API_KEY:
        st.info("Enter your Gemini API key to generate summaries.")
