import re
import os
import pandas as pd
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class LogAnalyzer:
    def __init__(self, file_path=None, dataframe=None):
        self.df = dataframe if dataframe is not None else pd.DataFrame()
        # Initialize the Gemini Client
        # It automatically picks up the GEMINI_API_KEY environment variable
        self.client = genai.Client() if os.environ.get("GEMINI_API_KEY") else None

    def set_api_key(self, api_key):
        """Allows dynamic API key configuration from the Streamlit UI."""
        os.environ["GEMINI_API_KEY"] = api_key
        self.client = genai.Client()

    def load_logs(self, file_path):
        """Parses a standard log file into a Pandas DataFrame."""
        log_data = []
        log_pattern = re.compile(r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<message>.*)')
        
        with open(file_path, 'r') as f:
            for line in f:
                match = log_pattern.match(line)
                if match:
                    log_data.append(match.groupdict())
        
        self.df = pd.DataFrame(log_data)
        if not self.df.empty:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        return self.df

    def detect_anomalies(self):
        """Identifies error counts and flags unusual spikes."""
        if self.df.empty:
            return {}

        errors_df = self.df[self.df['level'].isin(['ERROR', 'CRITICAL', 'FATAL'])]
        
        # Resample by 5-minute windows to spot rapid error accumulations
        error_counts = errors_df.set_index('timestamp').resample('5Min').count()['level']
        spikes = error_counts[error_counts > 5]
        
        return {
            "total_errors": len(errors_df),
            "error_summary": errors_df['message'].value_counts().to_dict(),
            "spikes_detected": spikes.to_dict()
        }

    def generate_ai_insights(self, error_context):
        """Sends aggregated error data to Gemini for Root Cause Analysis (RCA)."""
        if not self.client:
            raise ValueError("Gemini API Client is not initialized. Please provide a valid API key.")
            
        if not error_context.get("total_errors"):
            return "No critical errors or anomalies detected in the provided log file."

        prompt = f"""
        You are an expert Principal SRE and DevOps Engineer. Analyze the following aggregated log error data and provide:
        1. **Root Cause Analysis (RCA)**: What likely went wrong based on these patterns?
        2. **Immediate Mitigation**: What steps should the triage team take right now?
        3. **Long-term Fix**: Code, infrastructural, or configuration changes to prevent this from happening again.

        Aggregated Log Errors:
        {str(error_context['error_summary'])}

        Spike Windows Detected:
        {str(error_context['spikes_detected'])}
        """

        # Using modern SDK configuration blocks
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a precise, technical enterprise incident response assistant. Give direct, actionable engineering feedback.",
                temperature=0.2, # Kept low for deterministic, accurate technical responses
            )
        )
        return response.text