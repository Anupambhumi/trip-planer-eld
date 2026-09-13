# TripPilot AI — ELD Trip Planner

Plan FMCSA-compliant truck routes, generate Hours-of-Service (HOS) ELD logs, and review trip history.

**Live app:** [https://trip-planer-eld.vercel.app](https://trip-planer-eld.vercel.app)  
**API:** [https://trip-planer-eld.onrender.com](https://trip-planer-eld.onrender.com)

## Features

- Step-by-step trip planner: current location, pickup, dropoff, and cycle hours used
- City autocomplete and real road routing
- FMCSA 70-hour / 8-day HOS schedule (drive limits, breaks, fuel stops, 34-hour restart)
- Interactive route map and stop timeline
- Daily ELD log sheets (print / PDF)
- Trip history in this browser, with optional MongoDB or SQLite on the server

## Project layout

```
backend/     Django REST API (planner, HOS, geocoding, trip storage)
frontend/    React + Vite UI
```

| Page | Route | Purpose |
|------|--------|---------|
| Home | `/` | Dashboard and charts for the active trip |
| Trips | `/trips` | Trip history |
| Plan | `/plan` | Create a trip and generate route + logs |
| Route | `/route` | Map and stop timeline |
| HOS | `/hos` | Duty-status timeline and cycle gauges |
| Logs | `/logs` | Daily ELD log sheets |

## Requirements

- Python 3.12+
- Node.js 18+
- Optional: MongoDB (local or Atlas). If it is missing, the API uses SQLite.

## Local setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux

python manage.py migrate
python manage.py runserver
```

API runs at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux

npm run dev
```

UI runs at `http://localhost:5173` and calls the backend at `http://localhost:8000`.

## Environment variables

**Backend** (`backend/.env`)

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Django secret |
| `DJANGO_DEBUG` | `True` locally, `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Hosts allowed to reach the API |
| `CORS_ALLOW_ALL` | `True` to allow the Vercel frontend |
| `MONGODB_URI` | Optional. Blank or unreachable → SQLite fallback |
| `MONGODB_DB_NAME` | Default `eld_trip_planner` |

**Frontend**

| File | Variable | Purpose |
|------|----------|---------|
| `frontend/.env` | `VITE_API_URL` | Local API, default `http://localhost:8000` |
| `frontend/.env.production` | `VITE_API_URL` | Production API (`https://trip-planer-eld.onrender.com`) |

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health/` | Service and storage backend |
| `POST` | `/api/plan/` | Plan a trip (route + HOS logs) |
| `GET` | `/api/geocode/suggest/?q=` | City autocomplete |
| `GET` | `/api/trips/` | Saved trip list |
| `GET` | `/api/trips/<id>/` | One saved trip |

Example plan request:

```json
{
  "current_location": "New York",
  "pickup_location": "Dallas",
  "dropoff_location": "Denver",
  "current_cycle_used_hours": 10
}
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python manage.py test trips
```

## Deployment

- **Frontend:** Vercel, root directory `frontend`. Production builds use `frontend/.env.production`.
- **Backend:** Render (`backend/render.yaml`). Set `MONGODB_URI` in the Render dashboard for durable trip storage. Without it, SQLite is used and data can reset when the free instance sleeps or redeploys.

The first request after Render sleeps can take about a minute.

## License

Private project — not licensed for public reuse unless you add a license.
