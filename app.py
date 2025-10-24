from flask import Flask, jsonify, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "online", "message": "ConcursoMaster AI"})

@app.route('/api/materias')
def materias():
    return jsonify({
        "materias": [
            "Direito Administrativo", "Direito Constitucional",
            "Português", "Raciocínio Lógico", "Informática"
        ]
    })

@app.route('/api/dashboard-data')
def dashboard():
    return jsonify({
        "total_questoes": 295,
        "questoes_por_materia": {
            "Direito Administrativo": 33,
            "Direito Constitucional": 29,
            "Português": 27,
            "Raciocínio Lógico": 24,
            "Informática": 22
        }
    })

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)
