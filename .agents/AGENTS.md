# Industrial Thermal Intelligence & Emergency Decision-Support Platform — Project Rules

These rules apply to **every task** in this workspace.

---

## Data Sources & APIs

- **Use only free-tier APIs:** NASA FIRMS, OpenStreetMap (Overpass + Nominatim), Open-Meteo (weather + air quality), Copernicus Data Space (Sentinel-1/2), Alaska Satellite Facility (ASF), OpenTopography. No paid-only services.
- **NASA FIRMS and OSM are mandatory and foundational** — the app must fully work using only these two even if every other adapter is disabled.

## LLM Usage (Groq)

- Use Groq (`GROQ_API_KEY`, OpenAI-compatible endpoint) for **language/reasoning tasks only**: narrative explanations, translation, report triage.
- **Never let an LLM output alone decide whether to send an alert** — alert decisions are deterministic, rule-based code.

## No Mock Data

- **Never use mock/fake/hard-coded sample data** in the running app.
- If a source is unavailable, show a clear **"degraded mode" / stale-data indicator** instead.

## Frontend & Theming

- Frontend uses a **light theme by default**: light surfaces, dark text.
- **Severity colors** (green / amber / orange / red) are **reserved for risk levels only**.

## Internationalization (i18n)

- Support **English, Hindi, and Hinglish** via an i18n system.
- **No hard-coded strings** in components.

## Alert & Safety Logic

- A **persistent thermal source alone must never trigger a public alert**.
- **Low confidence must never trigger an evacuation-level message**.
- Cause of fire is always **"probable cause with confidence,"** never stated as confirmed.

## Verification & Delivery

- After each task: **run/build the app**, verify it actually works (use the browser subagent for UI tasks), and produce a **walkthrough** before stopping.

## Approval Gates

- **Ask for approval** on the Implementation Plan before writing code if the task touches:
  - The database schema
  - The alert-decision logic
  - Adding a new external API adapter
