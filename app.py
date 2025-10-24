from flask import Flask, jsonify, send_from_directory, request
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

app = Flask(__name__)

def get_db_connection():
    """Conexão segura com o banco"""
    try:
        conn = sqlite3.connect('concurso.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None

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
    """API de matérias com tratamento robusto"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"materias": [], "estatisticas": {}, "total_geral": 0})
    
    try:
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questões'")
        if not cursor.fetchone():
            conn.close()
            return jsonify({"materias": [], "estatisticas": {}, "total_geral": 0})
        
        cursor.execute("SELECT DISTINCT disciplina FROM questões ORDER BY disciplina")
        rows = cursor.fetchall()
        materias = [row['disciplina'] for row in rows] if rows else []
        
        # Estatísticas por matéria
        estatisticas = {}
        for materia in materias:
            try:
                cursor.execute('''
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN dificuldade = 'Fácil' THEN 1 ELSE 0 END) as faceis,
                           SUM(CASE WHEN dificuldade = 'Médio' THEN 1 ELSE 0 END) as medias,
                           SUM(CASE WHEN dificuldade = 'Difícil' THEN 1 ELSE 0 END) as dificeis
                    FROM questões WHERE disciplina = ?
                ''', (materia,))
                stats = cursor.fetchone()
                estatisticas[materia] = {
                    'total': stats['total'] or 0,
                    'faceis': stats['faceis'] or 0,
                    'medias': stats['medias'] or 0,
                    'dificeis': stats['dificeis'] or 0
                }
            except:
                estatisticas[materia] = {'total': 0, 'faceis': 0, 'medias': 0, 'dificeis': 0}
        
        conn.close()
        
        return jsonify({
            "materias": materias,
            "estatisticas": estatisticas,
            "total_geral": sum(stats['total'] for stats in estatisticas.values())
        })
        
    except Exception as e:
        print(f"❌ Erro em /api/materias: {e}")
        conn.close()
        return jsonify({"materias": [], "estatisticas": {}, "total_geral": 0})

@app.route('/api/dashboard-data')
def dashboard():
    """Dashboard à prova de erros"""
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "total_questoes": 0, 
            "questoes_por_materia": {},
            "dificuldade": {"faceis": 0, "medias": 0, "dificeis": 0},
            "atualizado_em": datetime.now().isoformat()
        })
    
    try:
        cursor = conn.cursor()
        
        # Verificar tabela
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questões'")
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                "total_questoes": 0, 
                "questoes_por_materia": {},
                "dificuldade": {"faceis": 0, "medias": 0, "dificeis": 0},
                "atualizado_em": datetime.now().isoformat()
            })
        
        # Total de questões
        cursor.execute("SELECT COUNT(*) as total FROM questões")
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        
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
        try:
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN dificuldade = 'Fácil' THEN 1 ELSE 0 END) as faceis,
                    SUM(CASE WHEN dificuldade = 'Médio' THEN 1 ELSE 0 END) as medias,
                    SUM(CASE WHEN dificuldade = 'Difícil' THEN 1 ELSE 0 END) as dificeis
                FROM questões
            ''')
            dificuldade_stats = cursor.fetchone()
            faceis = dificuldade_stats['faceis'] or 0 if dificuldade_stats else 0
            medias = dificuldade_stats['medias'] or 0 if dificuldade_stats else 0
            dificeis = dificuldade_stats['dificeis'] or 0 if dificuldade_stats else 0
        except:
            faceis = medias = dificeis = 0
        
        conn.close()
        
        return jsonify({
            "total_questoes": total,
            "questoes_por_materia": questoes_por_materia,
            "dificuldade": {
                "faceis": faceis,
                "medias": medias,
                "dificeis": dificeis
            },
            "atualizado_em": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erro em /api/dashboard-data: {e}")
        conn.close()
        return jsonify({
            "total_questoes": 0, 
            "questoes_por_materia": {},
            "dificuldade": {"faceis": 0, "medias": 0, "dificeis": 0},
            "atualizado_em": datetime.now().isoformat()
        })

@app.route('/api/questoes/<materia>')
def get_questoes(materia):
    """API de questões super resiliente"""
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "disciplina": materia, 
            "quantidade": 0, 
            "questoes": [],
            "filtros_aplicados": {}
        })
    
    try:
        cursor = conn.cursor()
        limit = request.args.get('limit', 10, type=int)
        dificuldade = request.args.get('dificuldade', None)
        randomize = request.args.get('random', 'true').lower() == 'true'
        
        # Verificar tabela
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questões'")
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                "disciplina": materia, 
                "quantidade": 0, 
                "questoes": [],
                "filtros_aplicados": {}
            })
        
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
            questao = {
                'id': row['id'],
                'enunciado': row['enunciado'],
                'materia': row['disciplina'],
                'alternativa_a': row['alt_a'],
                'alternativa_b': row['alt_b'],
                'alternativa_c': row['alt_c'],
                'alternativa_d': row['alt_d'],
                'resposta_correta': row['gabarito'],
                'dificuldade': row.get('dificuldade', 'Médio'),
                'justificativa': row.get('justificativa')
            }
            questoes.append(questao)
        
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
        print(f"❌ Erro em /api/questoes: {e}")
        conn.close()
        return jsonify({
            "disciplina": materia, 
            "quantidade": 0, 
            "questoes": [],
            "filtros_aplicados": {}
        })

@app.route('/api/simulado/configurar', methods=['POST'])
def configurar_simulado():
    """API de simulado com tratamento completo"""
    try:
        data = request.get_json() or {}
        
        materias = data.get('materias', [])
        quantidade_total = min(data.get('quantidade_total', 50), 100)  # Limite máximo
        tempo_minutos = data.get('tempo_minutos', 180)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Erro de conexão com o banco"}), 500
        
        cursor = conn.cursor()
        
        # Verificar tabela
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questões'")
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Tabela não encontrada"}), 404
        
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
        print(f"❌ Erro em /api/simulado/configurar: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 ConcursoMaster AI Professional iniciando na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
