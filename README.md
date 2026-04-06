# PharmCheck SK

Drug interaction checker POC targeting the Slovak pharmacy market.

## Quick Start

### 1. Seed the database

```bash
python3 scripts/seed_demo_data.py
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload
```

Or from root:
```bash
python3 -m uvicorn backend.main:app --port 8000 --reload
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Docker

```bash
docker-compose up --build
```

## Demo Scenarios

1. **Elderly Polypharmacy** — Warfarin + Nurofen + Helicid + Simvacard + Norvasc
2. **Depression + Pain** — Zoloft + Tramal + Paralen + Voltaren
3. **Antibiotic Interactions** — Ciprinol + Siofor + Warfarin

## Data

- 117 Slovak medications (trade names, active substances, ATC codes)
- 68 drug-drug interactions (26 Major, 33 Moderate, 9 Minor)
- Interaction data based on DDInter 2.0 evidence
