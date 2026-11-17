# 🔥 Industrial Thermal Intelligence & Emergency Decision-Support Platform

Real-time thermal anomaly detection, risk assessment, and emergency decision
support for industrial and wildfire scenarios — built on free, open data.

---

## 📁 Project Structure

```
├── apps/
│   └── web/              # React + TypeScript + Vite frontend
├── services/
│   └── api/              # Python FastAPI backend
├── packages/
│   └── i18n/             # Shared locale files (en, hi, hinglish)
├── infra/
│   └── docker-compose.yml  # PostgreSQL + PostGIS
├── .env.example          # All required environment variables
└── README.md             # ← You are here
```

---

## 🔑 Getting Your Free API Keys

| Service | What It Does | Sign Up |
|---------|-------------|---------|
| **NASA FIRMS** | Active fire / thermal hotspot data (mandatory) | [firms.modaps.eosdis.nasa.gov/api/area](https://firms.modaps.eosdis.nasa.gov/api/area/) |
| **OpenStreetMap** | Map tiles, Overpass queries, geocoding (mandatory, no key needed) | — |
| **Groq** | LLM for narrative reports & translation | [console.groq.com/keys](https://console.groq.com/keys) |
| **Open-Meteo** | Weather & air quality forecasts (no key needed) | [open-meteo.com](https://open-meteo.com/) |
| **Copernicus Data Space** | Sentinel-1/2 satellite imagery | [dataspace.copernicus.eu](https://dataspace.copernicus.eu/) |
| **Alaska Satellite Facility** | SAR data access | [search.asf.alaska.edu](https://search.asf.alaska.edu/) |
| **OpenTopography** | Elevation / DEM data | [opentopography.org](https://opentopography.org/) |
| **Twilio** *(optional)* | SMS / WhatsApp notifications | [twilio.com](https://www.twilio.com/) |

> **Minimum to run:** You only need a **NASA FIRMS** key. OpenStreetMap and
> Open-Meteo require no keys. Everything else is optional and the app will
> show a "degraded mode" indicator for any missing source.

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (for PostgreSQL + PostGIS)
- **Python 3.11+** (backend)
- **Node.js 18+** & **npm** (frontend)

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd "SIH 2026"
cp .env.example .env
# Edit .env and add at least your FIRMS_MAP_KEY
```

### 2. Start the Database

```bash
docker compose -f infra/docker-compose.yml up -d
# Verify PostGIS is running:
docker exec thermal_intel_db psql -U thermal_user -d thermal_intel \
  -c "SELECT PostGIS_Version();"
```

### 3. Start the Backend

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Health check: curl http://localhost:8000/health
```

### 4. Start the Frontend

```bash
cd apps/web
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## 🌐 Internationalization

The app supports **English**, **Hindi**, and **Hinglish**. All UI strings
live in `packages/i18n/` — never hard-code strings in components.

```typescript
import { t, setLocale } from '@packages/i18n';

setLocale('hi');
console.log(t('app.title'));  // "थर्मल इंटेलिजेंस प्लेटफ़ॉर्म"
```

---

## 🧹 Linting & Formatting

**Backend (Python):**
```bash
cd services/api
ruff check .        # lint
ruff format .       # format
```

**Frontend (TypeScript/React):**
```bash
cd apps/web
npx eslint src/     # lint
npx prettier --write src/  # format
```

---

## 🏗️ Architecture Notes

- **NASA FIRMS + OpenStreetMap** are the mandatory, foundational data sources.
  The app must fully work using only these two.
- **Alert decisions** are deterministic, rule-based code — never LLM-driven.
- **Severity colors** (green / amber / orange / red) are reserved for risk
  levels only.
- **Notifications** default to `console` (log-only). Set
  `NOTIFICATION_PROVIDER=twilio` and configure Twilio credentials for
  SMS/WhatsApp delivery.

---

## 📄 License

TBD
