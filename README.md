# LiverGuard IoT — Sensor-Based Liver Risk Prediction

ML model + IoT-ready prediction API that screens for liver disease using
biochemical parameters that can all be acquired with biosensor modules.
Trained on the **Indian Liver Patient Dataset (ILPD)** from Kaggle and packaged
as a real-time REST API + web dashboard for IoT device integration.

## Dataset (real, from Kaggle)
- **Indian Liver Patient Records (ILPD)** — Kaggle: `uciml/indian-liver-patient-records`
  (UCI ML Repository #225, Ramana & Venkateswarlu, 2012)
- 583 patient records · 416 liver patients / 167 healthy · 10 features + label

## Model
| Stage | Detail |
|---|---|
| Preprocessing | Missing-value repair (A/G ratio recomputed), gender encoding, 3 engineered ratios (bilirubin ratio, AST/ALT ratio, globulin) |
| Compared | Logistic Regression, Random Forest, Gradient Boosting, XGBoost, SVM, KNN (5-fold stratified CV) |
| Deployed | **Soft-voting ensemble** (XGBoost + Gradient Boosting + RF + SVM) |
| Test accuracy | **73.3 %** |
| ROC-AUC | **0.81** |
| Recall | **91.3 %** ← catches almost every true patient (screening requirement) |
| F1 | 82.9 % |

Comparable published results on ILPD are 71–78 %, so this is a strong result.

## Repository Structure
```
├── data/ilpd.csv                 # real Kaggle dataset (583 records)
├── train.py                      # training pipeline (re-runnable)
├── model/liver_model.pkl         # deployed ensemble model (joblib)
├── model/training_report.json    # full metrics for the report
├── app.py                        # Flask dashboard + IoT JSON API
├── build_ppt.py                  # generates the mid-review presentation
├── Liver_IoT_Mid_Review_PPT.pptx # mid-review slides (14 slides)
├── requirements.txt
└── README.md
```

## Run
```bash
pip install -r requirements.txt
python3 app.py        # dashboard on http://localhost:8000
```

## IoT Integration (final-review architecture)
```
[Biosensors] -> [ADC / signal conditioning] -> [ESP32 MCU]
      -> WiFi -> POST /api/predict -> [this ML server]
      -> risk_level JSON -> LED / buzzer / OLED / cloud dashboard
```

### Sensor mapping
| Parameter | Sensor technology |
|---|---|
| Total / Direct Bilirubin | Optical transcutaneous sensor (450–460 nm LED + photodiode) |
| ALT / AST | Electrochemical enzyme biosensors |
| Alkaline Phosphatase | Amperometric enzyme sensor |
| Total Proteins | Bio-impedance spectroscopy |
| Albumin | Potentiometric immuno-sensor |
| A/G ratio | Computed on MCU firmware |

### API example (what the ESP32 sends)
```json
POST /api/predict
{"age":52,"gender":"male","total_bilirubin":3.9,"direct_bilirubin":2.0,
 "alkaline_phosphotase":195,"alt":27,"ast":59,"total_proteins":7.3,
 "albumin":2.4,"ag_ratio":0.49}

→ {"risk_probability":88.4,"prediction":1,"risk_level":"HIGH"}
```

*Academic screening prototype — not a medical device.*
