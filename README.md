# Passport AI Extractor

A production-quality forensic passport document analysis system and audit-ready chronological travel timeline reconstructor powered by **Google Gemini (2.5 Flash)** and **FastAPI + React 18**.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5--Flash-8E75C4.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

---

## 1. Overview

**Passport AI Extractor** is built for immigration analysts, travel auditors, and individuals needing structured extraction of passport data. Users can upload passport pages (biodata page, visa stickers, entry/exit stamp pages) as images or multi-page PDFs.

The application automatically extracts:
1. **Full Personal Details**: Names, passport number, nationality, date of birth, dates of issue/expiry, authority, national ID, and Commonwealth/Indian endorsement fields (father, mother, spouse, address, prior passport details).
2. **TD3 MRZ Verification**: Decodes the 2-line x 44-character Machine Readable Zone, calculating mathematical 7-3-1 modulo-10 check digits (passport number, date of birth, expiry date, composite check) and cross-checking against the visual inspection zone.
3. **Chronological Travel Timeline**: Discovers visas and entry/exit stamps across all uploaded pages, orders them strictly chronologically, computes duration of stay between entry and exit, and summarizes countries visited.

---

## 2. Tech Stack

- **Backend**:
  - Python 3.11+
  - **FastAPI** & **Uvicorn** (REST API)
  - **Pydantic v2** (Type-safe schemas and JSON validation)
  - **google-genai** (Official Google Gemini SDK)
  - **PyMuPDF** (`fitz`) (In-memory PDF-to-image rasterization at 200 DPI)
  - **Pillow** (`PIL`) (Image validation, format normalization, and aspect downsampling)
  - **Pytest** (Automated unit and integration test suite)
- **Frontend**:
  - **React 18** + **Vite 5**
  - **Tailwind CSS** (Modern responsive design with print stylesheet)
  - **react-dropzone** (Multi-file drag-and-drop validation)
  - **lucide-react** (Crisp vector iconography)
  - **Axios** (API communication with progress callbacks)

---

## 3. Privacy & Security Architecture

> [!IMPORTANT]
> **Strict In-Memory Processing**: Uploaded documents are processed entirely in memory buffers (`BytesIO`). Files and extracted records are **never persisted to disk or written to a database**. Once the extraction request completes, buffers are discarded by the Python garbage collector.

- **Zero API Key Leakage**: The Gemini API key is isolated inside `backend/.env` and is never exposed to the frontend browser bundle.
- **Safe Logging**: The server explicitly filters out personal identifiable information (PII) and credentials from console and system logs.
- **Content Verification**: The backend validates file signatures via binary magic bytes (`%PDF-`, JPEG, PNG, WEBP) to prevent disguised executable uploads.
- **Rate Limiting**: Sliding-window rate limiter prevents abuse (up to 30 requests/minute per client).

---

## 4. Project Directory Structure

```
passport-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, rate limiting, routes
│   │   ├── config.py            # Environment configuration & settings
│   │   ├── schemas.py           # Pydantic v2 data models
│   │   ├── prompts.py           # Forensic OCR specialist prompt text
│   │   └── services/
│   │       ├── gemini_service.py   # Gemini API calls, structured output, retries
│   │       ├── file_service.py     # In-memory validation, PDF-to-image, resizing
│   │       ├── mrz_service.py      # ICAO 9303 TD3 MRZ check-digit verification
│   │       └── timeline_service.py # Chronological sorting, deduplication, stay duration
│   ├── tests/
│   │   ├── test_mrz.py          # Unit tests for MRZ check digits & discrepancies
│   │   ├── test_timeline.py     # Unit tests for timeline sorting & days stayed
│   │   ├── test_file_service.py # Unit tests for upload validation & resizing
│   │   └── test_api.py          # FastAPI endpoint integration tests
│   ├── sample_data/             # Synthetic SPECIMEN test images & generator script
│   ├── requirements.txt         # Backend Python dependencies
│   ├── pytest.ini               # Test configuration
│   └── .env.example             # Environment template
│
├── frontend/
│   ├── public/
│   │   └── samples/             # Specimen images for one-click testing
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js        # Axios API client
│   │   ├── components/
│   │   │   ├── Navbar.jsx       # Header, status pill, privacy badge
│   │   │   ├── FileUpload.jsx   # Dropzone, thumbnails, specimen loader
│   │   │   ├── PersonalDetailsCard.jsx # Biodata grid with inline editor
│   │   │   ├── MRZVerificationCard.jsx # Monospace MRZ + check digit badges
│   │   │   ├── TravelTimeline.jsx      # Chronological timeline & stay days
│   │   │   ├── TravelSummaryCard.jsx   # Metrics on countries, visas, stamps
│   │   │   ├── WarningsPanel.jsx       # Alert panel for low-confidence OCR
│   │   │   ├── EditEventModal.jsx      # Modal for editing travel records
│   │   │   └── ExportActions.jsx       # JSON download, CSV export, Print/PDF
│   │   ├── utils/
│   │   │   ├── formatters.js    # Date and status helpers
│   │   │   └── exportUtils.js   # JSON, CSV, and Print generators
│   │   ├── App.jsx              # Main React container
│   │   ├── main.jsx             # React DOM entrypoint
│   │   └── index.css            # Tailwind directives & @media print styles
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
└── README.md                    # Project documentation
```

---

## 5. Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### Step 1: Set Up Backend
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Open `backend/.env` and insert your Gemini API Key:
```ini
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODEL=gemini-2.5-flash
PORT=8000
HOST=0.0.0.0
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

*(Note: If no key is set or the placeholder is left as-is, the application automatically runs in demo specimen mode, returning realistic synthetic extractions for offline review).*

### Step 2: Run Backend Server
```bash
# From the backend directory:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API is now live at `http://127.0.0.1:8000` (API Docs at `http://127.0.0.1:8000/docs`).

### Step 3: Set Up and Run Frontend
In a second terminal window:
```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```
The frontend is now available at `http://localhost:5173`.

---

## 6. Running Unit & Integration Tests

The project includes an extensive test suite verifying MRZ mathematics, timeline chronological sorting, stay calculations, file validation, and API routes.

```bash
# Run all tests using pytest
pytest backend/tests -v
```

All 21 test cases execute in ~3-4 seconds with 100% pass rate:
- `test_mrz.py`: Check digit calculations (7-3-1 weights), invalid check digit detection, composite check digit verification, visual zone discrepancy alerts.
- `test_timeline.py`: Date parsing, deduplication, oldest-to-newest sorting, undated event handling, stay duration calculation between entries/exits, passport status calculation.
- `test_file_service.py`: Magic byte detection, PNG/JPEG/WEBP validation, oversized image resizing, corrupt file rejection.
- `test_api.py`: FastAPI health checks and mock-backed extraction endpoints.

---

## 7. API Reference

### Health Check
`GET /api/health`
- **Response**:
  ```json
  {
    "status": "ok",
    "gemini_model": "gemini-2.5-flash",
    "gemini_configured": true,
    "version": "1.0.0"
  }
  ```

### Document Extraction
`POST /api/extract`
- **Content-Type**: `multipart/form-data`
- **Parameters**: `files` (JPG, PNG, WEBP, or PDF files, max 10MB per file)
- **Response**:
  - `personal_details`: Extracted biodata fields, photo information, and MRZ lines.
  - `travel_events`: Ordered array of visas, entry stamps, exit stamps, and permits.
  - `mrz_validation`: Status of 4 check digits (passport number, DOB, expiry, composite) and detected discrepancies.
  - `passport_status`: `"valid"`, `"expiring_soon"`, or `"expired"`.
  - `days_until_expiry`: Exact days remaining on passport.
  - `travel_summary`: Total unique countries, entries, exits, active visas.
  - `warnings`: Detailed list of partial readings, smudged dates, or visual-MRZ mismatches.

---

## 8. One-Click Demo Testing

Don't have a passport scan on hand?
1. Open the application at `http://localhost:5173`.
2. Click the **"Load Specimen Sample"** button on the upload card.
3. The system loads 3 synthetic high-resolution specimen documents (Biodata page with valid TD3 MRZ, Schengen visa sticker, and international entry/exit stamps).
4. Click **"Extract Details"** to view personal details, MRZ verification badges, and the reconstructed travel timeline with computed stay durations.

---

## 9. Disclaimer

> [!CAUTION]
> **Human Verification Required**: Document extraction accuracy is dependent upon scan resolution, lighting conditions, ink clarity, and document condition. Extracted data and timeline dates should always be reviewed and confirmed by an authorized human operator before being used for official immigration, legal, or travel compliance decisions.

