from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import os
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_2024_corrigido'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DATABASE = 'concurso.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def carregar_questoes_csv():
    '''Carrega questões do CSV para o banco'''
    if not os.path.exists('questoes.csv'):
        print('❌ Arquivo questoes.csv não encontrado')
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT,
                materia TEXT,
                alternativas TEXT,
                resposta_correta TEXT,
                explicacao TEXT,
                dificuldade TEXT
            )
        ''')
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            for row in csv_reader:
                try:
                    enunciado = row.get('enunciado', '').strip()
                    materia = row.get('disciplina', 'Geral').strip()
                    
                    alternativas_dict = {
                        'A': row.get('alt_a', '').strip(),
                        'B': row.get('alt_b', '').strip(),
                        'C': row.get('alt_c', '').strip(),
                        'D': row.get('alt_d', '').strip()
                    }
                    
                    resposta_correta = row.get('gabarito', 'A').strip()
                    
                    explicacao_parts = []
                    if row.get('just_a'): explicacao_parts.append("A: " + row['just_a'])
                    if row.get('just_b'): explicacao_parts.append("B: " + row['just_b'])
                    if row.get('just_c'): explicacao_parts.append("C: " + row['just_c'])
                    if row.get('just_d'): explicacao_parts.append("D: " + row['just_d'])
                    
                    explicacao = ' | '.join(explicacao_parts) if explicacao_parts else 'Explicação não disponível'
                    dificuldade = row.get('dificuldade', 'Média').strip()
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO questoes 
                        (enunciado, materia, alternativas, resposta_correta, explicacao, dificuldade)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (enunciado, materia, json.dumps(alternativas_dict), resposta_correta, explicacao, dificuldade))
                    
                except Exception as e:
                    continue
        
        conn.commit()
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f'✅ {count} questões disponíveis no banco!')
        return True
        
    except Exception as e:
        print(f'❌ Erro ao carregar CSV: {e}')
        return False

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    try:
        carregar_questoes_csv()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT materia FROM questoes WHERE materia IS NOT NULL')
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        
        print(f'📚 Matérias disponíveis: {materias}')
        return render_template('simulado-simple.html', materias=materias)
        
    except Exception as e:
        print(f'❌ Erro no /simulado: {e}')
        return render_template('simulado-simple.html', materias=['Língua Portuguesa', 'Matemática', 'Raciocínio Lógico'])

@app.route('/questao/<int:numero>')
def questao(numero):
    '''Página REAL da questão com feedback educativo'''
    if 'simulado_ativo' not in session:
        return render_template('erro.html', mensagem='Simulado não iniciado. <a href="/simulado">Iniciar simulado</a>')
    
    # Obter questões do banco
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if 'questoes_ids' in session:
        questao_ids = session['questoes_ids']
        if 1 <= numero <= len(questao_ids):
            cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_ids[numero-1],))
            questao_db = cursor.fetchone()
            
            if questao_db:
                # Formatar questão
                try:
                    alternativas = json.loads(questao_db['alternativas'])
                except:
                    alternativas = {'A': 'Alternativa A', 'B': 'Alternativa B', 'C': 'Alternativa C', 'D': 'Alternativa D'}
                
                questao_atual = {
                    'id': questao_db['id'],
                    'enunciado': questao_db['enunciado'],
                    'materia': questao_db['materia'],
                    'alternativas': alternativas,
                    'resposta_correta': questao_db['resposta_correta'],
                    'explicacao': questao_db['explicacao'],
                    'dificuldade': questao_db['dificuldade'] if 'dificuldade' in questao_db.keys() else 'Média'
                }
                
                # Verificar se resposta foi submetida
                resposta_submetida = False
                resposta_correta = False
                resposta_usuario = session.get('respostas', {}).get(str(numero))
                
                if resposta_usuario:
                    resposta_submetida = True
                    resposta_correta = (resposta_usuario == questao_db['resposta_correta'])
                
                conn.close()
                return render_template('questao.html',
                                     numero=numero,
                                     total_questoes=len(questao_ids),
                                     questao=questao_atual,
                                     resposta_submetida=resposta_submetida,
                                     resposta_correta=resposta_correta)
    
    conn.close()
    return render_template('erro.html', mensagem='Questão não encontrada.')

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    '''API para iniciar simulado - CORRIGIDA quantidade'''
    try:
        data = request.get_json()
        quantidade = int(data.get('quantidade', 5))  # CORRIGIDO: garantir que é int
        materias = data.get('materias', [])
        
        print(f'🚀 Iniciando simulado: {quantidade} questões, matérias: {materias}')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # CORREÇÃO: Garantir que busca exatamente a quantidade solicitada
        if not materias:
            cursor.execute('SELECT id FROM questoes ORDER BY RANDOM() LIMIT ?', (quantidade,))
        else:
            placeholders = ','.join(['?'] * len(materias))
            query = f'SELECT id FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
            cursor.execute(query, materias + [quantidade])
        
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        # CORREÇÃO: Verificar se encontrou exatamente a quantidade solicitada
        if len(questao_ids) < quantidade:
            print(f'⚠️  Aviso: Solicitadas {quantidade} questões, mas só encontradas {len(questao_ids)}')
        
        if not questao_ids:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 404
        
        # Configurar sessão
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        session['inicio'] = datetime.now().isoformat()
        session['config'] = {
            'quantidade_solicitada': quantidade,
            'quantidade_obtida': len(questao_ids),
            'materias': materias
        }
        
        print(f'✅ Simulado configurado com {len(questao_ids)} questões')
        
        return jsonify({
            'success': True,
            'total': len(questao_ids),
            'questoes_ids': questao_ids,
            'aviso': f'Encontradas {len(questao_ids)} de {quantidade} questões solicitadas' if len(questao_ids) < quantidade else None
        })
        
    except Exception as e:
        print(f'❌ Erro ao iniciar simulado: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    '''Salvar resposta da questão'''
    try:
        if 'simulado_ativo' not in session:
            return jsonify({'success': False, 'error': 'Simulado não iniciado'}), 400
        
        data = request.get_json()
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        print(f'📝 Questão {questao_numero}: resposta "{resposta}" salva')
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f'❌ Erro ao salvar resposta: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/resposta/<int:numero>')
def obter_resposta(numero):
    '''Obter resposta salva da questão'''
    try:
        if 'simulado_ativo' not in session:
            return jsonify({'resposta': None})
        
        resposta = session['respostas'].get(str(numero))
        return jsonify({'resposta': resposta})
        
    except Exception as e:
        print(f'❌ Erro ao obter resposta: {e}')
        return jsonify({'resposta': None})

@app.route('/simulado/resultado')
def resultado_simulado():
    '''Página de resultado com feedback educativo'''
    if 'simulado_ativo' not in session:
        return render_template('erro.html', mensagem='Nenhum simulado em andamento.')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    questao_ids = session.get('questoes_ids', [])
    respostas = session.get('respostas', {})
    config = session.get('config', {})
    
    corretas = 0
    revisao = []
    
    for i, questao_id in enumerate(questao_ids, 1):
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
        questao_db = cursor.fetchone()
        
        if questao_db:
            resposta_usuario = respostas.get(str(i))
            resposta_correta = questao_db['resposta_correta']
            correta = resposta_usuario == resposta_correta
            
            if correta:
                corretas += 1
            
            # Formatar alternativas para exibição
            try:
                alternativas = json.loads(questao_db['alternativas'])
            except:
                alternativas = {'A': 'Alt A', 'B': 'Alt B', 'C': 'Alt C', 'D': 'Alt D'}
            
            texto_resposta_usuario = alternativas.get(resposta_usuario, 'Não respondida') if resposta_usuario else 'Não respondida'
            texto_resposta_correta = alternativas.get(resposta_correta, 'N/A')
            
            revisao.append({
                'numero': i,
                'enunciado': questao_db['enunciado'],
                'materia': questao_db['materia'],
                'resposta_usuario': f"{resposta_usuario}: {texto_resposta_usuario}" if resposta_usuario else 'Não respondida',
                'resposta_correta': f"{resposta_correta}: {texto_resposta_correta}",
                'correta': correta,
                'explicacao': questao_db['explicacao'],
                'dificuldade': questao_db['dificuldade'] if 'dificuldade' in questao_db.keys() else 'Média'
            })
    
    conn.close()
    
    total_questoes = len(questao_ids)
    porcentagem = (corretas / total_questoes) * 100 if total_questoes > 0 else 0
    erradas = total_questoes - corretas
    
    # Calcular tempo
    inicio = datetime.fromisoformat(session['inicio'])
    fim = datetime.now()
    tempo_segundos = (fim - inicio).total_seconds()
    tempo_minutos = tempo_segundos / 60
    
    # Feedback educativo
    if porcentagem >= 80:
        feedback = '🎉 Excelente! Seu desempenho foi ótimo! Continue assim!'
    elif porcentagem >= 60:
        feedback = '👍 Bom trabalho! Você está no caminho certo, continue estudando!'
    elif porcentagem >= 40:
        feedback = '💪 Está evoluindo! Revise os conteúdos que errou para melhorar.'
    else:
        feedback = '📚 Hora de reforçar os estudos! Analise as explicações das questões erradas.'
    
    # Aviso sobre quantidade de questões
    aviso_quantidade = None
    if config.get('quantidade_solicitada') and config.get('quantidade_obtida'):
        if config['quantidade_solicitada'] > config['quantidade_obtida']:
            aviso_quantidade = f"Foram utilizadas {config['quantidade_obtida']} questões (solicitadas: {config['quantidade_solicitada']})"
    
    # Limpar sessão do simulado
    session.pop('simulado_ativo', None)
    session.pop('questoes_ids', None)
    session.pop('respostas', None)
    session.pop('inicio', None)
    session.pop('config', None)
    
    return render_template('resultado.html',
                         total_questoes=total_questoes,
                         corretas=corretas,
                         erradas=erradas,
                         porcentagem=porcentagem,
                         tempo_minutos=tempo_minutos,
                         feedback=feedback,
                         revisao=revisao,
                         aviso_quantidade=aviso_quantidade)

@app.route('/redacao')
def redacao():
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/erro')
def erro():
    mensagem = request.args.get('mensagem', 'Ocorreu um erro.')
    return render_template('erro.html', mensagem=mensagem)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

