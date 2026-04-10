"""
╔══════════════════════════════════════════════════════════════════════╗
║       Student Performance Analysis Dashboard  —  app.py             ║
║  Tech : Streamlit · Pandas · NumPy · Matplotlib · Seaborn · Sklearn ║
║  Run  : streamlit run app.py                                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ──────────────────────────────────────────────────────────────────────
# SECTION 0 ▸ Imports
# ──────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import io
import warnings

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────
# SECTION 1 ▸ Page Config & Global Style
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for a clean, modern look
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Hide Streamlit top header / Deploy bar ── */
[data-testid="stHeader"],
header[data-testid="stHeader"] {
    background: #0f1117 !important;
    border-bottom: 1px solid #1e2333;
}
/* Hide Deploy button & toolbar icons ── */
[data-testid="stToolbar"],
[data-testid="manage-app-button"],
.stDeployButton { display: none !important; }

/* ── Background ── */
.stApp { background: #0f1117; color: #e6e6e6; }

/* ── Remove top gap ── */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 0.5rem !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 0.5rem !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1e2130, #252a3a);
    border: 1px solid #2e3347;
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.4);
}
[data-testid="metric-container"] label { color: #9aa0b4 !important; font-size: 0.78rem; }
[data-testid="metric-container"] [data-testid="metric-value"] {
    color: #7c9cff !important; font-size: 1.8rem !important; font-weight: 700;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #141724; border-right: 1px solid #1e2333; }
[data-testid="stSidebar"] * { color: #c8cedf; }

/* ── Section headings ── */
.section-title {
    font-size: 1.15rem; font-weight: 700; color: #7c9cff;
    border-left: 4px solid #7c9cff; padding-left: 10px;
    margin: 1.4rem 0 0.8rem;
}

/* ── Buttons ── */
div.stButton > button {
    background: linear-gradient(135deg, #4f6eff, #7c9cff);
    color: #fff; border: none; border-radius: 10px;
    padding: 0.55rem 2rem; font-weight: 600; font-size: 1rem;
    transition: transform .15s, box-shadow .15s;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 22px rgba(127,156,255,.45);
}

/* ── Prediction result box ── */
.pred-box {
    background: linear-gradient(135deg, #1b2340, #23304f);
    border: 1px solid #3a4f8a;
    border-radius: 14px; padding: 24px 28px;
    text-align: center; margin-top: 1rem;
}
.pred-value { font-size: 2.5rem; font-weight: 700; color: #7c9cff; }
.pred-label { font-size: 0.9rem; color: #9aa0b4; margin-top: 4px; }

/* ── Dividers ── */
hr { border-color: #2e3347; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# SECTION 2 ▸ Helper — Matplotlib dark theme wrapper
# ──────────────────────────────────────────────────────────────────────
def dark_fig(figsize=(8, 4)):
    """Return a Matplotlib figure pre-styled for the dark UI."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#1a1e2c")
    ax.set_facecolor("#1a1e2c")
    ax.tick_params(colors="#9aa0b4")
    ax.xaxis.label.set_color("#9aa0b4")
    ax.yaxis.label.set_color("#9aa0b4")
    ax.title.set_color("#c8cedf")
    for spine in ax.spines.values():
        spine.set_edgecolor("#2e3347")
    return fig, ax


# ──────────────────────────────────────────────────────────────────────
# SECTION 3 ▸ Dataset Generator (used when no CSV is uploaded)
# ──────────────────────────────────────────────────────────────────────
@st.cache_data
def generate_dataset(n: int = 200) -> pd.DataFrame:
    """
    Generate a synthetic student dataset with realistic correlations.
    n = number of student records (default 200).
    """
    np.random.seed(42)
    subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"]
    genders  = ["Male", "Female"]

    student_id   = [f"STU{str(i+1).zfill(4)}" for i in range(n)]
    gender       = np.random.choice(genders, n, p=[0.52, 0.48])
    subject      = np.random.choice(subjects, n)
    study_hours  = np.random.normal(5.5, 2.0, n).clip(0.5, 12.0).round(1)
    attendance   = np.random.normal(78, 12, n).clip(40, 100).round(1)

    # Marks are positively correlated with study hours & attendance + noise
    marks = (
        study_hours * 5.2 +
        attendance  * 0.25 +
        np.random.normal(0, 7, n)
    ).clip(20, 100).round(1)

    df = pd.DataFrame({
        "Student_ID"  : student_id,
        "Gender"      : gender,
        "Subject"     : subject,
        "Study_Hours" : study_hours,
        "Attendance"  : attendance,
        "Marks"       : marks,
    })

    # Inject ~5 % missing values and ~3 % duplicates for realism
    mask = np.random.choice(df.index, size=int(0.05 * n), replace=False)
    df.loc[mask, "Marks"] = np.nan

    dup_rows = df.sample(int(0.03 * n), random_state=7)
    df = pd.concat([df, dup_rows], ignore_index=True)

    return df


# ──────────────────────────────────────────────────────────────────────
# SECTION 4 ▸ Data Cleaning
# ──────────────────────────────────────────────────────────────────────
def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Clean the raw dataset:
      1. Remove duplicate rows
      2. Fill missing Marks with column median
    Returns cleaned DataFrame + a dict of cleaning stats.
    """
    raw_shape = df.shape
    dup_count = df.duplicated().sum()
    missing_count = df.isnull().sum().sum()

    df = df.drop_duplicates().reset_index(drop=True)
    # Fill numeric nulls with their respective median
    num_cols = df.select_dtypes(include=np.number).columns
    for col in num_cols:
        df[col].fillna(df[col].median(), inplace=True)

    stats = {
        "raw_rows"     : raw_shape[0],
        "clean_rows"   : df.shape[0],
        "dup_removed"  : int(dup_count),
        "missing_filled": int(missing_count),
    }
    return df, stats


# ──────────────────────────────────────────────────────────────────────
# SECTION 5 ▸ Machine Learning — Linear Regression
# ──────────────────────────────────────────────────────────────────────
@st.cache_resource
def train_model(df: pd.DataFrame):
    """
    Train a Linear Regression model to predict Marks
    using Study_Hours and Attendance as features.
    Returns: model, scaler (None; no scaling needed for LR here),
             MAE, R² score.
    """
    X = df[["Study_Hours", "Attendance"]]
    y = df["Marks"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = round(mean_absolute_error(y_test, y_pred), 2)
    r2  = round(r2_score(y_test, y_pred), 3)

    return model, mae, r2


# ──────────────────────────────────────────────────────────────────────
# SECTION 6 ▸ Main App Layout
# ──────────────────────────────────────────────────────────────────────
def main():
    # ── HEADER ────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; padding: 1.2rem 0 0.4rem;'>
        <span style='font-size:2.8rem;'>🎓</span>
        <h1 style='margin:0; font-size:2rem; font-weight:700;
                   background:linear-gradient(90deg,#7c9cff,#a78bfa);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            Student Performance Dashboard
        </h1>
        <p style='color:#9aa0b4; margin-top:4px; font-size:0.9rem;'>
            Analyze · Visualize · Predict
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── SIDEBAR ────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Controls")
        st.divider()

        # ── Custom dataset upload (Bonus) ─────────────────────────────
        st.markdown("### 📂 Upload Dataset")
        uploaded = st.file_uploader(
            "Upload CSV (optional)", type=["csv"],
            help="Must have columns: Student_ID, Gender, Subject, Study_Hours, Attendance, Marks"
        )
        st.divider()

        # Filters — populated after data is loaded
        st.markdown("### 🔍 Filters")
        gender_options  = st.empty()
        subject_options = st.empty()

    # ── DATA LOADING ───────────────────────────────────────────────────
    if uploaded is not None:
        try:
            raw_df = pd.read_csv(uploaded)
            required = {"Student_ID", "Gender", "Subject", "Study_Hours", "Attendance", "Marks"}
            if not required.issubset(set(raw_df.columns)):
                st.error(f"❌ CSV must contain columns: {required}")
                st.stop()
        except Exception as e:
            st.error(f"❌ Error reading CSV: {e}")
            st.stop()
    else:
        raw_df = generate_dataset(200)

    # ── DATA CLEANING ──────────────────────────────────────────────────
    clean_df, clean_stats = clean_data(raw_df.copy())

    # ── SIDEBAR FILTERS ────────────────────────────────────────────────
    with st.sidebar:
        gender_filter = gender_options.multiselect(
            "Select Gender",
            options=sorted(clean_df["Gender"].unique()),
            default=sorted(clean_df["Gender"].unique()),
        )
        subject_filter = subject_options.multiselect(
            "Select Subject",
            options=sorted(clean_df["Subject"].unique()),
            default=sorted(clean_df["Subject"].unique()),
        )

    # Apply filters
    filtered_df = clean_df[
        clean_df["Gender"].isin(gender_filter) &
        clean_df["Subject"].isin(subject_filter)
    ]

    if filtered_df.empty:
        st.warning("⚠️ No data matches the selected filters.")
        st.stop()

    # ── DATA CLEANING REPORT ───────────────────────────────────────────
    with st.expander("🧹 Data Cleaning Report", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Raw Rows",      clean_stats["raw_rows"])
        c2.metric("After Cleaning", clean_stats["clean_rows"])
        c3.metric("Duplicates Removed", clean_stats["dup_removed"])
        c4.metric("Missing Values Filled", clean_stats["missing_filled"])
        st.dataframe(filtered_df.head(10), use_container_width=True, hide_index=True)

    # ── KPI METRICS ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📊 Key Metrics</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("👥 Total Students",    len(filtered_df))
    m2.metric("📈 Avg Marks",         f"{filtered_df['Marks'].mean():.1f}")
    m3.metric("⏰ Avg Study Hours",   f"{filtered_df['Study_Hours'].mean():.1f} hrs")
    m4.metric("🏫 Avg Attendance",    f"{filtered_df['Attendance'].mean():.1f}%")

    st.divider()

    # ──────────────────────────────────────────────────────────────────
    # SECTION 7 ▸ Visualizations
    # ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📉 Visualizations</div>', unsafe_allow_html=True)

    # Row 1: Bar chart + Histogram
    col_left, col_right = st.columns(2)

    # ── 7a. Bar Chart: Average Marks per Subject ─────────────────────
    with col_left:
        st.markdown("**Average Marks per Subject**")
        avg_marks = (
            filtered_df.groupby("Subject")["Marks"]
            .mean().sort_values(ascending=False).reset_index()
        )
        fig, ax = dark_fig(figsize=(7, 4))
        palette  = ["#4f6eff", "#7c9cff", "#a78bfa", "#6ee7b7", "#fbbf24"]
        bars = ax.bar(
            avg_marks["Subject"], avg_marks["Marks"],
            color=palette[:len(avg_marks)], edgecolor="#1a1e2c", linewidth=0.8
        )
        ax.bar_label(bars, fmt="%.1f", padding=3, color="#c8cedf", fontsize=9)
        ax.set_xlabel("Subject", fontsize=9)
        ax.set_ylabel("Avg Marks", fontsize=9)
        ax.set_title("Avg Marks per Subject", fontsize=11, fontweight="bold")
        plt.xticks(rotation=20, ha="right", fontsize=8)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    # ── 7b. Histogram: Marks Distribution ───────────────────────────
    with col_right:
        st.markdown("**Marks Distribution**")
        fig, ax = dark_fig(figsize=(7, 4))
        ax.hist(
            filtered_df["Marks"], bins=20,
            color="#4f6eff", edgecolor="#1a1e2c", linewidth=0.6, alpha=0.9
        )
        ax.axvline(filtered_df["Marks"].mean(), color="#fbbf24", linewidth=1.8,
                   linestyle="--", label=f"Mean: {filtered_df['Marks'].mean():.1f}")
        ax.set_xlabel("Marks", fontsize=9)
        ax.set_ylabel("Number of Students", fontsize=9)
        ax.set_title("Marks Distribution", fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, facecolor="#1a1e2c", labelcolor="#9aa0b4")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    # Row 2: Scatter + Heatmap
    col_l2, col_r2 = st.columns(2)

    # ── 7c. Scatter: Study Hours vs Marks ────────────────────────────
    with col_l2:
        st.markdown("**Study Hours vs Marks**")
        fig, ax = dark_fig(figsize=(7, 4))
        scatter_colors = {"Male": "#4f6eff", "Female": "#a78bfa"}
        for gender, grp in filtered_df.groupby("Gender"):
            ax.scatter(
                grp["Study_Hours"], grp["Marks"],
                color=scatter_colors.get(gender, "#6ee7b7"),
                alpha=0.65, s=40, label=gender, edgecolors="none"
            )
        # Regression line
        x_vals = np.linspace(
            filtered_df["Study_Hours"].min(),
            filtered_df["Study_Hours"].max(), 100
        )
        m, b = np.polyfit(filtered_df["Study_Hours"], filtered_df["Marks"], 1)
        ax.plot(x_vals, m * x_vals + b, color="#fbbf24", linewidth=1.8,
                linestyle="--", label="Trend Line")
        ax.set_xlabel("Study Hours", fontsize=9)
        ax.set_ylabel("Marks", fontsize=9)
        ax.set_title("Study Hours vs Marks", fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, facecolor="#1a1e2c", labelcolor="#9aa0b4")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    # ── 7d. Heatmap: Correlation Matrix ──────────────────────────────
    with col_r2:
        st.markdown("**Correlation Heatmap**")
        num_cols = ["Study_Hours", "Attendance", "Marks"]
        corr_matrix = filtered_df[num_cols].corr()
        fig, ax = dark_fig(figsize=(7, 4))
        sns.heatmap(
            corr_matrix, annot=True, fmt=".2f", ax=ax,
            cmap="coolwarm", linewidths=0.5, linecolor="#1a1e2c",
            cbar_kws={"shrink": 0.8},
            annot_kws={"size": 10, "color": "white"},
        )
        ax.set_title("Correlation Heatmap", fontsize=11, fontweight="bold")
        ax.tick_params(colors="#9aa0b4", labelsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.divider()

    # ──────────────────────────────────────────────────────────────────
    # SECTION 8 ▸ Data Table + Download Button (Bonus)
    # ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📋 Filtered Dataset</div>', unsafe_allow_html=True)
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True, hide_index=True)

    # Download filtered data as CSV
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="filtered_student_data.csv",
        mime="text/csv",
    )

    st.divider()

    # ──────────────────────────────────────────────────────────────────
    # SECTION 9 ▸ Machine Learning Model Info
    # ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🤖 Machine Learning — Linear Regression</div>',
                unsafe_allow_html=True)

    model, mae, r2 = train_model(clean_df)

    ml1, ml2, ml3 = st.columns(3)
    ml1.metric("📐 Model",  "Linear Regression")
    ml2.metric("📉 MAE",   f"{mae} marks")
    ml3.metric("📊 R² Score", f"{r2}")

    st.caption(
        "Model trained on full cleaned dataset (not filtered). "
        "Features: **Study Hours** & **Attendance** → Target: **Marks**"
    )

    st.divider()

    # ──────────────────────────────────────────────────────────────────
    # SECTION 10 ▸ Prediction UI
    # ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🔮 Predict Student Marks</div>',
                unsafe_allow_html=True)

    pred_col, result_col = st.columns([1.2, 1])

    with pred_col:
        st.markdown("Enter the student's details below:")
        study_h = st.slider(
            "📚 Study Hours (per day)", min_value=0.0, max_value=12.0,
            value=5.0, step=0.5,
        )
        attend  = st.slider(
            "🏫 Attendance (%)", min_value=40, max_value=100,
            value=75, step=1,
        )
        predict_btn = st.button("🔮 Predict Marks", use_container_width=True)

    with result_col:
        if predict_btn:
            input_df    = pd.DataFrame([[study_h, attend]],
                                        columns=["Study_Hours", "Attendance"])
            prediction  = model.predict(input_df)[0]
            prediction  = max(0, min(100, round(float(prediction), 1)))

            # Grade label
            if prediction >= 90:
                grade, clr = "A+  🏆", "#22c55e"
            elif prediction >= 75:
                grade, clr = "A   🌟", "#86efac"
            elif prediction >= 60:
                grade, clr = "B   👍", "#fbbf24"
            elif prediction >= 50:
                grade, clr = "C   📘", "#fb923c"
            else:
                grade, clr = "F   ⚠️", "#f87171"

            st.markdown(f"""
            <div class='pred-box'>
                <!-- Grade label FIRST at top -->
                <div style='font-size:0.78rem; letter-spacing:0.08em; text-transform:uppercase;
                            color:#9aa0b4; margin-bottom:4px;'>Grade</div>
                <div style='font-size:2rem; font-weight:800; color:{clr};
                            margin-bottom:10px;'>{grade}</div>
                <hr style='border-color:#2e3347; margin:10px 0;'>
                <!-- Marks value BELOW grade -->
                <div style='color:#9aa0b4; font-size:0.78rem; margin-bottom:4px;'>Predicted Marks</div>
                <div class='pred-value' style='color:{clr};'>{prediction}</div>
                <hr style='border-color:#2e3347; margin:14px 0;'>
                <div style='font-size:0.82rem; color:#9aa0b4;'>
                    📚 Study Hours: <b style='color:#c8cedf'>{study_h}</b> &nbsp;|&nbsp;
                    🏫 Attendance: <b style='color:#c8cedf'>{attend}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='pred-box' style='opacity:0.5;'>
                <div class='pred-value'>——</div>
                <div class='pred-label'>Set inputs and click Predict</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ──────────────────────────────────────────────────────────────────
    # SECTION 11 ▸ Footer
    # ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; color:#555b79; font-size:0.8rem; padding:1rem 0;'>
        🎓 Student Performance Dashboard · Built with Streamlit · Foundations of Data Science
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
