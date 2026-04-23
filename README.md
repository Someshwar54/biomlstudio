# BioMLStudio

BioMLStudio is a comprehensive, AI-powered no-code platform designed for bioinformatics and machine learning workflows. It empowers researchers, biologists, and data scientists to easily upload datasets, run pre-built pipelines, train custom models, and analyze results without writing any code.

##  Architecture

The platform is built using a modern, scalable architecture separated into a frontend and a backend.

### Frontend
- **Framework:** Next.js 16 (React 19)
- **Language:** TypeScript
- **Styling:** Tailwind CSS 4 with Radix UI components for a responsive and accessible design.
- **Charts/Visualizations:** Recharts
- **AI Integrations:** `@google/generative-ai` for intelligent features and insights.
- **Routing:** App Router (`app/`) architecture.

### Backend
- **Framework:** FastAPI (Python) for high-performance API endpoints.
- **Database:** PostgreSQL via SQLAlchemy with Alembic for migrations.
- **Asynchronous Task Queue:** Celery with Redis for handling long-running ML jobs.
- **Machine Learning & Data Science:** Scikit-Learn, XGBoost, Pandas, Numpy, and SHAP for model training, inference, and explainability.
- **Bioinformatics Tools:** Biopython, PyFAIDX, and PyVCF3 for processing DNA/RNA/Protein sequences.

##  Core Modules

BioMLStudio is divided into exactly 8 core modules, accessible via the main application interface:

1. **Dashboard (`/dashboard`)**: Central overview of platform statistics, recent activities, and quick access to tools.
2. **Dataset Upload & Preprocessing (`/upload`)**: Drag-and-drop interface supporting FASTA, CSV, TSV, and JSON files with automatic type detection.
3. **Domain-Specific Pipelines (`/pipelines`)**: Pre-built bioinformatics workflows including ProtBERT and ESM2 integrations.
4. **AutoML Builder (`/automl`)**: Automated model selection and hyperparameter tuning for various algorithms (Random Forest, SVM, Neural Networks).
5. **Model Explorer (`/model-explorer`)**: Visualizations for model architecture, layer-by-layer analysis, and performance metrics.
6. **Inference Engine (`/inference`)**: Real-time predictions and batch inference capabilities.
7. **Dataset Analysis (`/datasets`)**: Deep dive into dataset statistics, sequence composition analysis, and quality assessment.
8. **Test Cases & Reports (`/reports`)**: Comprehensive logging, performance reports, and model comparison dashboards.

##  Getting Started

### Prerequisites
- Node.js (v20+)
- Python 3.10+
- PostgreSQL
- Redis

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Access the application at `http://localhost:3000`.

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
5. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

##  Project Structure

```text
biomlstudio/
├── frontend/               # Next.js React UI
│   ├── app/                # App router and page modules
│   ├── components/         # Reusable UI components
│   ├── lib/                # API client and utilities
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
├── backend/                # FastAPI backend
│   ├── alembic/            # Database migrations
│   ├── app/                # Core API logic, routes, and tasks
│   ├── models/             # SQLAlchemy database models
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Containerization for backend
├── *.fasta / *.csv         # Sample datasets for testing
├── TRANSFORMATION_SUMMARY.md # Detailed module overview
└── README.md               # This documentation
```
