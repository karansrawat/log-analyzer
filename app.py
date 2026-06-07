import streamlit as st
import pandas as pd
from analyzer import LogAnalyzer
import io
import re

st.set_page_config(page_title="Gemini Log Analyzer & RCA Tool", page_icon="♊", layout="wide")

st.title("♊ Gemini AI-Powered Log Analyzer")
st.subheader("Accelerating Incident Resolution for DevOps & SRE Teams")

# Sidebar for Gemini Configuration
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get a key from Google AI Studio. Leave blank if GEMINI_API_KEY is in your environment.")

# Initialize our Analyzer
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = LogAnalyzer()

if api_key:
    st.session_state.analyzer.set_api_key(api_key)

uploaded_file = st.file_uploader("Upload an application or server log file (.log, .txt)", type=["log", "txt"])

if uploaded_file is not None:
    # Process the stream
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    log_pattern = re.compile(r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<message>.*)')
    log_data = []
    
    for line in stringio:
        match = log_pattern.match(line)
        if match:
            log_data.append(match.groupdict())
            
    df = pd.DataFrame(log_data)
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        st.session_state.analyzer.df = df
        
        # --- UI LAYOUT ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("Total Log Entries Analyzed", len(df))
            anomalies = st.session_state.analyzer.detect_anomalies()
            st.metric("Critical Errors / Anomalies", anomalies.get("total_errors", 0), delta_color="inverse")
            
            st.write("### Log Level Distribution")
            st.bar_chart(df['level'].value_counts())
            
        with col2:
            st.write("### Raw Parsed Log Sample")
            st.dataframe(df.head(10), use_container_width=True)
            
        st.markdown("---")
        st.write("## 🤖 Gemini Root Cause Analysis & Fixes")
        
        if st.button("🚀 Run Gemini Diagnosis", type="primary"):
            with st.spinner("Gemini is parsing patterns and architecting fixes..."):
                try:
                    insights = st.session_state.analyzer.generate_ai_insights(anomalies)
                    st.markdown(insights)
                except Exception as e:
                    st.error(f"Error communicating with Gemini API: {str(e)}")
                    st.info("Tip: Double-check your Gemini API key in the sidebar.")
    else:
        st.error("Could not parse logs. Please ensure they match the format: YYYY-MM-DD HH:MM:SS [LEVEL] Message")