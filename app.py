from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'concurso_master_debug_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24
app.config['TEMPLATES_AUTO_RELOAD'] = True

DATABASE = 'concurso.db'

def debug_log(message):
    '''Sistema de logging para debug'''
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f'🔍 [{timestamp}] {message}')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    '''Inicializa o banco com debug completo'''
    try:
        debug_log('Iniciando banco de dados...')
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        debug_log(f'Questões no banco: {count}')
        
        if count == 0:
            debug_log('Nenhuma questão encontrada, carregando do CSV...')
            if not load_questions_from_csv():
                debug_log('Criando questões de exemplo...')
                create_sample_questions()
        else:
            debug_log(f'✅ {count} questões carregadas do banco')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        debug_log(f'❌ ERRO NO BANCO: {e}')
        return False

def load_questions_from_csv():
    '''Carrega questões do CSV com debug detalhado'''
    if not os.path.exists('questoes.csv'):
        debug_log('❌ Arquivo questoes.csv não encontrado')
        return False
    
    try:
        debug_log('📖 Lendo arquivo CSV...')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            # Verificar encoding e delimitador
            first_line = file.readline()
            debug_log(f'Primeira linha do CSV: {first_line[:100]}...')
            
            file.seek(0)  # Voltar ao início
            csv_reader = csv.DictReader(file, delimiter=';')
            
            debug_log(f'Colunas do CSV: {csv_reader.fieldnames}')
            
            questions_loaded = 0
            errors = 0
            
            for i, row in enumerate(csv_reader):
                try:
                    # Debug da linha
                    if i < 3:  # Mostrar apenas as 3 primeiras para debug
                        debug_log(f'Linha {i}: {str(row)[:200]}...')
                    
                    enunciado = row.get('enunciado', '').strip()
                    materia = row.get('disciplina', '').strip()
                    
                    if not enunciado:
                        debug_log(f'⚠️  Linha {i} sem enunciado, pulando...')
                        continue
                    
                    if not materia:
                        materia = 'Geral'
                        debug_log(f'⚠️  Linha {i} sem matéria, usando "Geral"')
                    
                    # Alternativas
                    alternativas = {
                        'A': row.get('alt_a', '').strip() or 'Alternativa A',
                        'B': row.get('alt_b', '').strip() or 'Alternativa B', 
                        'C': row.get('alt_c', '').strip() or 'Alternativa C',
                        'D': row.get('alt_d', '').strip() or 'Alternativa D'
                    }
                    
                    resposta_correta = row.get('gabarito', 'A').strip().upper()
                    if resposta_correta not in ['A', 'B', 'C', 'D']:
                        resposta_correta = 'A'
                        debug_log(f'⚠️  Linha {i} com gabarito inválido: {row.get("gabarito")}, usando "A"')
                    
                    # Sistema de dicas
                    dica = generate_hint(materia)
                    formula = generate_formula(materia)
                    
                    # Explicação
                    explicacao = f"Resposta correta: {resposta_correta}. "
                    if row.get('just_a'):
                        explicacao += f"A: {row['just_a']} "
                    if row.get('dica_interpretacao'):
                        explicacao += f"Dica: {row['dica_interpretacao']}"
                    
                    # Inserir no banco
                    cursor.execute('''
                        INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (enunciado, materia, json.dumps(alternativas), resposta_correta, explicacao, dica, formula))
                    
                    questions_loaded += 1
                    
                    if questions_loaded % 10 == 0:
                        debug_log(f'📥 {questions_loaded} questões processadas...')
                        
                except Exception as e:
                    errors += 1
                    debug_log(f'❌ Erro na linha {i}: {e}')
                    continue
        
        conn.commit()
        conn.close()
        
        debug_log(f'✅ CSV carregado: {questions_loaded} questões, {errors} erros')
        return questions_loaded > 0
        
    except Exception as e:
        debug_log(f'❌ ERRO CRÍTICO NO CSV: {e}')
        return False

def create_sample_questions():
    '''Cria questões de exemplo se o CSV falhar'''
    try:
        debug_log('Criando questões de exemplo...')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sample_questions = [
            {
                'enunciado': 'Qual é a capital do Brasil?',
                'materia': 'Geografia',
                'alternativas': {'A': 'Rio de Janeiro', 'B': 'Brasília', 'C': 'São Paulo', 'D': 'Salvador'},
                'resposta_correta': 'B',
                'explicacao': 'Brasília foi escolhida como capital federal em 1960.',
                'dica': '💡 Pense na cidade planejada para ser a capital',
                'formula': ''
            },
            {
                'enunciado': '2 + 2 é igual a:',
                'materia': 'Matemática', 
                'alternativas': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
                'resposta_correta': 'B',
                'explicacao': 'Operação básica de adição: 2 + 2 = 4.',
                'dica': '💡 É uma operação fundamental da matemática',
                'formula': '📐 a + b = c'
            },
            {
                'enunciado': 'Qual artigo define os direitos fundamentais na Constituição?',
                'materia': 'Direito Constitucional',
                'alternativas': {'A': 'Artigo 1º', 'B': 'Artigo 5º', 'C': 'Artigo 10º', 'D': 'Artigo 15º'},
                'resposta_correta': 'B', 
                'explicacao': 'O Artigo 5º da Constituição trata dos direitos e garantias fundamentais.',
                'dica': '💡 Pense no artigo que trata de direitos individuais',
                'formula': ''
            },
            {
                'enunciado': 'Quem escreveu "O Cortiço"?',
                'materia': 'Literatura',
                'alternativas': {'A': 'Machado de Assis', 'B': 'Aluísio Azevedo', 'C': 'José de Alencar', 'D': 'Lima Barreto'},
                'resposta_correta': 'B',
                'explicacao': '"O Cortiço" é uma obra do escritor naturalista Aluísio Azevedo.',
                'dica': '💡 Pense no autor naturalista brasileiro',
                'formula': ''
            },
            {
                'enunciado': 'Qual a fórmula da área do círculo?',
                'materia': 'Matemática',
                'alternativas': {'A': 'A = l²', 'B': 'A = πr²', 'C': 'A = bh/2', 'D': 'A = 2πr'},
                'resposta_correta': 'B', 
                'explicacao': 'A área do círculo é calculada por A = π × raio².',
                'dica': '💡 Lembre-se que π é pi (aproximadamente 3.14)',
                'formula': '📐 A = πr²'
            }
        ]
        
        for questao in sample_questions:
            cursor.execute('''
                INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                questao['enunciado'],
                questao['materia'], 
                json.dumps(questao['alternativas']),
                questao['resposta_correta'],
                questao['explicacao'],
                questao['dica'],
                questao['formula']
            ))
        
        conn.commit()
        conn.close()
        debug_log('✅ 5 questões de exemplo criadas')
        return True
        
    except Exception as e:
        debug_log(f'❌ Erro ao criar questões exemplo: {e}')
        return False

def generate_hint(materia):
    '''Gera dicas inteligentes'''
    hints = {
        'Matemática': '💡 Analise a operação matemática e verifique suas propriedades',
        'Português': '💡 Observe a estrutura gramatical e o contexto da frase',
        'Geografia': '💡 Considere aspectos físicos e humanos da localização',
        'História': '💡 Contextualize o período histórico mencionado',
        'Direito': '💡 Lembre-se dos princípios fundamentais e hierarquia',
        'Raciocínio': '💡 Identifique padrões e use eliminação'
    }
    
    for key, hint in hints.items():
        if key.lower() in materia.lower():
            return hint
    
    return '💡 Leia atentamente o enunciado e analise cada alternativa'

def generate_formula(materia):
    '''Gera fórmulas relevantes'''
    formulas = {
        'Matemática': '📐 Área do círculo: A = πr² | Teorema de Pitágoras: a² + b² = c²',
        'Física': '⚡ F = m × a | v = Δs/Δt',
        'Química': '🧪 n = m/M | C = n/V'
    }
    
    for key, formula in formulas.items():
        if key.lower() in materia.lower():
            return formula
    
    return ''

# ========== ROTAS COM DEBUG ==========

@app.route('/')
def index():
    debug_log('📄 Acessando página inicial')
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    debug_log('🎯 Acessando página de simulado')
    try:
        if not init_database():
            return render_template('error.html', mensagem='Erro ao carregar banco de dados')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT materia, COUNT(*) as total FROM questoes GROUP BY materia ORDER BY materia')
        materias_db = cursor.fetchall()
        conn.close()
        
        materias = [{'nome': row['materia'], 'total': row['total']} for row in materias_db]
        debug_log(f'📚 Matérias carregadas: {len(materias)}')
        
        if not materias:
            debug_log('⚠️  Nenhuma matéria encontrada')
            return render_template('error.html', mensagem='Nenhuma matéria disponível')
        
        return render_template('simulado.html', materias=materias)
        
    except Exception as e:
        debug_log(f'❌ ERRO NO SIMULADO: {e}')
        return render_template('error.html', mensagem=f'Erro: {str(e)}')

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    debug_log('🚀 Recebendo requisição para iniciar simulado')
    
    try:
        data = request.get_json()
        if not data:
            debug_log('❌ Dados JSON não recebidos')
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        quantidade = int(data.get('quantidade', 10))
        materias_selecionadas = data.get('materias', [])
        configs = data.get('configs', {})
        
        debug_log(f'📊 Configuração recebida: {quantidade} questões, {len(materias_selecionadas)} matérias')
        debug_log(f'🎛️  Configs: {configs}')
        
        # Validações
        if quantidade < 1 or quantidade > 100:
            debug_log(f'❌ Quantidade inválida: {quantidade}')
            return jsonify({'success': False, 'error': 'Quantidade deve ser entre 1 e 100'}), 400
        
        if not materias_selecionadas:
            debug_log('❌ Nenhuma matéria selecionada')
            return jsonify({'success': False, 'error': 'Selecione pelo menos uma matéria'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar questões
        placeholders = ','.join(['?'] * len(materias_selecionadas))
        query = f'''
            SELECT id FROM questoes 
            WHERE materia IN ({placeholders}) 
            ORDER BY RANDOM() 
            LIMIT ?
        '''
        
        debug_log(f'📋 Executando query: {query}')
        debug_log(f'🔍 Parâmetros: {materias_selecionadas + [quantidade]}')
        
        cursor.execute(query, materias_selecionadas + [quantidade])
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        debug_log(f'📚 Questões encontradas: {len(questao_ids)}')
        
        if not questao_ids:
            debug_log('❌ Nenhuma questão encontrada para os critérios')
            
            # Debug: ver quais matérias existem
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT materia FROM questoes')
            materias_existentes = [row['materia'] for row in cursor.fetchall()]
            conn.close()
            
            debug_log(f'📖 Matérias existentes: {materias_existentes}')
            debug_log(f'🎯 Matérias selecionadas: {materias_selecionadas}')
            
            return jsonify({
                'success': False, 
                'error': f'Nenhuma questão encontrada. Matérias disponíveis: {", ".join(materias_existentes)}'
            }), 404
        
        # Configurar sessão
        session.clear()
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        session['configs'] = configs
        session['inicio_simulado'] = datetime.now().isoformat()
        
        debug_log(f'✅ Simulado configurado com {len(questao_ids)} questões')
        debug_log(f'🔐 Sessão: {dict(session)}')
        
        return jsonify({
            'success': True,
            'total_questoes': len(questao_ids),
            'redirect_url': url_for('questao', numero=1)
        })
        
    except Exception as e:
        debug_log(f'❌ ERRO CRÍTICO: {e}')
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@app.route('/questao/<int:numero>')
def questao(numero):
    debug_log(f'📖 Acessando questão {numero}')
    
    if not session.get('simulado_ativo'):
        debug_log('❌ Sessão de simulado não ativa')
        return redirect(url_for('simulado'))
    
    questao_ids = session.get('questoes_ids', [])
    debug_log(f'📚 IDs das questões: {questao_ids}')
    
    if numero < 1 or numero > len(questao_ids):
        debug_log(f'❌ Número de questão inválido: {numero} (total: {len(questao_ids)})')
        return render_template('error.html', mensagem=f'Questão {numero} não encontrada')
    
    try:
        questao_id = questao_ids[numero-1]
        debug_log(f'🔍 Buscando questão ID: {questao_id}')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
        questao_db = cursor.fetchone()
        conn.close()
        
        if not questao_db:
            debug_log(f'❌ Questão ID {questao_id} não encontrada no banco')
            return render_template('error.html', mensagem='Questão não encontrada')
        
        # Processar questão
        try:
            alternativas = json.loads(questao_db['alternativas'])
        except:
            alternativas = {'A': 'Erro', 'B': 'Erro', 'C': 'Erro', 'D': 'Erro'}
            debug_log('⚠️  Erro ao carregar alternativas JSON')
        
        resposta_usuario = session.get('respostas', {}).get(str(numero))
        configs = session.get('configs', {})
        
        questao_data = {
            'id': questao_db['id'],
            'enunciado': questao_db['enunciado'],
            'materia': questao_db['materia'],
            'alternativas': alternativas,
            'resposta_correta': questao_db['resposta_correta'],
            'explicacao': questao_db['explicacao'],
            'dica': questao_db['dica'] if configs.get('dicasAutomaticas', True) else '',
            'formula': questao_db['formula'] if configs.get('formulasMatematicas', True) else '',
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
        debug_log(f'❌ ERRO NA QUESTÃO {numero}: {e}')
        return render_template('error.html', mensagem=f'Erro: {str(e)}')

@app.route('/api/questao/responder', methods=['POST'])
def responder_questao():
    debug_log('📝 Recebendo resposta de questão')
    
    try:
        if not session.get('simulado_ativo'):
            debug_log('❌ Tentativa de resposta sem simulado ativo')
            return jsonify({'success': False, 'error': 'Simulado não iniciado'}), 400
        
        data = request.get_json()
        if not data:
            debug_log('❌ Dados de resposta não recebidos')
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        debug_log(f'📤 Resposta: questão {questao_numero} = {resposta}')
        
        if not questao_numero or not resposta:
            debug_log('❌ Dados incompletos na resposta')
            return jsonify({'success': False, 'error': 'Número da questão e resposta são obrigatórios'}), 400
        
        if resposta not in ['A', 'B', 'C', 'D']:
            debug_log(f'❌ Resposta inválida: {resposta}')
            return jsonify({'success': False, 'error': 'Resposta inválida'}), 400
        
        # Salvar resposta
        if 'respostas' not in session:
            session['respostas'] = {}
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        debug_log(f'✅ Resposta salva: {dict(session["respostas"])}')
        
        return jsonify({'success': True})
        
    except Exception as e:
        debug_log(f'❌ ERRO AO SALVAR RESPOSTA: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/resultado')
def resultado():
    debug_log('📊 Calculando resultado do simulado')
    
    if not session.get('simulado_ativo'):
        debug_log('❌ Tentativa de ver resultado sem simulado ativo')
        return redirect(url_for('simulado'))
    
    try:
        questao_ids = session.get('questoes_ids', [])
        respostas = session.get('respostas', {})
        
        debug_log(f'📚 Total de questões: {len(questao_ids)}')
        debug_log(f'📝 Respostas dadas: {len(respostas)}')
        
        acertos = 0
        detalhes_questoes = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for i, questao_id in enumerate(questao_ids, 1):
            cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
            questao_db = cursor.fetchone()
            
            if questao_db:
                resposta_usuario = respostas.get(str(i))
                resposta_correta = questao_db['resposta_correta']
                acertou = resposta_usuario == resposta_correta
                
                if acertou:
                    acertos += 1
                
                try:
                    alternativas = json.loads(questao_db['alternativas'])
                except:
                    alternativas = {'A': 'N/A', 'B': 'N/A', 'C': 'N/A', 'D': 'N/A'}
                
                detalhes_questoes.append({
                    'numero': i,
                    'enunciado': questao_db['enunciado'],
                    'materia': questao_db['materia'],
                    'resposta_usuario': resposta_usuario,
                    'resposta_correta': resposta_correta,
                    'acertou': acertou,
                    'explicacao': questao_db['explicacao'],
                    'alternativas': alternativas,
                    'dificuldade': questao_db['dificuldade']
                })
        
        conn.close()
        
        total_questoes = len(questao_ids)
        porcentagem_acertos = (acertos / total_questoes) * 100 if total_questoes > 0 else 0
        
        debug_log(f'🎯 Resultado: {acertos}/{total_questoes} = {porcentagem_acertos:.1f}%')
        
        # Limpar sessão
        session.clear()
        debug_log('✅ Sessão limpa após resultado')
        
        return render_template('resultado.html',
                             total_questoes=total_questoes,
                             acertos=acertos,
                             erros=total_questoes - acertos,
                             porcentagem=porcentagem_acertos,
                             tempo_minutos=5.0,  # Placeholder
                             desempenho='Bom' if porcentagem_acertos >= 70 else 'Regular',
                             cor_desempenho='success' if porcentagem_acertos >= 70 else 'warning',
                             detalhes_questoes=detalhes_questoes)
        
    except Exception as e:
        debug_log(f'❌ ERRO NO RESULTADO: {e}')
        return render_template('error.html', mensagem=f'Erro: {str(e)}')

@app.route('/redacao')
def redacao():
    debug_log('📝 Acessando página de redação')
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    debug_log('📈 Acessando dashboard')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM questoes')
        total_questoes = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(DISTINCT materia) as total FROM questoes')
        total_materias = cursor.fetchone()['total']
        
        cursor.execute('SELECT materia, COUNT(*) as total FROM questoes GROUP BY materia ORDER BY total DESC LIMIT 5')
        top_materias = cursor.fetchall()
        
        conn.close()
        
        debug_log(f'📊 Dashboard: {total_questoes} questões, {total_materias} matérias')
        
        return render_template('dashboard.html',
                             total_questoes=total_questoes,
                             total_materias=total_materias,
                             total_simulados=0,
                             top_materias=top_materias,
                             historico=[])
        
    except Exception as e:
        debug_log(f'❌ ERRO NO DASHBOARD: {e}')
        return render_template('error.html', mensagem=f'Erro: {str(e)}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_log(f'🚀 Iniciando servidor na porta {port}')
    app.run(host='0.0.0.0', port=port, debug=False)
