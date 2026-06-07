# ♊ Gemini AI Log Analyzer

An AI-powered DevOps tool that ingests application or server log files, automatically detects error patterns and unusual spikes, and uses Google Gemini to generate an instant Root Cause Analysis (RCA) along with actionable mitigation steps.

This project reduces incident resolution time (MTTR) dramatically for SRE and DevOps teams.

---

## 🛠️ Tech Stack
- **Python** (Core engine)
- **Pandas** (Log analysis & rolling-window error detection)
- **Google Gen AI SDK** (Gemini 2.5 Flash API)
- **Streamlit** (Interactive Dashboard UI)

---

## 📁 Repository Structure
- `app.py` — The Streamlit front-end user interface.
- `analyzer.py` — Core logic handling log parsing and Gemini API interactions.
- `requirements.txt` — Python dependencies needed to execute the application.
- `sample.log` — A pre-formatted log file containing sample error spikes for testing.
- `.env` — Local configuration file for your secret API keys (Should be hidden in production).

---

## 💻 Local Setup & Installation

### 1. Clone the repository & Navigate inside:
```bash
cd log-analyzer
