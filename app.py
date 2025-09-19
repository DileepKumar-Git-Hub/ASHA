from flask import Flask, render_template, request, jsonify
import os, json, requests
from datetime import datetime

app = Flask(__name__)

DATA_DIR = 'data'
EHR_FILE = os.path.join(DATA_DIR, 'ehr_records.json')
SURVEY_FILE = os.path.join(DATA_DIR, 'survey_data.json')
VACCINE_FILE = os.path.join(DATA_DIR, 'vaccination_schedule.json')

os.makedirs(DATA_DIR, exist_ok=True)

# ---------- Helpers ----------
def init_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f, indent=2)

def read_file(file_path):
    init_file(file_path)
    with open(file_path, 'r') as f:
        return json.load(f)

def write_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def append_to_file(file_path, data):
    records = read_file(file_path)
    records.append(data)
    write_file(file_path, records)

# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

# EHR Routes
@app.route('/save_ehr', methods=['POST'])
def save_ehr():
    data = request.json
    # Ensure date field exists
    if 'date' not in data:
        data['date'] = datetime.now().strftime("%Y-%m-%d")
    # Load existing patient or create
    records = read_file(EHR_FILE)
    patient = next((p for p in records if p['abha_number']==data['abha_number']), None)
    if patient:
        # Add disease entry
        if 'diseases' not in patient:
            patient['diseases'] = []
        patient['diseases'].append({
            'problem_name': data.get('problem_name'),
            'problem_description': data.get('problem_description'),
            'vitals_bp': data.get('vitals_bp',''),
            'vitals_temp': data.get('vitals_temp',''),
            'date': data['date']
        })
    else:
        # Create new patient entry
        patient = {
            'abha_number': data['abha_number'],
            'name': data.get('name','Unknown'),
            'gender': data.get('gender','Unknown'),
            'diseases':[{
                'problem_name': data.get('problem_name'),
                'problem_description': data.get('problem_description'),
                'vitals_bp': data.get('vitals_bp',''),
                'vitals_temp': data.get('vitals_temp',''),
                'date': data['date']
            }]
        }
        records.append(patient)
    write_file(EHR_FILE, records)
    return jsonify({'status':'EHR saved successfully'})

@app.route('/load_ehr')
def load_ehr():
    return jsonify(read_file(EHR_FILE))

# Survey Routes
@app.route('/save_survey', methods=['POST'])
def save_survey():
    data = request.json
    if 'date' not in data:
        data['date'] = datetime.now().strftime("%Y-%m-%d")
    append_to_file(SURVEY_FILE, data)
    return jsonify({'status':'Survey saved successfully'})

@app.route('/load_survey')
def load_survey():
    return jsonify(read_file(SURVEY_FILE))

# Vaccination Reminders
@app.route('/vaccination_reminders')
def vaccination_reminders():
    reminders = read_file(VACCINE_FILE)
    return jsonify(reminders)

# ABHA Sync simulation
@app.route('/sync_ayushman')
def sync_ayushman():
    try:
        response = requests.get('https://api.ayushmanbharat.gov.in/data', timeout=5)
        return jsonify(response.json())
    except:
        return jsonify({'error':'Unable to connect. Offline mode'})

# Clear all data (testing)
@app.route('/clear_all')
def clear_all():
    for f in [EHR_FILE,SURVEY_FILE,VACCINE_FILE]:
        write_file(f,[])
    return jsonify({'status':'All local data cleared'})

if __name__=="__main__":
    app.run(debug=True)
