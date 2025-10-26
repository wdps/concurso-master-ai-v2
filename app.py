from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'concurso_master_secret_key_v4'
app.config['SESSION_TYPE'] = 'filesystem'

def get_db_connection():
    conn = sqlite3.connect('concurso.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Verificar se o banco está ok
def verificar_banco():
    try:
        conn = get_db_connection()
        
        # Verificar tabelas
        tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print("📊 Tabelas no banco:")
        for tabela in tabelas:
            print(f"   - {tabela['name']}")
        
        # Verificar questões
        count_questoes = conn.execute("SELECT COUNT(*) FROM questoes").fetchone()[0]
        count_temas = conn.execute("SELECT COUNT(*) FROM temas_redacao").fetchone()[0]
        
        print(f"📚 Estatísticas:")
        print(f"   - Questões: {count_questoes}")
        print(f"   - Temas de redação: {count_temas}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return False

# Rotas principais
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# API Materias
@app.route('/api/materias')
def api_materias():
    try:
        conn = get_db_connection()
        materias_data = conn.execute('''
            SELECT materia, disciplina, COUNT(*) as total
            FROM questoes 
            GROUP BY materia, disciplina
            ORDER BY disciplina, materia
        ''').fetchall()
        
        materias = []
        estatisticas = {}
        
        for row in materias_data:
            materia = row['materia']
            materias.append(materia)
            estatisticas[materia] = {
                'total': row['total'],
                'disciplina': row['disciplina']
            }
        
        return jsonify({
            'success': True,
            'materias': materias,
            'estatisticas': estatisticas
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API Simulado
@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    try:
        data = request.get_json()
        materias = data.get('materias', [])
        quantidade_total = data.get('quantidade_total', 10)
        tempo_minutos = data.get('tempo_minutos', 60)
        aleatorio = data.get('aleatorio', True)
        
        if not materias:
            return jsonify({'success': False, 'error': 'Nenhuma matéria selecionada'}), 400
        
        simulado_id = f"simulado_{int(time.time())}_{random.randint(1000, 9999)}"
        
        conn = get_db_connection()
        placeholders = ','.join(['?'] * len(materias))
        query = f'SELECT * FROM questoes WHERE materia IN ({placeholders})'
        
        if aleatorio:
            query += ' ORDER BY RANDOM()'
        else:
            query += ' ORDER BY materia, dificuldade'
        
        query += ' LIMIT ?'
        questões = conn.execute(query, materias + [quantidade_total]).fetchall()
        
        if not questões:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 400
        
        primeira_questao = {
            'id': questões[0]['id'],
            'disciplina': questões[0]['disciplina'],
            'materia': questões[0]['materia'],
            'enunciado': questões[0]['enunciado'],
            'alternativas': json.loads(questões[0]['alternativas']),
            'dificuldade': questões[0]['dificuldade']
        }
        
        if 'user_id' not in session:
            session['user_id'] = f"user_{random.randint(10000, 99999)}"
        
        config_simulado = {
            'materias': materias,
            'quantidade_total': quantidade_total,
            'tempo_minutos': tempo_minutos,
            'aleatorio': aleatorio,
            'questoes_ids': [q['id'] for q in questões],
            'data_inicio': datetime.now().isoformat()
        }
        
        session['simulado_atual'] = {
            'simulado_id': simulado_id,
            'config': config_simulado,
            'respostas': {},
            'questao_atual': 0,
            'iniciado_em': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'simulado_id': simulado_id,
            'total_questoes': len(questões),
            'tempo_limite_seg': tempo_minutos * 60,
            'primeira_questao': primeira_questao
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/<simulado_id>/questao/<int:questao_index>')
def get_questao(simulado_id, questao_index):
    try:
        simulado_data = session.get('simulado_atual')
        if not simulado_data or simulado_data['simulado_id'] != simulado_id:
            return jsonify({'success': False, 'error': 'Simulado não encontrado'}), 404
        
        config = simulado_data['config']
        questao_id = config['questoes_ids'][questao_index]
        
        conn = get_db_connection()
        questao = conn.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,)).fetchone()
        
        if not questao:
            return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404
        
        questao_formatada = {
            'id': questao['id'],
            'disciplina': questao['disciplina'],
            'materia': questao['materia'],
            'enunciado': questao['enunciado'],
            'alternativas': json.loads(questao['alternativas']),
            'dificuldade': questao['dificuldade']
        }
        
        return jsonify({
            'success': True,
            'questao': questao_formatada
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/<simulado_id>/responder', methods=['POST'])
def responder_questao(simulado_id):
    try:
        data = request.get_json()
        questao_index = data.get('questao_index')
        alternativa = data.get('alternativa')
        
        simulado_data = session.get('simulado_atual')
        if not simulado_data or simulado_data['simulado_id'] != simulado_id:
            return jsonify({'success': False, 'error': 'Simulado não encontrado'}), 404
        
        config = simulado_data['config']
        questao_id = config['questoes_ids'][questao_index]
        
        conn = get_db_connection()
        questao = conn.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,)).fetchone()
        
        if not questao:
            return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404
        
        acertou = alternativa.upper() == questao['resposta_correta'].upper()
        
        feedback = {
            'acertou': acertou,
            'resposta_correta': questao['resposta_correta'],
            'justificativa': questao['justificativa'],
            'dica': questao['dica'],
            'formula': questao['formula']
        }
        
        if 'respostas' not in simulado_data:
            simulado_data['respostas'] = {}
        
        simulado_data['respostas'][str(questao_index)] = {
            'alternativa': alternativa,
            'feedbackData': feedback
        }
        
        session.modified = True
        
        return jsonify({
            'success': True,
            **feedback
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API Redação
@app.route('/api/redacao/temas')
def get_temas_redacao():
    try:
        conn = get_db_connection()
        temas = conn.execute('SELECT * FROM temas_redacao ORDER BY dificuldade, titulo').fetchall()
        
        temas_list = []
        for tema in temas:
            temas_list.append({
                'id': tema['id'],
                'titulo': tema['titulo'],
                'descricao': tema['descricao'],
                'tipo': tema['tipo'],
                'dificuldade': tema['dificuldade'],
                'palavras_chave': tema['palavras_chave']
            })
        
        return jsonify({
            'success': True,
            'temas': temas_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/redacao/corrigir', methods=['POST'])
def corrigir_redacao():
    try:
        data = request.get_json()
        texto = data.get('texto', '')
        
        # Simulação de correção
        palavras = len(texto.split())
        paragrafos = texto.count('\n\n') + 1
        
        competencias = {
            'competencia1': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Bom domínio da norma padrão.'},
            'competencia2': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Boa compreensão do tema.'},
            'competencia3': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Argumentação coerente.'},
            'competencia4': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Boa organização textual.'},
            'competencia5': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Proposta de intervenção adequada.'}
        }
        
        nota_final = sum(comp['nota'] for comp in competencias.values()) / 5
        
        correcao = {
            'nota_final': round(nota_final, 1),
            'competencias': competencias,
            'estatisticas': {
                'palavras': palavras,
                'paragrafos': paragrafos,
                'linhas': texto.count('\n') + 1
            },
            'sugestoes': [
                'Revise a concordância verbal.',
                'Desenvolva mais o segundo argumento.',
                'Mantenha o foco no tema proposto.'
            ]
        }
        
        return jsonify({
            'success': True,
            'correcao': correcao
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando ConcursoMaster AI...")
    if verificar_banco():
        print("✅ Banco de dados verificado e pronto!")
        print("🌐 Servidor rodando em: http://localhost:5000")
        print("📚 Funcionalidades disponíveis:")
        print("   - Simulados com 3 questões exemplo")
        print("   - Sistema de redação com 2 temas")
        print("   - Dashboard de estatísticas")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Falha na verificação do banco de dados!")
