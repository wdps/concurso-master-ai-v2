from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'concurso_master_pro_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuração do banco
DATABASE = 'concurso.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    '''Inicializa o banco de dados de forma robusta'''
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabela de questões
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
                dificuldade TEXT DEFAULT 'Média',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de resultados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resultados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_questoes INTEGER,
                acertos INTEGER,
                porcentagem REAL,
                tempo_gasto REAL,
                data_simulado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                configs TEXT
            )
        ''')
        
        # Verificar se existem questões
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print('📥 Carregando questões do CSV...')
            if not load_questions_from_csv():
                print('❌ Erro ao carregar questões do CSV')
                # Criar questões de exemplo
                create_sample_questions()
        else:
            print(f'✅ {count} questões no banco')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Erro crítico no banco: {e}')
        return False

def load_questions_from_csv():
    '''Carrega questões do CSV de forma robusta'''
    if not os.path.exists('questoes.csv'):
        print('❌ Arquivo questoes.csv não encontrado')
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            questions_loaded = 0
            
            for row in csv_reader:
                try:
                    enunciado = row.get('enunciado', '').strip()
                    materia = row.get('disciplina', 'Geral').strip()
                    
                    if not enunciado:
                        continue
                    
                    # Alternativas
                    alternativas = {
                        'A': row.get('alt_a', 'Alternativa A').strip(),
                        'B': row.get('alt_b', 'Alternativa B').strip(),
                        'C': row.get('alt_c', 'Alternativa C').strip(),
                        'D': row.get('alt_d', 'Alternativa D').strip()
                    }
                    
                    resposta_correta = row.get('gabarito', 'A').strip().upper()
                    
                    # Sistema de dicas inteligentes
                    dica = generate_intelligent_hint(materia, enunciado)
                    formula = generate_relevant_formula(materia)
                    
                    # Explicação detalhada
                    explicacao_parts = []
                    if row.get('just_a'): explicacao_parts.append(f"A: {row['just_a']}")
                    if row.get('just_b'): explicacao_parts.append(f"B: {row['just_b']}")
                    if row.get('just_c'): explicacao_parts.append(f"C: {row['just_c']}")
                    if row.get('just_d'): explicacao_parts.append(f"D: {row['just_d']}")
                    if row.get('dica_interpretacao'): explicacao_parts.append(f"💡 {row['dica_interpretacao']}")
                    
                    explicacao = ' | '.join(explicacao_parts) if explicacao_parts else 'Explicação detalhada disponível após resposta'
                    
                    # Inserir questão
                    cursor.execute('''
                        INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (enunciado, materia, json.dumps(alternativas), resposta_correta, explicacao, dica, formula))
                    
                    questions_loaded += 1
                    
                except Exception as e:
                    print(f'⚠️ Erro ao processar linha do CSV: {e}')
                    continue
        
        conn.commit()
        conn.close()
        print(f'✅ {questions_loaded} questões carregadas do CSV')
        return True
        
    except Exception as e:
        print(f'❌ Erro crítico ao carregar CSV: {e}')
        return False

def create_sample_questions():
    '''Cria questões de exemplo se o CSV não existir'''
    try:
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
                'explicacao': 'Operação básica de adição.',
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
        print('✅ Questões de exemplo criadas')
        return True
        
    except Exception as e:
        print(f'❌ Erro ao criar questões de exemplo: {e}')
        return False

def generate_intelligent_hint(materia, enunciado):
    '''Gera dicas inteligentes baseadas no contexto'''
    hints = {
        'Matemática': [
            "🔍 Analise a operação matemática envolvida",
            "📐 Verifique se há fórmulas aplicáveis",
            "🧮 Considere as propriedades matemáticas",
            "💡 Quebre o problema em etapas menores"
        ],
        'Língua Portuguesa': [
            "📖 Observe a estrutura gramatical",
            "🔍 Analise o contexto da frase",
            "✍️ Verifique concordância e regência",
            "💡 Identifique a classe gramatical das palavras"
        ],
        'Raciocínio Lógico': [
            "🎯 Identifique padrões e sequências",
            "🔍 Use o processo de eliminação",
            "🧩 Divida o problema em partes",
            "💡 Considere todas as possibilidades"
        ],
        'Direito Constitucional': [
            "⚖️ Lembre-se dos princípios fundamentais",
            "📚 Consulte a hierarquia das normas",
            "🔍 Analise a competência envolvida",
            "💡 Pense na aplicação prática do dispositivo"
        ],
        'Direito Administrativo': [
            "🏛️ Revise os princípios da administração",
            "⚖️ Considere a legalidade do ato",
            "🔍 Verifique a competência do agente",
            "💡 Analise os requisitos de validade"
        ],
        'Geografia': [
            "🌍 Considere aspectos físicos e humanos",
            "🗺️ Pense na localização geográfica",
            "🔍 Analise relações espaciais",
            "💡 Relacione com contextos atuais"
        ]
    }
    
    # Encontrar dica mais relevante
    for key, hint_list in hints.items():
        if key.lower() in materia.lower():
            return random.choice(hint_list)
    
    return "💡 Leia atentamente o enunciado e analise cada alternativa com cuidado"

def generate_relevant_formula(materia):
    '''Gera fórmulas relevantes para a matéria'''
    formulas = {
        'Matemática': [
            "Área do círculo: A = πr²",
            "Teorema de Pitágoras: a² + b² = c²",
            "Regra de três: a/b = c/d ⇒ a = (b × c)/d",
            "Juros simples: J = C × i × t",
            "Progressão Aritmética: aₙ = a₁ + (n-1)r",
            "Progressão Geométrica: aₙ = a₁ × qⁿ⁻¹"
        ],
        'Raciocínio Lógico': [
            "Probabilidade: P(A) = n(A)/n(S)",
            "Princípio Fundamental da Contagem",
            "Permutação Simples: Pₙ = n!",
            "Combinação: C(n,p) = n!/(p!(n-p)!)",
            "Arranjo: A(n,p) = n!/(n-p)!"
        ],
        'Geografia': [
            "Densidade demográfica: D = População/Área",
            "Taxa de crescimento: TC = (Pf - Pi)/Pi × 100",
            "Coordenadas geográficas: Lat/Long",
            "Escala: E = Dmapa/Dreal"
        ]
    }
    
    for key, formula_list in formulas.items():
        if key.lower() in materia.lower():
            return random.choice(formula_list)
    
    return ""

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def index():
    '''Página inicial profissional'''
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    '''Página de configuração do simulado'''
    try:
        if not init_database():
            return render_template('error.html', mensagem='Erro ao inicializar o sistema')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar matérias disponíveis com estatísticas
        cursor.execute('''
            SELECT DISTINCT materia, COUNT(*) as total 
            FROM questoes 
            WHERE materia IS NOT NULL AND materia != '' 
            GROUP BY materia 
            ORDER BY total DESC, materia ASC
        ''')
        materias_db = cursor.fetchall()
        conn.close()
        
        materias = [{'nome': row['materia'], 'total': row['total']} for row in materias_db]
        
        if not materias:
            return render_template('error.html', mensagem='Nenhuma matéria disponível no banco de dados')
        
        return render_template('simulado.html', materias=materias)
        
    except Exception as e:
        print(f'❌ Erro na página de simulado: {e}')
        return render_template('error.html', mensagem='Erro ao carregar configurações do simulado')

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    '''API robusta para iniciar simulado'''
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        quantidade = int(data.get('quantidade', 20))
        materias_selecionadas = data.get('materias', [])
        configs = data.get('configs', {})
        
        # Validações
        if quantidade < 1 or quantidade > 100:
            return jsonify({'success': False, 'error': 'Quantidade deve ser entre 1 e 100'}), 400
        
        if not materias_selecionadas:
            return jsonify({'success': False, 'error': 'Selecione pelo menos uma matéria'}), 400
        
        print(f'🚀 Iniciando simulado: {quantidade} questões, {len(materias_selecionadas)} matérias')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar questões baseado nas matérias selecionadas
        placeholders = ','.join(['?'] * len(materias_selecionadas))
        query = f'''
            SELECT id FROM questoes 
            WHERE materia IN ({placeholders}) 
            ORDER BY RANDOM() 
            LIMIT ?
        '''
        
        cursor.execute(query, materias_selecionadas + [quantidade])
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        if not questao_ids:
            return jsonify({
                'success': False, 
                'error': f'Nenhuma questão encontrada para as matérias selecionadas. Matérias disponíveis: {", ".join(get_available_subjects())}'
            }), 404
        
        # Configurar sessão
        session.clear()
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        session['configs'] = configs
        session['inicio_simulado'] = datetime.now().isoformat()
        session['questao_atual'] = 1
        
        print(f'✅ Simulado configurado com {len(questao_ids)} questões')
        
        return jsonify({
            'success': True,
            'total_questoes': len(questao_ids),
            'redirect_url': url_for('questao', numero=1)
        })
        
    except Exception as e:
        print(f'❌ Erro crítico ao iniciar simulado: {e}')
        return jsonify({
            'success': False, 
            'error': f'Erro interno do sistema: {str(e)}'
        }), 500

def get_available_subjects():
    '''Retorna lista de matérias disponíveis'''
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT materia FROM questoes WHERE materia IS NOT NULL ORDER BY materia')
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        return materias
    except:
        return []

@app.route('/questao/<int:numero>')
def questao(numero):
    '''Página individual da questão'''
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    questao_ids = session.get('questoes_ids', [])
    total_questoes = len(questao_ids)
    
    if numero < 1 or numero > total_questoes:
        return render_template('error.html', mensagem=f'Questão {numero} não encontrada')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_ids[numero-1],))
        questao_db = cursor.fetchone()
        
        if not questao_db:
            return render_template('error.html', mensagem='Questão não encontrada no banco de dados')
        
        # Processar questão
        try:
            alternativas = json.loads(questao_db['alternativas'])
        except:
            alternativas = {'A': 'Erro', 'B': 'Erro', 'C': 'Erro', 'D': 'Erro'}
        
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
        
        conn.close()
        
        return render_template('questao.html',
                             numero=numero,
                             total_questoes=total_questoes,
                             questao=questao_data,
                             resposta_usuario=resposta_usuario,
                             configs=configs,
                             questao_respondida=resposta_usuario is not None)
        
    except Exception as e:
        print(f'❌ Erro ao carregar questão {numero}: {e}')
        return render_template('error.html', mensagem='Erro ao carregar questão')

@app.route('/api/questao/responder', methods=['POST'])
def responder_questao():
    '''API para registrar resposta'''
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'success': False, 'error': 'Simulado não iniciado'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        if not questao_numero or not resposta:
            return jsonify({'success': False, 'error': 'Número da questão e resposta são obrigatórios'}), 400
        
        # Validar resposta
        if resposta not in ['A', 'B', 'C', 'D']:
            return jsonify({'success': False, 'error': 'Resposta inválida'}), 400
        
        # Salvar resposta
        if 'respostas' not in session:
            session['respostas'] = {}
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        print(f'📝 Questão {questao_numero}: resposta "{resposta}" registrada')
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f'❌ Erro ao registrar resposta: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/resultado')
def resultado():
    '''Página de resultados'''
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    try:
        questao_ids = session.get('questoes_ids', [])
        respostas = session.get('respostas', {})
        configs = session.get('configs', {})
        inicio_simulado = datetime.fromisoformat(session.get('inicio_simulado'))
        
        # Calcular resultados
        acertos = 0
        detalhes_questoes = []
        desempenho_por_materia = {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for i, questao_id in enumerate(questao_ids, 1):
            cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
            questao_db = cursor.fetchone()
            
            if questao_db:
                resposta_usuario = respostas.get(str(i))
                resposta_correta = questao_db['resposta_correta']
                acertou = resposta_usuario == resposta_correta
                materia = questao_db['materia']
                
                if acertou:
                    acertos += 1
                
                # Estatísticas por matéria
                if materia not in desempenho_por_materia:
                    desempenho_por_materia[materia] = {'total': 0, 'acertos': 0}
                
                desempenho_por_materia[materia]['total'] += 1
                if acertou:
                    desempenho_por_materia[materia]['acertos'] += 1
                
                # Processar alternativas
                try:
                    alternativas = json.loads(questao_db['alternativas'])
                except:
                    alternativas = {'A': 'N/A', 'B': 'N/A', 'C': 'N/A', 'D': 'N/A'}
                
                detalhes_questoes.append({
                    'numero': i,
                    'enunciado': questao_db['enunciado'],
                    'materia': materia,
                    'resposta_usuario': resposta_usuario,
                    'resposta_correta': resposta_correta,
                    'acertou': acertou,
                    'explicacao': questao_db['explicacao'],
                    'alternativas': alternativas,
                    'dificuldade': questao_db['dificuldade']
                })
        
        # Calcular métricas
        total_questoes = len(questao_ids)
        porcentagem_acertos = (acertos / total_questoes) * 100 if total_questoes > 0 else 0
        tempo_total = (datetime.now() - inicio_simulado).total_seconds()
        
        # Determinar desempenho
        if porcentagem_acertos >= 90:
            desempenho = 'Excelente 🎉'
            cor_desempenho = 'success'
        elif porcentagem_acertos >= 70:
            desempenho = 'Bom 👍'
            cor_desempenho = 'info'
        elif porcentagem_acertos >= 50:
            desempenho = 'Regular 💪'
            cor_desempenho = 'warning'
        else:
            desempenho = 'Precisa melhorar 📚'
            cor_desempenho = 'danger'
        
        # Salvar resultado
        cursor.execute('''
            INSERT INTO resultados (total_questoes, acertos, porcentagem, tempo_gasto, configs)
            VALUES (?, ?, ?, ?, ?)
        ''', (total_questoes, acertos, porcentagem_acertos, tempo_total, json.dumps(configs)))
        conn.commit()
        conn.close()
        
        # Limpar sessão
        session.clear()
        
        return render_template('resultado.html',
                             total_questoes=total_questoes,
                             acertos=acertos,
                             erros=total_questoes - acertos,
                             porcentagem=porcentagem_acertos,
                             tempo_minutos=tempo_total / 60,
                             desempenho=desempenho,
                             cor_desempenho=cor_desempenho,
                             desempenho_por_materia=desempenho_por_materia,
                             detalhes_questoes=detalhes_questoes)
        
    except Exception as e:
        print(f'❌ Erro ao calcular resultados: {e}')
        return render_template('error.html', mensagem='Erro ao processar resultados')

@app.route('/redacao')
def redacao():
    '''Sistema de redação'''
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    '''Dashboard de estatísticas'''
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Estatísticas
        cursor.execute('SELECT COUNT(*) as total FROM questoes')
        total_questoes = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(DISTINCT materia) as total FROM questoes')
        total_materias = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM resultados')
        total_simulados = cursor.fetchone()['total']
        
        # Top matérias
        cursor.execute('SELECT materia, COUNT(*) as total FROM questoes GROUP BY materia ORDER BY total DESC LIMIT 5')
        top_materias = cursor.fetchall()
        
        # Histórico
        cursor.execute('SELECT * FROM resultados ORDER BY data_simulado DESC LIMIT 10')
        historico = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html',
                             total_questoes=total_questoes,
                             total_materias=total_materias,
                             total_simulados=total_simulados,
                             top_materias=top_materias,
                             historico=historico)
        
    except Exception as e:
        print(f'❌ Erro no dashboard: {e}')
        return render_template('error.html', mensagem='Erro ao carregar dashboard')

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('error.html', mensagem='Página não encontrada'), 404

@app.errorhandler(500)
def erro_interno(e):
    return render_template('error.html', mensagem='Erro interno do servidor'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 ConcursoMaster AI Professional - Porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
