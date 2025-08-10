# LinkedIn CaseBot
Automated LinkedIn case explainer bot with manual approval UI.

## Setup

1. Copy `.env.example` to `.env` and fill in your keys.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run locally:
   ```
   python casebot_engine.py
   flask run
   ```

## Deploy on Render
- Connect GitHub repo.
- Use `render.yaml` to set up both web service (UI) and daily cron job.
