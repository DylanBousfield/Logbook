# Work Logbook (Flask)

A simple, clean logbook for employees to submit work entries (name, date, hours, description). Admin page lists entries with filters and lets you export to Excel.

## Quick start

```bash
# 1) Create a folder and put these files in it (keep structure)
# 2) Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) (Optional) create .env
cp .env.example .env  # then edit FLASK_SECRET

# 5) Run the app
flask --app app run --debug
# The app will be at http://127.0.0.1:5000/
```

## Usage
- **Employee page**: `/` — submit new log entries.
- **Admin page**: `/admin` — filter by name and date range, view totals, and click **Export to Excel**.
- **Export**: `/export` — downloads `work_logs.xlsx` with your current filters applied.

## Deploy (Render/Heroku)
- Use the included `Procfile` with: `web: gunicorn app:app`.
- Set environment variable `FLASK_SECRET` to a long random string.

## Notes
- Database file is created at `instance/worklogs.db` automatically on first run.
- TailwindCSS is loaded via CDN for a nice, modern UI.
- You can add simple protection to `/admin` by putting it behind your own network/VPN or by adding a password gate.
