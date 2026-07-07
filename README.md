# 💊 Pharmacy Smart Shortage Manager

An intelligent pharmacy assistant that automatically converts Titan Pharmacy System screenshots, Excel files, CSV files, or PDF reports into accurate, editable shortage reports in under one minute.

## ✨ Features

- **AI-Powered OCR**: Upload screenshots from Titan and get automatic medicine + stock extraction
- **Multi-Format Support**: Screenshots, Excel (.xlsx/.xls), CSV, PDF
- **Smart Duplicate Detection**: Automatically merges duplicate medicine entries
- **Priority System**: Color-coded urgency levels (Critical, High, Medium, Safe)
- **Editable Reports**: Manually adjust quantities before exporting
- **Multiple Export Formats**: Excel, PDF, CSV, Print-friendly
- **Dark/Light Mode**: Professional medical design with theme support
- **Arabic + English**: Full bilingual support with RTL layout
- **Responsive Design**: Mobile-first with tablet and desktop support

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, Tailwind CSS |
| Backend | Python FastAPI |
| Database | PostgreSQL 16 |
| OCR | PaddleOCR, Tesseract (fallback) |
| Auth | JWT, bcrypt |

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 16 (or Docker)

### Option 1: Docker (Recommended)

```bash
cp .env.example .env
docker-compose up -d
```

Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📂 Project Structure

```
pharmacy-smart-shortage-manager/
├── frontend/          # Next.js 14 (App Router)
├── backend/           # Python FastAPI
├── docker-compose.yml # Container orchestration
├── .env.example       # Environment template
└── README.md
```

## 📝 License

Private — Pharmacy data management tool.
