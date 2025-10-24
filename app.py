from flask import Flask, jsonify, send_from_directory, request
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

app = Flask(__name__)

# ✅ ESTRUTURAS SIMPLIFICADAS SEM PANDAS
class QuestaoWeb:
    def __init__(self, id, enunciado, materia, alt_a, alt_b, alt_c, alt_d, gabarito, dificuldade="Médio", justificativa=None):
        self.id = id
        self.enunciado = enunciado
        self.materia = materia
        self.alternativa_a = alt_a
        self.alternativa_b = alt_b
        self.alternativa_c = alt_c
        self.alternativa_d = alt_d
        self.resposta_correta = gabarito
        self.dificuldade = dificuldade
        self.justificativa = justificativa
    
    def to_dict(self):
        return self.__dict__

# ✅ API ROBUSTA E FUNCIONAL
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api/health')
def health():
    return jsonify({
        "status": "online", 
        "message": "ConcursoMaster AI Professional",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/materias')
def materias():
    """API melhorada com tratamento de erros"""
    try:
        conn = sqlite3.connect('concurso.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT disciplina FROM questões ORDER BY disciplina")
        materias = [row['disciplina'] for row in cursor.fetchall()]
        
        # Estatísticas por matéria
        estatisticas = {}
        for materia in materias:
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN dificuldade = 'Fácil' THEN 1 ELSE 0 END) as faceis,
                       SUM(CASE WHEN dificuldade = 'Médio' THEN 1 ELSE 0 END) as medias,
                       SUM(CASE WHEN dificuldade = 'Difícil' THEN 1 ELSE 0 END) as dificeis
                FROM questões WHERE disciplina = ?
            ''', (materia,))
            stats = cursor.fetchone()
            estatisticas[materia] = {
                'total': stats['total'],
                'faceis': stats['faceis'] or 0,
                'medias': stats['medias'] or 0,
                'dificeis': stats['dificeis'] or 0
            }
        
        conn.close()
        
        return jsonify({
            "materias": materias,
            "estatisticas": estatisticas,
            "total_geral": sum(stats['total'] for stats in estatisticas.values())
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard-data')
def dashboard():
    """Dashboard profissional com métricas avançadas"""
    try:
        conn = sqlite3.connect('concurso.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Total de questões
        cursor.execute("SELECT COUNT(*) as total FROM questões")
        total = cursor.fetchone()['total']
        
        # Distribuição por matéria
        cursor.execute('''
            SELECT disciplina, COUNT(*) as quantidade
            FROM questões 
            GROUP BY disciplina 
            ORDER BY quantidade DESC
        ''')
        
        distribuicao = cursor.fetchall()
        questoes_por_materia = {}
        for row in distribuicao:
            percentual = round((row['quantidade'] * 100.0 / total), 2) if total > 0 else 0
            questoes_por_materia[row['disciplina']] = {
                'quantidade': row['quantidade'],
                'percentual': percentual
            }
        
        # Dificuldade geral
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN dificuldade = 'Fácil' THEN 1 ELSE 0 END) as faceis,
                SUM(CASE WHEN dificuldade = 'Médio' THEN 1 ELSE 0 END) as medias,
                SUM(CASE WHEN dificuldade = 'Difícil' THEN 1 ELSE 0 END) as dificeis
            FROM questões
        ''')
        dificuldade_stats = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            "total_questoes": total,
            "questoes_por_materia": questoes_por_materia,
            "dificuldade": {
                "faceis": dificuldade_stats['faceis'] or 0,
                "medias": dificuldade_stats['medias'] or 0,
                "dificeis": dificuldade_stats['dificeis'] or 0
            },
            "atualizado_em": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/questoes/<materia>')
def get_questoes(materia):
    """API avançada de questões com filtros"""
    try:
        limit = request.args.get('limit', 10, type=int)
        dificuldade = request.args.get('dificuldade', None)
        randomize = request.args.get('random', 'true').lower() == 'true'
        
        conn = sqlite3.connect('concurso.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM questões WHERE disciplina = ?"
        params = [materia]
        
        if dificuldade:
            query += " AND dificuldade = ?"
            params.append(dificuldade)
        
        if randomize:
            query += " ORDER BY RANDOM()"
        else:
            query += " ORDER BY id"
        
        query += " LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        questoes = []
        for row in resultados:
            questao = QuestaoWeb(
                id=row['id'],
                enunciado=row['enunciado'],
                materia=row['disciplina'],
                alt_a=row['alt_a'],
                alt_b=row['alt_b'],
                alt_c=row['alt_c'],
                alt_d=row['alt_d'],
                gabarito=row['gabarito'],
                dificuldade=row.get('dificuldade', 'Médio'),
                justificativa=row.get('justificativa')
            )
            questoes.append(questao.to_dict())
        
        conn.close()
        
        return jsonify({
            "disciplina": materia,
            "quantidade": len(questoes),
            "questoes": questoes,
            "filtros_aplicados": {
                "dificuldade": dificuldade,
                "randomize": randomize,
                "limit": limit
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulado/configurar', methods=['POST'])
def configurar_simulado():
    """API para configurar simulado personalizado"""
    try:
        data = request.get_json()
        
        materias = data.get('materias', [])
        quantidade_total = data.get('quantidade_total', 50)
        tempo_minutos = data.get('tempo_minutos', 180)
        
        # Lógica avançada de configuração de simulado
        conn = sqlite3.connect('concurso.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM questões WHERE 1=1"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND disciplina IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade_total)
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        questoes_simulado = []
        for row in resultados:
            questao = {
                'id': row['id'],
                'enunciado': row['enunciado'],
                'materia': row['disciplina'],
                'alternativas': {
                    'A': row['alt_a'],
                    'B': row['alt_b'],
                    'C': row['alt_c'],
                    'D': row['alt_d']
                },
                'resposta_correta': row['gabarito'],
                'dificuldade': row.get('dificuldade', 'Médio')
            }
            questoes_simulado.append(questao)
        
        conn.close()
        
        return jsonify({
            "simulado_configurado": True,
            "quantidade_questoes": len(questoes_simulado),
            "tempo_minutos": tempo_minutos,
            "materias_incluidas": materias,
            "questoes": questoes_simulado,
            "instrucoes": {
                "tempo_por_questao": f"{tempo_minutos/len(questoes_simulado):.1f} min" if questoes_simulado else "N/A",
                "dificuldade_media": "Calculada automaticamente",
                "recomendacao": "Mantenha o ritmo constante"
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 ConcursoMaster AI Professional iniciando na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
