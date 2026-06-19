# RouteGuard AI — Developer & Contribution Guide

This document describes setup, testing, and development workflows for RouteGuard AI.

## Environment Installation

### 1. Backend Gateway (Node.js)
```bash
cd backend
npm install
npm run dev
```

### 2. Frontend Application (Next.js)
```bash
cd frontend
npm install
npm run dev
```

### 3. Python Microservices
Set up a Python virtual environment (version 3.10+ recommended) in the root directory:
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Start the engines:
- **Graph Engine**: `python graph-engine/main.py`
- **AI Engine**: `python ai-engine/main.py`
- **GIS Engine**: `python gis-engine/main.py`

---

## Running Verification Tests

To verify backend gateway endpoints:
```bash
cd backend
npm run test
```

To verify Python graph algorithms:
```bash
pytest tests
```
