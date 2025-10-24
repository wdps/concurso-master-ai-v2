from flask import Flask, jsonify, send_from_directory, request
import os
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('concurso.db')
    conn.row_factory = sqlite3.Row
    return conn

# ROTAS EXISTENTES (mantenha as que já tem)
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "online", "message": "ConcursoMaster AI"})

@app.route('/api/materias')
def materias():
    conn = get_db_connection()
    materias = conn.execute('SELECT DISTINCT disciplina FROM questões').fetchall()
    conn.close()
    materias_lista = [row['disciplina'] for row in materias]
    return jsonify({"materias": materias_lista})

@app.route('/api/dashboard-data')
def dashboard():
    conn = get_db_connection()
    
    # Total de questões
    total = conn.execute('SELECT COUNT(*) as count FROM questões').fetchone()['count']
    
    # Por matéria
    materias_count = conn.execute('''
        SELECT disciplina, COUNT(*) as count 
        FROM questões 
        GROUP BY disciplina
    ''').fetchall()
    
    conn.close()
    
    questoes_por_materia = {row['disciplina']: row['count'] for row in materias_count}
    
    return jsonify({
        "total_questoes": total,
        "questoes_por_materia": questoes_por_materia
    })

# 🎯 NOVA ROTA - QUESTÕES REAIS DO BANCO
@app.route('/api/questoes/<materia>')
def get_questoes(materia):
    conn = get_db_connection()
    
    # Buscar questões da matéria específica
    limit = request.args.get('limit', 10, type=int)
    
    questões = conn.execute('''
        SELECT id, disciplina, enunciado, alt_a, alt_b, alt_c, alt_d, gabarito
        FROM questões 
        WHERE disciplina = ? 
        LIMIT ?
    ''', (materia, limit)).fetchall()
    
    conn.close()
    
    questões_lista = []
    for row in questões:
        questões_lista.append({
            'id': row['id'],
            'materia': row['disciplina'],
            'enunciado': row['enunciado'],
            'alternativa_a': row['alt_a'],
            'alternativa_b': row['alt_b'],
            'alternativa_c': row['alt_c'],
            'alternativa_d': row['alt_d'],
            'resposta_correta': row['gabarito']
        })
    
    return jsonify({
        "disciplina": materia,
        "quantidade": len(questões_lista),
        "questoes": questões_lista
    })

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
