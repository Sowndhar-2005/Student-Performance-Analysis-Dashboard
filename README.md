# B23ADT302 FOUNDATIONS OF DATA SCIENCE

> An interactive data science web application that analyzes student academic performance using machine learning, statistical visualizations, and a modern dark-mode UI.

---

## Features

| Tab | Description |
|-----|-------------|
| **Dashboard** | KPI cards (total students, pass rate, avg score, avg study hours) + 3 summary charts |
| **Data Explorer** | Paginated, filterable table of all 300 student records |
| **Visualizations** | Interactive scatter plot, distribution histogram, and correlation heatmap |
| **ML Model** | Random Forest classifier — accuracy metrics, feature importance, confusion matrix, and live prediction form |
| **Insights** | 6 auto-generated key findings from the dataset |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.x |
| Data & ML | Pandas, NumPy, Scikit-learn (Random Forest) |
| Frontend | Vanilla HTML5, CSS3, JavaScript (ES6+) |
| Charts | Chart.js v4 |
| Fonts | Inter, JetBrains Mono (Google Fonts) |

---

## Project Structure

```
fds/
├── app.py              # Flask server — data generation, API endpoints, ML training
├── requirements.txt    # Python dependencies
├── README.md
└── static/
    ├── index.html      # Single-page application shell (5 tab panels)
    ├── style.css       # Dark-mode design system
    └── main.js         # All chart rendering, table logic, ML interactions
```

---

## Dataset

The dataset is **synthetically generated** on server startup (no external files needed).

- **300 students** across 5 departments: CS, Math, Physics, Commerce, Biology
- **12 features** per student:

| Feature | Type | Range |
|---------|------|-------|
| `student_id` | String | STU0001–STU0300 |
| `age` | Integer | 17–22 |
| `gender` | Categorical | Male / Female |
| `department` | Categorical | CS / Math / Physics / Commerce / Biology |
| `study_hours` | Float | 0–12 h/day |
| `attendance` | Float | 40–100% |
| `prev_score` | Float | 20–100 |
| `sleep_hours` | Float | 3–10 h/day |
| `assignments` | Integer | 0–10 submitted |
| `extracurricular` | Binary | 0 (No) / 1 (Yes) |
| `final_score` | Float | 20–100 (target variable) |
| `pass_fail` | Binary | 0 (Fail) / 1 (Pass, score ≥ 50) |

---

## Machine Learning

- **Algorithm:** Random Forest Classifier (100 estimators)
- **Features used:** `study_hours`, `attendance`, `prev_score`, `sleep_hours`, `assignments`, `extracurricular`
- **Train/Test split:** 80% / 20%
- **Preprocessing:** StandardScaler normalization
- **Typical accuracy:** ~88–92%

The model is trained once at startup and exposed via a REST API for live predictions.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | KPI stats and chart data for the dashboard |
| `GET` | `/api/data` | Paginated student records (supports `page`, `limit`, `dept`, `gender`) |
| `GET` | `/api/scatter` | Scatter plot data (supports `x`, `y` column params) |
| `GET` | `/api/histogram` | Histogram distribution for any numeric column |
| `GET` | `/api/correlation` | Full correlation matrix for numeric features |
| `GET` | `/api/model` | Model accuracy, feature importances, confusion matrix |
| `POST` | `/api/predict` | Live prediction — send student features, receive Pass/Fail + probabilities |
| `GET` | `/` | Serves the frontend SPA |

### Example: Live Prediction Request

```bash
curl -X POST http://127.0.0.1:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "study_hours": 7,
    "attendance": 85,
    "prev_score": 72,
    "sleep_hours": 7.5,
    "assignments": 9,
    "extracurricular": 1
  }'
```

**Response:**
```json
{
  "prediction": "Pass",
  "probability_pass": 94.2,
  "probability_fail": 5.8
}
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# 1. Clone or navigate to the project
cd fds

# 2. (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## Dependencies

```
flask>=3.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
```

---

## Design Highlights

- **Dark-mode first** — `#0a0b0f` background with layered card surfaces
- **Accent palette** — Indigo (`#6366f1`) + Violet (`#8b5cf6`) gradient system
- **Animated KPI counters** — numbers animate from 0 on load
- **Interactive heatmap** — color-coded correlation matrix with hover effects
- **Live ML predictor** — fill inputs → instant pass/fail probability result
- **Smooth tab transitions** — fade + slide-up animation between panels

---

## License

MIT — free to use, modify, and distribute.
