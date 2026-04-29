# Email Visibility System

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-API-009688.svg) ![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-ff4b4b.svg) ![SQLite](https://img.shields.io/badge/SQLite-storage-003b57.svg)

*A FastAPI and Streamlit system for tracking intern email updates, progress, risk, and missed daily reports.*

---

## Overview

The **Email Visibility System** monitors daily intern work updates received through email. It fetches messages from an IMAP inbox, filters registered interns, stores email activity in SQLite, summarizes updates, tracks progress, computes risk, and sends reminder emails when expected updates are missing.

The project includes:

- A **FastAPI backend** for ingestion, processing, HR views, risk reports, health checks, and platform snapshots.
- A **Streamlit dashboard** for HR-facing progress analytics, reminder history, timelines, and raw update inspection.
- A background **scheduler** that fetches inbox updates and runs compliance checks.

## Features

### Email Ingestion

- Fetches emails securely from an IMAP inbox.
- Filters messages to registered intern email addresses.
- Cleans HTML/plain-text email bodies.
- Avoids duplicate processing using message IDs and UID tracking.
- Stores fetched emails and audit events in SQLite.

### Progress Processing

- Converts structured daily updates into professional summaries.
- Falls back to a local Ollama LLM summarizer for free-form email text.
- Tracks project, status, intern ID, summary, and timestamps.
- Exposes processed updates through API endpoints.

### HR Dashboard

- Displays intern activity and consistency metrics.
- Shows monthly reminder analysis and calendar views.
- Visualizes momentum trends using Plotly.
- Provides a timeline of recent intern updates.
- Includes expandable raw HR data for inspection.

### Compliance Monitoring

- Checks whether interns missed expected daily updates.
- Sends reminder emails through Gmail SMTP.
- Stores reminder records for monthly analysis.
- Runs scheduled checks in the Asia/Kolkata timezone.

### Platform Integration

- Provides a canonical platform snapshot endpoint.
- Groups intern status, latest project, risk, and last update time.
- Includes a placeholder adapter for future internal platform push flows.

## Tech Stack

- **Backend API**: FastAPI, Uvicorn
- **Dashboard**: Streamlit
- **Database**: SQLite, SQLAlchemy
- **Scheduling**: APScheduler
- **Email**: IMAP, SMTP
- **Parsing**: BeautifulSoup
- **Visualization**: Pandas, Plotly
- **LLM Summaries**: Local Ollama endpoint

## Project Structure

```txt
email_visibility_system/
|-- backend/
|   |-- core/                 # Config, database, logger
|   |-- domain/               # SQLAlchemy models and intern allowlist
|   |-- integrations/         # IMAP, SMTP, LLM integrations
|   |-- platform_adapter/     # Platform snapshot schemas and adapter
|   |-- scheduler/            # Background jobs
|   |-- services/             # Ingestion, tracking, risk, compliance
|   `-- main.py               # FastAPI application
|-- dashboard.py              # Streamlit HR dashboard
|-- emails.db                 # Local SQLite database
|-- last_uid.txt              # Last fetched IMAP UID tracker
|-- requirements.txt          # Python dependencies
`-- README.md
```

## Installation

### Prerequisites

- Python 3.10 or higher
- An email inbox with IMAP access enabled
- A Gmail app password or SMTP-compatible credentials for reminders
- Optional: Ollama running locally with the `llama3` model for free-form summaries

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/email-visibility-system.git
cd email-visibility-system
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```env
EMAIL_HOST=imap.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
FETCH_INTERVAL_SECONDS=30
```

5. Update the registered intern list in:

```txt
backend/domain/interns.py
```

## Running Locally

Start the FastAPI backend:

```bash
uvicorn backend.main:app --reload
```

The API will be available at:

```txt
http://127.0.0.1:8000
```

Start the Streamlit dashboard in a second terminal:

```bash
streamlit run dashboard.py
```

The dashboard will be available at:

```txt
http://localhost:8501
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/email/ingest` | Manually ingest an email payload |
| `POST` | `/email/process` | Process pending emails in the background |
| `GET` | `/email/status` | Check processing job status |
| `GET` | `/hr/updates` | Return processed intern work updates |
| `GET` | `/hr/risk` | Return risk status grouped by intern |
| `GET` | `/hr/intern/{intern_email}` | Return progress for one intern |
| `GET` | `/integration/platform/snapshot` | Return platform-ready intern status snapshot |

## Requirements

```txt
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
streamlit>=1.32.0
sqlalchemy>=2.0.0
pydantic>=2.6.0
python-dotenv>=1.0.0
python-dateutil>=2.8.2
requests>=2.31.0
beautifulsoup4>=4.12.0
apscheduler>=3.10.4
pandas>=2.2.0
plotly>=5.19.0
```

## Screenshots 
  ### Reminder Analysis <img src="Assets/Reminder Analysis.png" width = "700"/>

  ### Reminder Calendar <img src="Assets/Reminder Calendar.png" width = "700"/>

  ### Momentum Trend    <img src="Assets/Momentum Trend.png" width = "700"/>



## Known Limitations

- The dashboard currently expects the backend API URL to be configured in `dashboard.py`.
- The local SQLite database is convenient for development but should be backed up if the data is important.
- Registered interns are stored in code inside `backend/domain/interns.py`; for production, move this list to a database or admin-managed config.
- Local Ollama summarization requires Ollama to be running on the same machine.

## Acknowledgments

- FastAPI and Streamlit for the application framework.
- SQLAlchemy for database modeling.
- Plotly and Pandas for dashboard analytics.
- APScheduler for background email and compliance jobs.
