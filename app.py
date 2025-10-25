from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'diagnostico_completo_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24
app.config['TEMPLATES_AUTO_RELOAD'] = True

DATABASE = 'concurso.db'

def debug_log(message, level='INFO'):
    '''Sistema de logging completo'''
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f'🔍 [{timestamp}] {level}: {message}')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    '''Inicializa o banco com diagnóstico completo'''
    try:
        debug_log('=== INICIANDO BANCO DE DADOS ===')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT NOT NULL,
                materia TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT,
                dica TEXT,
                formula TEXT,
                dificuldade TEXT DEFAULT 'Média'
            )
        ''')
        
        # Verificar questões existentes
        cursor.execute('SELECT COUNT(*) as total, GROUP_CONCAT(DISTINCT materia) as materias FROM questoes')
        resultado = cursor.fetchone()
        total_questoes = resultado['total']
        materias = resultado['materias'] or 'Nenhuma'
        
        debug_log(f'Questões no banco: {total_questoes}')
        debug_log(f'Matérias disponíveis: {materias}')
        
        if total_questoes == 0:
            debug_log('Nenhuma questão encontrada, tentando carregar...')
            if not carregar_questoes_com_fallback():
                debug_log('❌ FALHA CRÍTICA: Não foi possível carregar questões', 'ERRO')
                return False
        
        conn.commit()
        conn.close()
        debug_log('✅ Banco inicializado com sucesso')
        return True
        
    except Exception as e:
        debug_log(f'❌ ERRO CRÍTICO NO BANCO: {e}', 'ERRO')
        return False

def carregar_questoes_com_fallback():
    '''Tenta carregar questões com múltiplos fallbacks'''
    debug_log('Tentando carregar questões...')
    
    # Tentativa 1: Carregar do CSV
    if carregar_questoes_csv():
        return True
    
    # Tentativa 2: Criar questões de exemplo
    debug_log('CSP não encontrado, criando questões de exemplo...')
    if criar_questoes_exemplo():
        return True
    
    # Tentativa 3: Criar questões mínimas de emergência
    debug_log('Criando questões mínimas de emergência...')
    return criar_questoes_emergencia()

def carregar_questoes_csv():
    '''Tenta carregar do CSV com diagnóstico'''
    if not os.path.exists('questoes.csv'):
        debug_log('❌ Arquivo questoes.csv não encontrado', 'ERRO')
        return False
    
    try:
        debug_log('📖 Lendo arquivo CSV...')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            # Verificar encoding
            try:
                csv_reader = csv.DictReader(file, delimiter=';')
                debug_log(f'Colunas detectadas: {csv_reader.fieldnames}')
            except Exception as e:
                debug_log(f'❌ Erro ao ler CSV: {e}', 'ERRO')
                return False
            
            file.seek(0)  # Voltar ao início
            csv_reader = csv.DictReader(file, delimiter=';')
            
            questions_loaded = 0
            errors = 0
            
            for i, row in enumerate(csv_reader):
                try:
                    if i == 0:  # Debug da primeira linha
                        debug_log(f'Primeira linha: {str(dict(row))[:200]}...')
                    
                    enunciado = row.get('enunciado', '').strip()
                    if not enunciado:
                        continue
                    
                    materia = row.get('disciplina', 'Geral').strip()
                    if not materia:
                        materia = 'Geral'
                    
                    # Processar alternativas
                    alternativas = {}
                    for letra in ['A', 'B', 'C', 'D']:
                        texto = row.get(f'alt_{letra.lower()}', '') or row.get(f'alt{letra.lower()}', '') or f'Alternativa {letra}'
                        alternativas[letra] = texto.strip() or f'Alternativa {letra}'
                    
                    resposta = row.get('gabarito', 'A').strip().upper()
                    if resposta not in ['A', 'B', 'C', 'D']:
                        resposta = 'A'
                    
                    # Inserir no banco
                    cursor.execute('''
                        INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        enunciado,
                        materia,
                        json.dumps(alternativas),
                        resposta,
                        f'Resposta correta: {resposta}',
                        '💡 Analise cuidadosamente cada alternativa',
                        ''
                    ))
                    
                    questions_loaded += 1
                    
                except Exception as e:
                    errors += 1
                    if errors <= 3:  # Mostrar apenas os primeiros erros
                        debug_log(f'Erro na linha {i}: {e}', 'ERRO')
                    continue
        
        conn.commit()
        conn.close()
        
        debug_log(f'✅ CSV carregado: {questions_loaded} questões, {errors} erros')
        return questions_loaded > 0
        
    except Exception as e:
        debug_log(f'❌ ERRO CRÍTICO NO CSV: {e}', 'ERRO')
        return False

def criar_questoes_exemplo():
    '''Cria questões de exemplo robustas'''
    try:
        debug_log('Criando questões de exemplo...')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        exemplos = [
            {
                'enunciado': 'Qual é a capital do Brasil?',
                'materia': 'Geografia',
                'alternativas': {'A': 'Rio de Janeiro', 'B': 'Brasília', 'C': 'São Paulo', 'D': 'Salvador'},
                'resposta': 'B'
            },
            {
                'enunciado': '2 + 2 é igual a:',
                'materia': 'Matemática', 
                'alternativas': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
                'resposta': 'B'
            },
            {
                'enunciado': 'Qual artigo define direitos fundamentais na Constituição?',
                'materia': 'Direito Constitucional',
                'alternativas': {'A': 'Artigo 1º', 'B': 'Artigo 5º', 'C': 'Artigo 10º', 'D': 'Artigo 15º'},
                'resposta': 'B'
            }
        ]
        
        for ex in exemplos:
            cursor.execute('''
                INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                ex['enunciado'],
                ex['materia'],
                json.dumps(ex['alternativas']),
                ex['resposta'],
                f'Resposta correta: {ex["resposta"]}',
                '💡 Dica: Leia atentamente o enunciado',
                ''
            ))
        
        conn.commit()
        conn.close()
        debug_log(f'✅ {len(exemplos)} questões de exemplo criadas')
        return True
        
    except Exception as e:
        debug_log(f'❌ Erro ao criar exemplos: {e}', 'ERRO')
        return False

def criar_questoes_emergencia():
    '''Cria questões mínimas de emergência'''
    try:
        debug_log('CRIANDO QUESTÕES DE EMERGÊNCIA...', 'ALERTA')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Questão mínima de emergência
        cursor.execute('''
            INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Questão de exemplo do sistema. O simulado está funcionando!',
            'Geral',
            json.dumps({'A': 'Alternativa A', 'B': 'Alternativa B', 'C': 'Alternativa C', 'D': 'Alternativa D'}),
            'A',
            'Esta é uma questão de exemplo para teste do sistema.',
            '💡 Esta questão foi gerada automaticamente pelo sistema.',
            ''
        ))
        
        conn.commit()
        conn.close()
        debug_log('✅ Questão de emergência criada')
        return True
        
    except Exception as e:
        debug_log(f'❌ FALHA CRÍTICA: {e}', 'ERRO')
        return False

# ========== ROTAS COM DIAGNÓSTICO ==========

@app.route('/')
def index():
    debug_log('📄 GET /')
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    debug_log('🎯 GET /simulado')
    try:
        if not init_database():
            return render_template('error.html', mensagem='Sistema temporariamente indisponível')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar matérias disponíveis
        cursor.execute('SELECT DISTINCT materia, COUNT(*) as total FROM questoes GROUP BY materia ORDER BY materia')
        materias_db = cursor.fetchall()
        conn.close()
        
        materias = [{'nome': row['materia'], 'total': row['total']} for row in materias_db]
        debug_log(f'📚 Matérias para exibição: {len(materias)}')
        
        return render_template('simulado.html', materias=materias)
        
    except Exception as e:
        debug_log(f'❌ ERRO EM /simulado: {e}', 'ERRO')
        return render_template('error.html', mensagem=f'Erro: {str(e)}')

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    debug_log('🚀 POST /api/simulado/iniciar', 'IMPORTANTE')
    
    try:
        # Log dos headers
        debug_log(f'Headers: {dict(request.headers)}')
        debug_log(f'Content-Type: {request.content_type}')
        
        # Tentar pegar dados JSON
        if request.content_type == 'application/json':
            data = request.get_json()
            debug_log(f'📦 Dados JSON recebidos: {data}')
        else:
            debug_log('⚠️ Content-Type não é JSON, tentando parse manual')
            data = request.get_json(force=True, silent=True)
            if not data:
                raw_data = request.get_data(as_text=True)
                debug_log(f'📦 Dados brutos: {raw_data[:500]}...')
                return jsonify({'success': False, 'error': 'Dados não são JSON válido'}), 400
        
        if not data:
            debug_log('❌ Nenhum dado recebido', 'ERRO')
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        quantidade = int(data.get('quantidade', 10))
        materias_selecionadas = data.get('materias', [])
        configs = data.get('configs', {})
        
        debug_log(f'📊 Configuração: {quantidade} questões, {len(materias_selecionadas)} matérias')
        debug_log(f'🎯 Matérias selecionadas: {materias_selecionadas}')
        
        # Validações
        if not materias_selecionadas:
            debug_log('❌ Nenhuma matéria selecionada', 'ERRO')
            return jsonify({'success': False, 'error': 'Selecione pelo menos uma matéria'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar questões
        placeholders = ','.join(['?'] * len(materias_selecionadas))
        query = f'SELECT id FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
        
        debug_log(f'📋 Query: {query}')
        debug_log(f'🔍 Parâmetros: {materias_selecionadas + [quantidade]}')
        
        cursor.execute(query, materias_selecionadas + [quantidade])
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        debug_log(f'📚 Questões encontradas: {len(questao_ids)}')
        
        if not questao_ids:
            # Debug: ver matérias disponíveis
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT materia FROM questoes')
            materias_disponiveis = [row['materia'] for row in cursor.fetchall()]
            conn.close()
            
            debug_log(f'📖 Matérias disponíveis: {materias_disponiveis}')
            debug_log(f'🎯 Matérias solicitadas: {materias_selecionadas}')
            
            return jsonify({
                'success': False, 
                'error': f'Nenhuma questão encontrada. Matérias disponíveis: {", ".join(materias_disponiveis)}'
            }), 404
        
        # Configurar sessão
        session.clear()
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        session['configs'] = configs
        session['inicio_simulado'] = datetime.now().isoformat()
        
        debug_log(f'✅ Simulado configurado: {len(questao_ids)} questões')
        debug_log(f'🔐 Sessão configurada: simulado_ativo={session.get("simulado_ativo")}')
        
        return jsonify({
            'success': True,
            'total_questoes': len(questao_ids),
            'redirect_url': url_for('questao', numero=1),
            'debug': {
                'questoes_encontradas': len(questao_ids),
                'materias_selecionadas': materias_selecionadas
            }
        })
        
    except Exception as e:
        debug_log(f'❌ ERRO CRÍTICO: {e}', 'ERRO')
        import traceback
        debug_log(f'📝 Stack trace: {traceback.format_exc()}', 'ERRO')
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@app.route('/questao/<int:numero>')
def questao(numero):
    debug_log(f'📖 GET /questao/{numero}')
    
    if not session.get('simulado_ativo'):
        debug_log('❌ Sessão não ativa, redirecionando...')
        return redirect(url_for('simulado'))
    
    questao_ids = session.get('questoes_ids', [])
    debug_log(f'📚 IDs na sessão: {len(questao_ids)} questões')
    
    if numero < 1 or numero > len(questao_ids):
        debug_log(f'❌ Número inválido: {numero} (max: {len(questao_ids)})')
        return render_template('error.html', mensagem='Questão não encontrada')
    
    try:
        questao_id = questao_ids[numero-1]
        debug_log(f'🔍 Buscando questão ID: {questao_id}')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
        questao_db = cursor.fetchone()
        conn.close()
        
        if not questao_db:
            debug_log(f'❌ Questão {questao_id} não encontrada no banco')
            return render_template('error.html', mensagem='Questão corrompida')
        
        # Processar questão
        try:
            alternativas = json.loads(questao_db['alternativas'])
        except:
            alternativas = {'A': 'Erro', 'B': 'Erro', 'C': 'Erro', 'D': 'Erro'}
            debug_log('⚠️ Erro ao carregar alternativas')
        
        resposta_usuario = session.get('respostas', {}).get(str(numero))
        configs = session.get('configs', {})
        
        questao_data = {
            'id': questao_db['id'],
            'enunciado': questao_db['enunciado'],
            'materia': questao_db['materia'],
            'alternativas': alternativas,
            'resposta_correta': questao_db['resposta_correta'],
            'explicacao': questao_db['explicacao'],
            'dica': questao_db['dica'],
            'formula': questao_db['formula'],
            'dificuldade': questao_db['dificuldade']
        }
        
        debug_log(f'✅ Questão {numero} carregada: {questao_data["materia"]}')
        
        return render_template('questao.html',
                             numero=numero,
                             total_questoes=len(questao_ids),
                             questao=questao_data,
                             resposta_usuario=resposta_usuario,
                             configs=configs,
                             questao_respondida=resposta_usuario is not None)
        
    except Exception as e:
        debug_log(f'❌ ERRO NA QUESTÃO: {e}', 'ERRO')
        return render_template('error.html', mensagem=f'Erro: {str(e)}')

@app.route('/api/questao/responder', methods=['POST'])
def responder_questao():
    debug_log('📝 POST /api/questao/responder')
    
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'success': False, 'error': 'Simulado não iniciado'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        debug_log(f'📤 Resposta: questão {questao_numero} = {resposta}')
        
        # Salvar resposta
        if 'respostas' not in session:
            session['respostas'] = {}
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        debug_log(f'✅ Resposta salva: {dict(session["respostas"])}')
        
        return jsonify({'success': True})
        
    except Exception as e:
        debug_log(f'❌ ERRO AO SALVAR RESPOSTA: {e}', 'ERRO')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug')
def debug():
    '''Página de debug para diagnóstico'''
    debug_log('🔧 GET /debug')
    
    info = {
        'sessao': dict(session),
        'questoes_no_banco': 0,
        'materias_disponiveis': [],
        'arquivos': os.listdir('.')
    }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM questoes')
        info['questoes_no_banco'] = cursor.fetchone()['total']
        
        cursor.execute('SELECT DISTINCT materia FROM questoes')
        info['materias_disponiveis'] = [row['materia'] for row in cursor.fetchall()]
        
        conn.close()
    except Exception as e:
        info['erro_banco'] = str(e)
    
    return jsonify(info)

@app.route('/debug/reset')
def debug_reset():
    '''Reset completo para testes'''
    debug_log('🔄 GET /debug/reset', 'IMPORTANTE')
    
    try:
        # Limpar banco
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM questoes')
        conn.commit()
        conn.close()
        
        # Limpar sessão
        session.clear()
        
        # Recriar questões
        init_database()
        
        return jsonify({'success': True, 'message': 'Sistema resetado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_log(f'🚀 SERVIDOR INICIADO NA PORTA {port}', 'IMPORTANTE')
    debug_log('=== SISTEMA DE DIAGNÓSTICO ATIVO ===', 'IMPORTANTE')
    app.run(host='0.0.0.0', port=port, debug=False)
