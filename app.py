from flask import Flask, jsonify, send_from_directory, request
import os
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('concurso.db')
    conn.row_factory = sqlite3.Row
    
    # ✅ VERIFICAR E CRIAR TABELA SE NÃO EXISTIR
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questões (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina TEXT NOT NULL,
            enunciado TEXT NOT NULL,
            alt_a TEXT NOT NULL,
            alt_b TEXT NOT NULL,
            alt_c TEXT NOT NULL,
            alt_d TEXT NOT NULL,
            gabarito TEXT NOT NULL
        )
    ''')
    conn.commit()
    
    return conn

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "online", "message": "ConcursoMaster AI"})

@app.route('/api/materias')
def materias():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se há questões
    cursor.execute("SELECT COUNT(*) as total FROM questões")
    total_questoes = cursor.fetchone()['total']
    
    if total_questoes == 0:
        # Se não há questões, retornar lista vazia
        materias = []
    else:
        cursor.execute("SELECT DISTINCT disciplina FROM questões ORDER BY disciplina")
        materias = [row['disciplina'] for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({"materias": materias})

@app.route('/api/dashboard-data')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de questões
    cursor.execute("SELECT COUNT(*) as total FROM questões")
    total = cursor.fetchone()['total']
    
    if total == 0:
        # Se não há questões, retornar dados vazios
        questoes_por_materia = {}
    else:
        # Questões por matéria
        cursor.execute('''
            SELECT disciplina, COUNT(*) as quantidade 
            FROM questões 
            GROUP BY disciplina 
            ORDER BY quantidade DESC
        ''')
        materias_data = cursor.fetchall()
        questoes_por_materia = {row['disciplina']: row['quantidade'] for row in materias_data}
    
    conn.close()
    
    return jsonify({
        "total_questoes": total,
        "questoes_por_materia": questoes_por_materia
    })

@app.route('/api/questoes/<materia>')
def get_questoes(materia):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    limit = request.args.get('limit', 10, type=int)
    
    cursor.execute('''
        SELECT id, disciplina, enunciado, alt_a, alt_b, alt_c, alt_d, gabarito
        FROM questões 
        WHERE disciplina = ? 
        LIMIT ?
    ''', (materia, limit))
    
    questoes_data = cursor.fetchall()
    
    questoes = []
    for row in questoes_data:
        questoes.append({
            'id': row['id'],
            'materia': row['disciplina'],
            'enunciado': row['enunciado'],
            'alternativa_a': row['alt_a'],
            'alternativa_b': row['alt_b'],
            'alternativa_c': row['alt_c'],
            'alternativa_d': row['alt_d'],
            'resposta_correta': row['gabarito']
        })
    
    conn.close()
    
    return jsonify({
        "disciplina": materia,
        "quantidade": len(questoes),
        "questoes": questoes
    })

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
