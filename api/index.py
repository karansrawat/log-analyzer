from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import io
import re
import os
import pandas as pd
from google import genai
from google.genai import types

app = FastAPI()

# Allow the frontend to talk to the backend smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def analyze_log_data(contents: str):
    """Parses logs locally inside the serverless execution environment."""
    log_pattern = re.compile(r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<message>.*)')
    log_data = []
    
    for line in contents.splitlines():
        match = log_pattern.match(line)
        if match:
            log_data.append(match.groupdict())
            
    df = pd.DataFrame(log_data)
    if df.empty:
        return None
        
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    errors_df = df[df['level'].isin(['ERROR', 'CRITICAL', 'FATAL'])]
    error_counts = errors_df.set_index('timestamp').resample('5Min').count()['level']
    spikes = error_counts[error_counts > 5]
    
    return {
        "total_logs": len(df),
        "total_errors": len(errors_df),
        "error_summary": errors_df['message'].value_counts().to_dict(),
        "spikes_detected": spikes.to_dict()
    }

@app.post("/api/analyze")
async def analyze_log(file: UploadFile = File(...), custom_key: str = Form(None)):
    try:
        # Read file contents safely in memory
        contents = (await file.read()).decode("utf-8")
        metrics = analyze_log_data(contents)
        
        if not metrics:
            return {"error": "Could not parse logs. Ensure format is YYYY-MM-DD HH:MM:SS [LEVEL] Message"}
            
        # Determine which API Key to use (Form input or Vercel Environment Variable)
        api_key = custom_key if custom_key else os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {"error": "Gemini API Key missing. Add it to Vercel environment or input it directly."}
            
        # Initialize Gemini Client
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are an expert Principal SRE. Analyze this log error data and provide:
        1. **Root Cause Analysis (RCA)**: What went wrong?
        2. **Immediate Mitigation**: Quick fix steps.
        3. **Long-term Fix**: Architectural changes.

        Aggregated Log Errors: {str(metrics['error_summary'])}
        Spike Windows: {str(metrics['spikes_detected'])}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a precise, technical enterprise incident response assistant.",
                temperature=0.2,
            )
        )
        
        return {
            "total_logs": metrics["total_logs"],
            "total_errors": metrics["total_errors"],
            "analysis": response.text
        }
        
    except Exception as e:
        return {"error": str(e)}