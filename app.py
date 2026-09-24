"""
LiverGuard IoT - Prediction Dashboard + IoT API
================================================
Run:  python3 app.py          (serves on 0.0.0.0:8000)

Endpoints
---------
GET  /              -> dashboard UI (enter sensor readings, get risk)
POST /api/predict   -> JSON API for IoT devices (ESP32 / Node-RED / MQTT bridge)
GET  /api/health    -> liveness probe

Example IoT payload (ESP32 HTTPClient POST):
{
  "age": 52, "gender": "male",
  "total_bilirubin": 3.9, "direct_bilirubin": 2.0,
  "alkaline_phosphotase": 195, "alt": 27, "ast": 59,
  "total_proteins": 7.3, "albumin": 2.4, "ag_ratio": 0.49
}
"""

import joblib
import numpy as np
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

BUNDLE = joblib.load("model/liver_model.pkl")
MODEL = BUNDLE["model"]
FEATURES = BUNDLE["feature_columns"]

# Normal clinical ranges used to flag abnormal sensor readings in the UI
NORMAL_RANGES = {
    "Total_Bilirubin":            (0.1, 1.2,  "mg/dL"),
    "Direct_Bilirubin":           (0.0, 0.3,  "mg/dL"),
    "Alkaline_Phosphotase":       (44, 147,   "U/L"),
    "Alamine_Aminotransferase":   (7, 56,     "U/L"),
    "Aspartate_Aminotransferase": (10, 40,    "U/L"),
    "Total_Protiens":             (6.0, 8.3,  "g/dL"),
    "Albumin":                    (3.5, 5.5,  "g/dL"),
    "Albumin_and_Globulin_Ratio": (1.1, 2.5,  "ratio"),
}

SENSOR_MAP = [
    ("Total / Direct Bilirubin", "Optical transcutaneous sensor (450-460 nm LED + photodiode), "
     "same principle as a jaundice meter / pulse-oximeter", "Non-invasive"),
    ("ALT / AST (SGPT / SGOT)", "Electrochemical enzyme biosensor (screen-printed electrode + enzyme layer)", "Micro-fluidic / finger-prick"),
    ("Alkaline Phosphatase", "Amperometric enzyme sensor with pNPP substrate", "Micro-fluidic"),
    ("Total Proteins", "Bio-impedance spectroscopy electrodes", "Wearable patch"),
    ("Albumin", "Potentiometric immuno-sensor / ion-selective electrode", "Micro-fluidic"),
    ("A/G Ratio", "Computed on MCU: Albumin / (Total Protein - Albumin)", "Firmware"),
    ("Age / Gender", "Stored patient profile on device (EEPROM / app)", "User profile"),
]


def build_feature_vector(p):
    """Map raw sensor JSON to the model's 13-feature vector (same order as training)."""
    age = float(p["age"])
    gender_male = 1 if str(p.get("gender", "male")).strip().lower() in ("male", "m", "1") else 0
    tb = float(p["total_bilirubin"]); db = float(p["direct_bilirubin"])
    alp = float(p["alkaline_phosphotase"])
    alt = float(p["alt"]); ast = float(p["ast"])
    tp = float(p["total_proteins"]); alb = float(p["albumin"])

    if p.get("ag_ratio") not in (None, ""):
        ag = float(p["ag_ratio"])
    else:
        glob = tp - alb
        ag = alb / glob if glob > 0 else 0.0

    bilirubin_ratio = db / tb if tb > 0 else 0.0
    ast_alt_ratio = ast / alt if alt > 0 else 1.0
    protein_albumin_diff = tp - alb

    values = {
        "Age": age, "Gender_Male": gender_male,
        "Total_Bilirubin": tb, "Direct_Bilirubin": db,
        "Alkaline_Phosphotase": alp, "Alamine_Aminotransferase": alt,
        "Aspartate_Aminotransferase": ast, "Total_Protiens": tp,
        "Albumin": alb, "Albumin_and_Globulin_Ratio": ag,
        "Bilirubin_Ratio": bilirubin_ratio, "AST_ALT_Ratio": ast_alt_ratio,
        "Protein_Albumin_Diff": protein_albumin_diff,
    }
    return np.array([[values[f] for f in FEATURES]])


def predict_dict(payload):
    X = build_feature_vector(payload)
    proba = float(MODEL.predict_proba(X)[0][1])
    label = int(proba >= 0.5)
    if proba >= 0.75:
        risk = "HIGH"
    elif proba >= 0.45:
        risk = "MODERATE"
    else:
        risk = "LOW"
    return {
        "risk_probability": round(proba * 100, 1),
        "prediction": label,
        "prediction_text": "Liver disease indicated" if label else "No liver disease indicated",
        "risk_level": risk,
    }


@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        payload = request.get_json(force=True)
        return jsonify(predict_dict(payload))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "model": "liver-risk-ensemble-v1"})


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    alerts = []
    form = {
        "age": 52, "gender": "male", "total_bilirubin": 3.9, "direct_bilirubin": 2.0,
        "alkaline_phosphotase": 195, "alt": 27, "ast": 59,
        "total_proteins": 7.3, "albumin": 2.4, "ag_ratio": 0.49,
    }
    if request.method == "POST":
        form = {k: request.form.get(k, "") for k in form}
        try:
            result = predict_dict(form)
            checks = {
                "Total_Bilirubin": form["total_bilirubin"],
                "Direct_Bilirubin": form["direct_bilirubin"],
                "Alkaline_Phosphotase": form["alkaline_phosphotase"],
                "Alamine_Aminotransferase": form["alt"],
                "Aspartate_Aminotransferase": form["ast"],
                "Total_Protiens": form["total_proteins"],
                "Albumin": form["albumin"],
                "Albumin_and_Globulin_Ratio": form["ag_ratio"],
            }
            pretty = {
                "Total_Bilirubin": "Total Bilirubin", "Direct_Bilirubin": "Direct Bilirubin",
                "Alkaline_Phosphotase": "Alkaline Phosphatase (ALP)",
                "Alamine_Aminotransferase": "ALT / SGPT",
                "Aspartate_Aminotransferase": "AST / SGOT",
                "Total_Protiens": "Total Proteins", "Albumin": "Albumin",
                "Albumin_and_Globulin_Ratio": "A/G Ratio",
            }
            for k, v in checks.items():
                lo, hi, unit = NORMAL_RANGES[k]
                fv = float(v)
                if fv < lo:
                    alerts.append((pretty[k], f"LOW ({fv} {unit}, normal {lo}-{hi} {unit})"))
                elif fv > hi:
                    alerts.append((pretty[k], f"HIGH ({fv} {unit}, normal {lo}-{hi} {unit})"))
        except Exception as e:
            result = {"error": f"Invalid input: {e}"}

    return render_template_string(PAGE, result=result, alerts=alerts, form=form,
                                  sensor_map=SENSOR_MAP)


PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>LiverGuard IoT - Liver Risk Prediction</title>
<style>
  :root{--bg:#0b1220;--card:#121c31;--card2:#182441;--accent:#2dd4bf;--accent2:#38bdf8;
        --danger:#f87171;--warn:#fbbf24;--ok:#34d399;--text:#e2e8f0;--muted:#94a3b8;}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(160deg,#0b1220,#0f1b33 60%,#0b1220);
       color:var(--text);min-height:100vh;padding-bottom:60px}
  .wrap{max-width:1100px;margin:0 auto;padding:0 20px}
  header{padding:34px 0 10px;text-align:center}
  .logo{font-size:2.1rem;font-weight:800;letter-spacing:.5px}
  .logo span{color:var(--accent)}
  .tag{color:var(--muted);margin-top:6px;font-size:.95rem}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:26px}
  @media(max-width:900px){.grid{grid-template-columns:1fr}}
  .card{background:var(--card);border:1px solid #22304f;border-radius:16px;padding:26px}
  h2{font-size:1.05rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--accent2);margin-bottom:18px}
  label{display:block;font-size:.8rem;color:var(--muted);margin:10px 0 4px}
  input,select{width:100%;padding:10px 12px;border-radius:9px;border:1px solid #2b3b60;background:var(--card2);
               color:var(--text);font-size:.95rem}
  input:focus,select:focus{outline:none;border-color:var(--accent)}
  .row2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  button{margin-top:22px;width:100%;padding:14px;border:none;border-radius:10px;font-size:1rem;font-weight:700;
         background:linear-gradient(90deg,var(--accent),var(--accent2));color:#04121f;cursor:pointer}
  button:hover{filter:brightness(1.1)}
  .res{ text-align:center }
  .gauge{position:relative;height:26px;border-radius:13px;background:linear-gradient(90deg,#34d399,#fbbf24 50%,#f87171);margin:26px 0 8px}
  .needle{position:absolute;top:-7px;width:5px;height:40px;background:#fff;border-radius:3px;transition:left .6s}
  .pct{font-size:3rem;font-weight:800}
  .pill{display:inline-block;padding:8px 22px;border-radius:99px;font-weight:800;letter-spacing:1px;margin-top:8px}
  .HIGH{background:#3b1520;color:var(--danger);border:1px solid var(--danger)}
  .MODERATE{background:#3a2c10;color:var(--warn);border:1px solid var(--warn)}
  .LOW{background:#0f2e22;color:var(--ok);border:1px solid var(--ok)}
  .alertbox{margin-top:18px;text-align:left}
  .alert{background:#2a1a1d;border-left:4px solid var(--danger);padding:9px 12px;border-radius:6px;margin:7px 0;font-size:.87rem}
  .verdict{margin-top:14px;color:var(--muted);font-size:.92rem}
  table{width:100%;border-collapse:collapse;font-size:.86rem}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid #22304f}
  th{color:var(--accent2);font-size:.75rem;text-transform:uppercase;letter-spacing:1px}
  .full{grid-column:1/-1}
  code{background:#0a1122;border:1px solid #22304f;padding:2px 7px;border-radius:6px;color:var(--accent);font-size:.83rem}
  pre{background:#0a1122;border:1px solid #22304f;border-radius:10px;padding:14px;overflow-x:auto;
      font-size:.8rem;color:#a5f3fc;line-height:1.5}
  .stats{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:16px}
  .stat{flex:1;min-width:120px;background:var(--card2);border-radius:12px;padding:14px;text-align:center}
  .stat b{font-size:1.35rem;color:var(--accent)}
  .stat small{color:var(--muted);display:block;margin-top:4px}
  footer{text-align:center;color:#586a8c;font-size:.8rem;margin-top:40px}
</style>
</head>
<body>
<header class="wrap">
  <div class="logo">&#129657; Liver<span>Guard</span> IoT</div>
  <div class="tag">Sensor-based Liver Disease Risk Screening &nbsp;&bull;&nbsp; Ensemble ML Model &nbsp;&bull;&nbsp; Kaggle ILPD Dataset (583 records)</div>
</header>

<div class="wrap grid">

  <div class="card">
    <h2>Biosensor Readings Input</h2>
    <form method="post">
      <div class="row2">
        <div><label>Age (years)</label><input name="age" value="{{ form.age }}" required></div>
        <div><label>Gender</label>
          <select name="gender">
            <option value="male" {% if form.gender=='male' %}selected{% endif %}>Male</option>
            <option value="female" {% if form.gender=='female' %}selected{% endif %}>Female</option>
          </select></div>
      </div>
      <div class="row2">
        <div><label>Total Bilirubin (mg/dL) &mdash; optical sensor</label>
             <input step="any" name="total_bilirubin" value="{{ form.total_bilirubin }}" required></div>
        <div><label>Direct Bilirubin (mg/dL) &mdash; optical sensor</label>
             <input step="any" name="direct_bilirubin" value="{{ form.direct_bilirubin }}" required></div>
      </div>
      <div class="row2">
        <div><label>ALT / SGPT (U/L) &mdash; enzyme biosensor</label>
             <input step="any" name="alt" value="{{ form.alt }}" required></div>
        <div><label>AST / SGOT (U/L) &mdash; enzyme biosensor</label>
             <input step="any" name="ast" value="{{ form.ast }}" required></div>
      </div>
      <div class="row2">
        <div><label>Alkaline Phosphatase (U/L) &mdash; enzyme biosensor</label>
             <input step="any" name="alkaline_phosphotase" value="{{ form.alkaline_phosphotase }}" required></div>
        <div><label>Total Proteins (g/dL) &mdash; bio-impedance</label>
             <input step="any" name="total_proteins" value="{{ form.total_proteins }}" required></div>
      </div>
      <div class="row2">
        <div><label>Albumin (g/dL) &mdash; immuno-sensor</label>
             <input step="any" name="albumin" value="{{ form.albumin }}" required></div>
        <div><label>A/G Ratio &mdash; computed on MCU</label>
             <input step="any" name="ag_ratio" value="{{ form.ag_ratio }}" required></div>
      </div>
      <button type="submit">Analyze Liver Risk</button>
    </form>
  </div>

  <div class="card res">
    <h2>Risk Analysis</h2>
    {% if result and result.error %}
      <div class="alert">{{ result.error }}</div>
    {% elif result %}
      <div class="pct" style="color:{% if result.risk_level=='HIGH' %}var(--danger){% elif result.risk_level=='MODERATE' %}var(--warn){% else %}var(--ok){% endif %}">
        {{ result.risk_probability }}%</div>
      <div class="gauge"><div class="needle" style="left:{{ result.risk_probability }}%"></div></div>
      <div class="pill {{ result.risk_level }}">{{ result.risk_level }} RISK</div>
      <div class="verdict">{{ result.prediction_text }}.<br>
      Screening recommendation:
      {% if result.risk_level == 'HIGH' %}immediate clinical consultation advised.{% elif result.risk_level == 'MODERATE' %}consult a physician and re-test in 2 weeks.{% else %}no action needed, re-screen annually.{% endif %}
      </div>
      {% if alerts %}
      <div class="alertbox">
        <b style="font-size:.85rem;color:var(--muted)">OUT-OF-RANGE SENSOR VALUES</b>
        {% for name, msg in alerts %}<div class="alert"><b>{{ name }}:</b> {{ msg }}</div>{% endfor %}
      </div>
      {% endif %}
    {% else %}
      <p style="color:var(--muted);margin-top:30px">Enter biosensor readings and press <b>Analyze Liver Risk</b>.<br><br>
      The model returns a probability of liver disease from 10 biochemical parameters -
      all measurable with the IoT sensor modules listed below.</p>
    {% endif %}
  </div>

  <div class="card full">
    <h2>Model Performance (held-out test set)</h2>
    <div class="stats">
      <div class="stat"><b>73.3%</b><small>Accuracy</small></div>
      <div class="stat"><b>0.81</b><small>ROC-AUC</small></div>
      <div class="stat"><b>91.3%</b><small>Recall (sensitivity)</small></div>
      <div class="stat"><b>82.9%</b><small>F1 Score</small></div>
      <div class="stat"><b>583</b><small>Patient records</small></div>
    </div>
    <p style="color:var(--muted);font-size:.88rem">Soft-voting ensemble of XGBoost + Gradient Boosting + Random Forest + SVM, trained on the
    <b>Indian Liver Patient Dataset (Kaggle: uciml/indian-liver-patient-records)</b>. High recall (91%) means the device catches
    almost every true patient - the key requirement for a screening tool. Comparable published results on ILPD are 71-78%.</p>
  </div>

  <div class="card full">
    <h2>IoT Sensor Integration Map (for final review)</h2>
    <table>
      <tr><th>Parameter</th><th>Sensor Technology</th><th>Form Factor</th></tr>
      {% for param, tech, formf in sensor_map %}
      <tr><td><b>{{ param }}</b></td><td>{{ tech }}</td><td>{{ formf }}</td></tr>
      {% endfor %}
    </table>
  </div>

  <div class="card full">
    <h2>Device Integration API</h2>
    <p style="color:var(--muted);font-size:.88rem;margin-bottom:12px">
      Your microcontroller (ESP32 / Raspberry Pi Pico W) collects sensor readings and POSTs them to this server:</p>
    <pre>POST /api/predict
Content-Type: application/json

{
  "age": 52, "gender": "male",
  "total_bilirubin": 3.9, "direct_bilirubin": 2.0,
  "alkaline_phosphotase": 195, "alt": 27, "ast": 59,
  "total_proteins": 7.3, "albumin": 2.4, "ag_ratio": 0.49
}

Response:
{
  "risk_probability": 88.4,
  "prediction": 1,
  "prediction_text": "Liver disease indicated",
  "risk_level": "HIGH"
}</pre>
    <p style="color:var(--muted);font-size:.85rem;margin-top:10px">
      ESP32 Arduino sketch: use <code>HTTPClient</code> + <code>WiFiClientSecure</code> to POST the JSON above,
      then drive an LED/buzzer or OLED display from the <code>risk_level</code> field.</p>
  </div>
</div>

<footer class="wrap">LiverGuard IoT &mdash; academic screening prototype. Not a medical device; clinical diagnosis must be confirmed by a physician.</footer>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
