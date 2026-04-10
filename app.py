from flask import Flask, jsonify, request, send_from_directory
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import json
import os
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__, static_folder='static', static_url_path='')

# ─────────────────────────────────────────────
# Generate synthetic dataset on startup
# ─────────────────────────────────────────────
np.random.seed(42)
N = 300

def generate_dataset():
    study_hours   = np.random.normal(5, 2, N).clip(0, 12)
    attendance    = np.random.normal(75, 15, N).clip(40, 100)
    prev_score    = np.random.normal(65, 15, N).clip(20, 100)
    sleep_hours   = np.random.normal(7, 1.5, N).clip(3, 10)
    assignments   = np.random.randint(0, 11, N)
    extracurricular = np.random.choice([0, 1], N, p=[0.4, 0.6])
    gender        = np.random.choice(['Male', 'Female'], N)
    department    = np.random.choice(['CS', 'Math', 'Physics', 'Commerce', 'Biology'], N)
    age           = np.random.randint(17, 23, N)

    # Score with correlations + noise
    score = (
        study_hours * 4.5 +
        attendance * 0.3 +
        prev_score * 0.4 +
        sleep_hours * 1.5 +
        assignments * 1.2 +
        extracurricular * 3 +
        np.random.normal(0, 8, N)
    ).clip(20, 100)

    pass_fail = (score >= 50).astype(int)

    df = pd.DataFrame({
        'student_id':       [f'STU{str(i+1).zfill(4)}' for i in range(N)],
        'age':              age,
        'gender':           gender,
        'department':       department,
        'study_hours':      study_hours.round(1),
        'attendance':       attendance.round(1),
        'prev_score':       prev_score.round(1),
        'sleep_hours':      sleep_hours.round(1),
        'assignments':      assignments,
        'extracurricular':  extracurricular,
        'final_score':      score.round(1),
        'pass_fail':        pass_fail
    })
    return df

df = generate_dataset()

# ─────────────────────────────────────────────
# Train ML model once at startup
# ─────────────────────────────────────────────
FEATURES = ['study_hours', 'attendance', 'prev_score',
            'sleep_hours', 'assignments', 'extracurricular']

X = df[FEATURES]
y = df['pass_fail']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train_s, y_train)
y_pred = rf_model.predict(X_test_s)
model_accuracy = accuracy_score(y_test, y_pred)
feature_importances = dict(zip(FEATURES, rf_model.feature_importances_.round(4)))
cm = confusion_matrix(y_test, y_pred).tolist()

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/stats')
def stats():
    data = {
        'total_students':  int(len(df)),
        'pass_rate':       round(df['pass_fail'].mean() * 100, 1),
        'avg_score':       round(df['final_score'].mean(), 1),
        'avg_study_hours': round(df['study_hours'].mean(), 1),
        'avg_attendance':  round(df['attendance'].mean(), 1),
        'dept_counts':     df['department'].value_counts().to_dict(),
        'gender_counts':   df['gender'].value_counts().to_dict(),
        'pass_by_dept':    df.groupby('department')['pass_fail'].mean().mul(100).round(1).to_dict(),
        'avg_score_by_dept': df.groupby('department')['final_score'].mean().round(1).to_dict(),
    }
    return jsonify(data)

@app.route('/api/data')
def get_data():
    page  = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    dept  = request.args.get('dept', '')
    gender = request.args.get('gender', '')
    result = df.copy()
    if dept:
        result = result[result['department'] == dept]
    if gender:
        result = result[result['gender'] == gender]
    total = len(result)
    start = (page - 1) * limit
    end   = start + limit
    rows  = result.iloc[start:end].to_dict(orient='records')
    return jsonify({'total': total, 'rows': rows})

@app.route('/api/scatter')
def scatter():
    x_col = request.args.get('x', 'study_hours')
    y_col = request.args.get('y', 'final_score')
    sample = df[[x_col, y_col, 'pass_fail', 'department']].copy()
    return jsonify(sample.to_dict(orient='records'))

@app.route('/api/histogram')
def histogram():
    col = request.args.get('col', 'final_score')
    data = df[col].tolist()
    return jsonify({'data': data, 'column': col})

@app.route('/api/correlation')
def correlation():
    num_cols = ['study_hours', 'attendance', 'prev_score',
                'sleep_hours', 'assignments', 'final_score']
    corr = df[num_cols].corr().round(3)
    return jsonify({
        'columns': num_cols,
        'matrix': corr.values.tolist()
    })

@app.route('/api/model')
def model_info():
    return jsonify({
        'accuracy':            round(model_accuracy * 100, 1),
        'feature_importances': feature_importances,
        'confusion_matrix':    cm,
        'samples_train':       len(X_train),
        'samples_test':        len(X_test),
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    body = request.json
    try:
        row = [[
            float(body['study_hours']),
            float(body['attendance']),
            float(body['prev_score']),
            float(body['sleep_hours']),
            int(body['assignments']),
            int(body['extracurricular'])
        ]]
        row_s = scaler.transform(row)
        pred  = int(rf_model.predict(row_s)[0])
        prob  = rf_model.predict_proba(row_s)[0].tolist()
        return jsonify({
            'prediction': 'Pass' if pred == 1 else 'Fail',
            'probability_pass': round(prob[1] * 100, 1),
            'probability_fail': round(prob[0] * 100, 1),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/insights')
def insights():
    top_dept  = df.groupby('department')['final_score'].mean().idxmax()
    best_corr = df[['study_hours','attendance','prev_score','sleep_hours','assignments','final_score']]\
                  .corr()['final_score'].drop('final_score').idxmax()
    ec_pass   = df.groupby('extracurricular')['pass_fail'].mean().mul(100).round(1).to_dict()
    gender_avg= df.groupby('gender')['final_score'].mean().round(1).to_dict()
    return jsonify({
        'top_department':         top_dept,
        'strongest_predictor':    best_corr.replace('_', ' ').title(),
        'extracurricular_effect': ec_pass,
        'gender_avg_score':       gender_avg,
        'high_achievers':         int((df['final_score'] >= 80).sum()),
        'at_risk':                int((df['final_score'] < 45).sum()),
    })

if __name__ == '__main__':
    print("Data Science Dashboard running at http://127.0.0.1:5000")
    app.run(debug=True)
