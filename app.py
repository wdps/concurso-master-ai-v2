from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
from datetime import datetime, timedelta
import logging
import os
import csv

<<<<<<< HEAD
# Configuração do logging
=======
# ConfiguraÃ§Ã£o do logging
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_secret_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

<<<<<<< HEAD
# Configuração do banco de dados
DATABASE = 'concurso.db'

def get_db_connection():
    """Cria conexão com o banco de dados"""
=======
# ConfiguraÃ§Ã£o do banco de dados
DATABASE = 'concurso.db'

def get_db_connection():
    """Cria conexÃ£o com o banco de dados"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar com o banco: {e}")
        return None

def criar_tabelas_se_necessario():
<<<<<<< HEAD
    """Cria as tabelas necessárias se não existirem"""
=======
    """Cria as tabelas necessÃ¡rias se nÃ£o existirem"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
<<<<<<< HEAD
        # Tabela de questões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questões (
=======
        # Tabela de questÃµes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questÃµes (
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT NOT NULL,
                materia TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT,
<<<<<<< HEAD
                dificuldade TEXT DEFAULT 'Média',
=======
                dificuldade TEXT DEFAULT 'MÃ©dia',
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                tempo_estimado INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
<<<<<<< HEAD
        # Tabela de histórico de simulados
=======
        # Tabela de histÃ³rico de simulados
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_simulados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                relatorio TEXT NOT NULL,
                data_fim TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo_simulado TEXT DEFAULT 'Personalizado',
                quantidade_questoes INTEGER,
                materias_selecionadas TEXT
            )
        ''')
        
        conn.commit()
<<<<<<< HEAD
        logger.info("? Tabelas verificadas/criadas com sucesso!")
=======
        logger.info("âœ… Tabelas verificadas/criadas com sucesso!")
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        return False
    finally:
        conn.close()

def carregar_questoes_csv():
<<<<<<< HEAD
    """Carrega questões do CSV para o banco de dados usando csv nativo"""
    if not os.path.exists('questoes.csv'):
        logger.warning("? Arquivo questoes.csv não encontrado")
        # Criar algumas questões de exemplo
=======
    """Carrega questÃµes do CSV para o banco de dados usando csv nativo"""
    if not os.path.exists('questoes.csv'):
        logger.warning("âŒ Arquivo questoes.csv nÃ£o encontrado")
        # Criar algumas questÃµes de exemplo
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        criar_questoes_exemplo()
        return True
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
<<<<<<< HEAD
            questões_carregadas = 0
            
            for row in csv_reader:
                try:
                    # Criar dicionário de alternativas
=======
            questÃµes_carregadas = 0
            
            for row in csv_reader:
                try:
                    # Criar dicionÃ¡rio de alternativas
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                    alternativas_dict = {}
                    for letra in ['A', 'B', 'C', 'D', 'E']:
                        if letra in row and row[letra] and row[letra].strip():
                            alternativas_dict[letra] = row[letra].strip()
                    
<<<<<<< HEAD
                    # Se não encontrou alternativas, criar padrão
=======
                    # Se nÃ£o encontrou alternativas, criar padrÃ£o
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                    if not alternativas_dict:
                        alternativas_dict = {
                            'A': 'Alternativa A',
                            'B': 'Alternativa B', 
                            'C': 'Alternativa C',
                            'D': 'Alternativa D'
                        }
                    
<<<<<<< HEAD
                    # Inserir questão
                    cursor.execute('''
                        INSERT OR IGNORE INTO questões 
                        (enunciado, materia, alternativas, resposta_correta, explicacao)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row.get('enunciado', 'Enunciado não disponível'),
                        row.get('materia', 'Geral'),
                        json.dumps(alternativas_dict),
                        row.get('resposta_correta', 'A'),
                        row.get('explicacao', 'Explicação não disponível')
                    ))
                    
                    if cursor.rowcount > 0:
                        questões_carregadas += 1
=======
                    # Inserir questÃ£o
                    cursor.execute('''
                        INSERT OR IGNORE INTO questÃµes 
                        (enunciado, materia, alternativas, resposta_correta, explicacao)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row.get('enunciado', 'Enunciado nÃ£o disponÃ­vel'),
                        row.get('materia', 'Geral'),
                        json.dumps(alternativas_dict),
                        row.get('resposta_correta', 'A'),
                        row.get('explicacao', 'ExplicaÃ§Ã£o nÃ£o disponÃ­vel')
                    ))
                    
                    if cursor.rowcount > 0:
                        questÃµes_carregadas += 1
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                        
                except Exception as e:
                    logger.error(f"Erro ao processar linha do CSV: {e}")
                    continue
        
        conn.commit()
        conn.close()
<<<<<<< HEAD
        logger.info(f"? {questões_carregadas} questões carregadas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"? Erro ao carregar questões do CSV: {e}")
        # Criar questões de exemplo em caso de erro
=======
        logger.info(f"âœ… {questÃµes_carregadas} questÃµes carregadas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"âŒ Erro ao carregar questÃµes do CSV: {e}")
        # Criar questÃµes de exemplo em caso de erro
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        criar_questoes_exemplo()
        return True

def criar_questoes_exemplo():
<<<<<<< HEAD
    """Cria questões de exemplo se o CSV não existir ou falhar"""
=======
    """Cria questÃµes de exemplo se o CSV nÃ£o existir ou falhar"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
<<<<<<< HEAD
        questões_exemplo = [
            {
                'enunciado': 'Qual é a capital do Brasil?',
                'materia': 'Geografia',
                'alternativas': {'A': 'Rio de Janeiro', 'B': 'Brasília', 'C': 'São Paulo', 'D': 'Salvador'},
                'resposta_correta': 'B',
                'explicacao': 'Brasília é a capital federal do Brasil desde 1960.'
=======
        questÃµes_exemplo = [
            {
                'enunciado': 'Qual Ã© a capital do Brasil?',
                'materia': 'Geografia',
                'alternativas': {'A': 'Rio de Janeiro', 'B': 'BrasÃ­lia', 'C': 'SÃ£o Paulo', 'D': 'Salvador'},
                'resposta_correta': 'B',
                'explicacao': 'BrasÃ­lia Ã© a capital federal do Brasil desde 1960.'
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
            },
            {
                'enunciado': 'Quem escreveu "Dom Casmurro"?',
                'materia': 'Literatura', 
<<<<<<< HEAD
                'alternativas': {'A': 'Machado de Assis', 'B': 'José de Alencar', 'C': 'Lima Barreto', 'D': 'Graciliano Ramos'},
                'resposta_correta': 'A',
                'explicacao': 'Machado de Assis é o autor de "Dom Casmurro", publicado em 1899.'
            },
            {
                'enunciado': 'Qual é o resultado de 2 + 2?',
                'materia': 'Matemática',
                'alternativas': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
                'resposta_correta': 'B',
                'explicacao': 'A soma de 2 + 2 é igual a 4.'
=======
                'alternativas': {'A': 'Machado de Assis', 'B': 'JosÃ© de Alencar', 'C': 'Lima Barreto', 'D': 'Graciliano Ramos'},
                'resposta_correta': 'A',
                'explicacao': 'Machado de Assis Ã© o autor de "Dom Casmurro", publicado em 1899.'
            },
            {
                'enunciado': 'Qual Ã© o resultado de 2 + 2?',
                'materia': 'MatemÃ¡tica',
                'alternativas': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
                'resposta_correta': 'B',
                'explicacao': 'A soma de 2 + 2 Ã© igual a 4.'
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
            },
            {
                'enunciado': 'Qual oceano banha o litoral brasileiro?',
                'materia': 'Geografia',
<<<<<<< HEAD
                'alternativas': {'A': 'Oceano Pacífico', 'B': 'Oceano Índico', 'C': 'Oceano Atlântico', 'D': 'Oceano Ártico'},
                'resposta_correta': 'C',
                'explicacao': 'O Brasil é banhado pelo Oceano Atlântico.'
            },
            {
                'enunciado': 'Em que ano o Brasil foi descoberto?',
                'materia': 'História',
                'alternativas': {'A': '1492', 'B': '1500', 'C': '1520', 'D': '1450'},
                'resposta_correta': 'B', 
                'explicacao': 'O Brasil foi descoberto em 1500 por Pedro Álvares Cabral.'
            }
        ]
        
        for questao in questões_exemplo:
            cursor.execute('''
                INSERT OR IGNORE INTO questões 
=======
                'alternativas': {'A': 'Oceano PacÃ­fico', 'B': 'Oceano Ãndico', 'C': 'Oceano AtlÃ¢ntico', 'D': 'Oceano Ãrtico'},
                'resposta_correta': 'C',
                'explicacao': 'O Brasil Ã© banhado pelo Oceano AtlÃ¢ntico.'
            },
            {
                'enunciado': 'Em que ano o Brasil foi descoberto?',
                'materia': 'HistÃ³ria',
                'alternativas': {'A': '1492', 'B': '1500', 'C': '1520', 'D': '1450'},
                'resposta_correta': 'B', 
                'explicacao': 'O Brasil foi descoberto em 1500 por Pedro Ãlvares Cabral.'
            }
        ]
        
        for questao in questÃµes_exemplo:
            cursor.execute('''
                INSERT OR IGNORE INTO questÃµes 
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                (enunciado, materia, alternativas, resposta_correta, explicacao)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                questao['enunciado'],
                questao['materia'],
                json.dumps(questao['alternativas']),
                questao['resposta_correta'],
                questao['explicacao']
            ))
        
        conn.commit()
        conn.close()
<<<<<<< HEAD
        logger.info("? 5 questões de exemplo criadas com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao criar questões exemplo: {e}")
=======
        logger.info("âœ… 5 questÃµes de exemplo criadas com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao criar questÃµes exemplo: {e}")
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8

# Rotas principais
@app.route('/')
def index():
<<<<<<< HEAD
    """Página inicial"""
=======
    """PÃ¡gina inicial"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    return render_template('index.html')

@app.route('/simulado')
def simulado():
<<<<<<< HEAD
    """Página de configuração do simulado"""
=======
    """PÃ¡gina de configuraÃ§Ã£o do simulado"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    conn = get_db_connection()
    if not conn:
        return render_template('simulado.html', materias=[])
    
    try:
        cursor = conn.cursor()
<<<<<<< HEAD
        cursor.execute("SELECT DISTINCT materia FROM questões WHERE materia IS NOT NULL AND materia != ''")
=======
        cursor.execute("SELECT DISTINCT materia FROM questÃµes WHERE materia IS NOT NULL AND materia != ''")
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        
        return render_template('simulado.html', materias=materias)
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"Erro ao carregar matérias: {e}")
=======
        logger.error(f"Erro ao carregar matÃ©rias: {e}")
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        return render_template('simulado.html', materias=[])

@app.route('/redacao')
def redacao():
<<<<<<< HEAD
    """Página de redação"""
=======
    """PÃ¡gina de redaÃ§Ã£o"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard profissional"""
    return render_template('dashboard.html')

# API Routes
@app.route('/api/questoes/random')
def get_questoes_random():
<<<<<<< HEAD
    """API para obter questões aleatórias"""
=======
    """API para obter questÃµes aleatÃ³rias"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    try:
        quantidade = int(request.args.get('quantidade', 10))
        materias = request.args.getlist('materias') or []
        
        conn = get_db_connection()
        if not conn:
<<<<<<< HEAD
            return jsonify({'error': 'Erro de conexão com o banco'}), 500
        
        cursor = conn.cursor()
        
        query = "SELECT * FROM questões WHERE 1=1"
=======
            return jsonify({'error': 'Erro de conexÃ£o com o banco'}), 500
        
        cursor = conn.cursor()
        
        query = "SELECT * FROM questÃµes WHERE 1=1"
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND materia IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade)
        
        cursor.execute(query, params)
<<<<<<< HEAD
        questões = cursor.fetchall()
        conn.close()
        
        questões_formatadas = []
        for questao in questões:
=======
        questÃµes = cursor.fetchall()
        conn.close()
        
        questÃµes_formatadas = []
        for questao in questÃµes:
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
            try:
                alternativas = json.loads(questao['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
<<<<<<< HEAD
            questões_formatadas.append({
=======
            questÃµes_formatadas.append({
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                'id': questao['id'],
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'alternativas': alternativas,
                'resposta_correta': questao['resposta_correta'],
                'explicacao': questao['explicacao'],
<<<<<<< HEAD
                'dificuldade': questao.get('dificuldade', 'Média')
            })
        
        return jsonify({'questoes': questões_formatadas})
=======
                'dificuldade': questao.get('dificuldade', 'MÃ©dia')
            })
        
        return jsonify({'questoes': questÃµes_formatadas})
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        
    except Exception as e:
        logger.error(f"Erro em /api/questoes/random: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    """Inicia um novo simulado"""
    try:
        data = request.get_json()
        quantidade = data.get('quantidade', 10)
        materias = data.get('materias', [])
        tempo_por_questao = data.get('tempo_por_questao', 60)
        
<<<<<<< HEAD
        # Buscar questões
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão'}), 500
        
        cursor = conn.cursor()
        
        query = "SELECT * FROM questões WHERE 1=1"
=======
        # Buscar questÃµes
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexÃ£o'}), 500
        
        cursor = conn.cursor()
        
        query = "SELECT * FROM questÃµes WHERE 1=1"
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND materia IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade)
        
        cursor.execute(query, params)
<<<<<<< HEAD
        questões_db = cursor.fetchall()
        conn.close()
        
        if not questões_db:
            return jsonify({'error': 'Nenhuma questão encontrada com os filtros selecionados'}), 404
        
        # Formatar questões
        questões_formatadas = []
        for questao in questões_db:
=======
        questÃµes_db = cursor.fetchall()
        conn.close()
        
        if not questÃµes_db:
            return jsonify({'error': 'Nenhuma questÃ£o encontrada com os filtros selecionados'}), 404
        
        # Formatar questÃµes
        questÃµes_formatadas = []
        for questao in questÃµes_db:
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
            try:
                alternativas = json.loads(questao['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
<<<<<<< HEAD
            questões_formatadas.append({
=======
            questÃµes_formatadas.append({
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                'id': questao['id'],
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'alternativas': alternativas,
                'resposta_correta': questao['resposta_correta'],
                'explicacao': questao['explicacao'],
<<<<<<< HEAD
                'dificuldade': questao.get('dificuldade', 'Média')
            })
        
        # Iniciar sessão do simulado
        session['simulado_ativo'] = True
        session['questoes_simulado'] = questões_formatadas
=======
                'dificuldade': questao.get('dificuldade', 'MÃ©dia')
            })
        
        # Iniciar sessÃ£o do simulado
        session['simulado_ativo'] = True
        session['questoes_simulado'] = questÃµes_formatadas
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        session['respostas_usuario'] = {}
        session['tempo_inicio'] = datetime.now().isoformat()
        session['config_simulado'] = {
            'quantidade': quantidade,
            'materias': materias,
            'tempo_por_questao': tempo_por_questao
        }
        
        return jsonify({
            'success': True,
<<<<<<< HEAD
            'total_questoes': len(questões_formatadas),
=======
            'total_questoes': len(questÃµes_formatadas),
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
            'tempo_estimado': quantidade * tempo_por_questao
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/simulado/iniciar: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/questao/<int:questao_id>')
def get_questao_simulado(questao_id):
<<<<<<< HEAD
    """Obtém uma questão específica do simulado atual"""
    if not session.get('simulado_ativo'):
        return jsonify({'error': 'Nenhum simulado ativo'}), 400
    
    questões = session.get('questoes_simulado', [])
    questao = next((q for q in questões if q['id'] == questao_id), None)
    
    if not questao:
        return jsonify({'error': 'Questão não encontrada'}), 404
=======
    """ObtÃ©m uma questÃ£o especÃ­fica do simulado atual"""
    if not session.get('simulado_ativo'):
        return jsonify({'error': 'Nenhum simulado ativo'}), 400
    
    questÃµes = session.get('questoes_simulado', [])
    questao = next((q for q in questÃµes if q['id'] == questao_id), None)
    
    if not questao:
        return jsonify({'error': 'QuestÃ£o nÃ£o encontrada'}), 404
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    
    return jsonify({'questao': questao})

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
<<<<<<< HEAD
    """Registra resposta do usuário"""
=======
    """Registra resposta do usuÃ¡rio"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    try:
        data = request.get_json()
        questao_id = data.get('questao_id')
        resposta = data.get('resposta')
        
        if not session.get('simulado_ativo'):
            return jsonify({'error': 'Nenhum simulado ativo'}), 400
        
        # Registrar resposta
        respostas = session.get('respostas_usuario', {})
        respostas[str(questao_id)] = {
            'resposta': resposta,
            'timestamp': datetime.now().isoformat()
        }
        session['respostas_usuario'] = respostas
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Erro em /api/simulado/responder: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/finalizar', methods=['POST'])
def finalizar_simulado():
<<<<<<< HEAD
    """Finaliza o simulado e gera relatório"""
=======
    """Finaliza o simulado e gera relatÃ³rio"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'error': 'Nenhum simulado ativo'}), 400
        
<<<<<<< HEAD
        questões = session.get('questoes_simulado', [])
=======
        questÃµes = session.get('questoes_simulado', [])
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        respostas = session.get('respostas_usuario', {})
        tempo_inicio = datetime.fromisoformat(session.get('tempo_inicio', datetime.now().isoformat()))
        tempo_fim = datetime.now()
        
<<<<<<< HEAD
        # Calcular estatísticas
        estatisticas = calcular_estatisticas_simulado(questões, respostas, tempo_inicio, tempo_fim)
        
        # Salvar no histórico
        salvar_historico_simulado(estatisticas, session.get('config_simulado', {}))
        
        # Limpar sessão
=======
        # Calcular estatÃ­sticas
        estatisticas = calcular_estatisticas_simulado(questÃµes, respostas, tempo_inicio, tempo_fim)
        
        # Salvar no histÃ³rico
        salvar_historico_simulado(estatisticas, session.get('config_simulado', {}))
        
        # Limpar sessÃ£o
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        session.pop('simulado_ativo', None)
        session.pop('questoes_simulado', None)
        session.pop('respostas_usuario', None)
        session.pop('tempo_inicio', None)
        session.pop('config_simulado', None)
        
        return jsonify({
            'success': True,
            'relatorio': estatisticas
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/simulado/finalizar: {e}")
        return jsonify({'error': str(e)}), 500

<<<<<<< HEAD
def calcular_estatisticas_simulado(questões, respostas, tempo_inicio, tempo_fim):
    """Calcula estatísticas detalhadas do simulado"""
    total_questoes = len(questões)
=======
def calcular_estatisticas_simulado(questÃµes, respostas, tempo_inicio, tempo_fim):
    """Calcula estatÃ­sticas detalhadas do simulado"""
    total_questoes = len(questÃµes)
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    acertos = 0
    erros = 0
    nao_respondidas = 0
    
<<<<<<< HEAD
    # Estatísticas por matéria
    stats_por_materia = {}
    
    for questao in questões:
=======
    # EstatÃ­sticas por matÃ©ria
    stats_por_materia = {}
    
    for questao in questÃµes:
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        questao_id = str(questao['id'])
        materia = questao['materia']
        resposta_usuario = respostas.get(questao_id, {}).get('resposta')
        resposta_correta = questao['resposta_correta']
        
<<<<<<< HEAD
        # Inicializar estatísticas da matéria
=======
        # Inicializar estatÃ­sticas da matÃ©ria
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        if materia not in stats_por_materia:
            stats_por_materia[materia] = {'acertos': 0, 'total': 0}
        
        stats_por_materia[materia]['total'] += 1
        
        if resposta_usuario:
            if resposta_usuario == resposta_correta:
                acertos += 1
                stats_por_materia[materia]['acertos'] += 1
            else:
                erros += 1
        else:
            nao_respondidas += 1
    
    # Calcular percentuais
    tempo_total = (tempo_fim - tempo_inicio).total_seconds()
    tempo_medio = tempo_total / total_questoes if total_questoes > 0 else 0
    percentual_acerto = (acertos * 100 / total_questoes) if total_questoes > 0 else 0
    
<<<<<<< HEAD
    # Calcular percentuais por matéria
=======
    # Calcular percentuais por matÃ©ria
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    for materia, stats in stats_por_materia.items():
        stats['percentual'] = (stats['acertos'] * 100 / stats['total']) if stats['total'] > 0 else 0
    
    return {
        'geral': {
            'total_questoes': total_questoes,
            'acertos': acertos,
            'erros': erros,
            'nao_respondidas': nao_respondidas,
            'percentual_acerto': round(percentual_acerto, 2),
            'tempo_total_minutos': round(tempo_total / 60, 2),
            'tempo_medio_questao': round(tempo_medio, 2),
            'questoes_respondidas': acertos + erros
        },
        'por_materia': stats_por_materia,
        'tempo_inicio': tempo_inicio.isoformat(),
        'tempo_fim': tempo_fim.isoformat()
    }

def salvar_historico_simulado(estatisticas, config):
<<<<<<< HEAD
    """Salva o relatório do simulado no histórico"""
=======
    """Salva o relatÃ³rio do simulado no histÃ³rico"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO historico_simulados 
            (relatorio, data_fim, tipo_simulado, quantidade_questoes, materias_selecionadas)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            json.dumps(estatisticas, ensure_ascii=False),
            datetime.now().isoformat(),
            config.get('tipo_simulado', 'Personalizado'),
            config.get('quantidade', 0),
            json.dumps(config.get('materias', []))
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"Erro ao salvar histórico: {e}")
=======
        logger.error(f"Erro ao salvar histÃ³rico: {e}")
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        return False

@app.route('/api/dashboard/estatisticas')
def get_estatisticas_dashboard():
<<<<<<< HEAD
    """Estatísticas para o dashboard profissional"""
=======
    """EstatÃ­sticas para o dashboard profissional"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    criar_tabelas_se_necessario()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"estatisticas": {}})
    
    try:
        cursor = conn.cursor()
        
<<<<<<< HEAD
        # 1. Total de questões no banco
        cursor.execute("SELECT COUNT(*) as total FROM questões")
        total_questoes_banco = cursor.fetchone()['total']
        
        # 2. Histórico de simulados
=======
        # 1. Total de questÃµes no banco
        cursor.execute("SELECT COUNT(*) as total FROM questÃµes")
        total_questoes_banco = cursor.fetchone()['total']
        
        # 2. HistÃ³rico de simulados
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        cursor.execute("SELECT relatorio, data_fim FROM historico_simulados ORDER BY data_fim ASC")
        todos_relatorios = cursor.fetchall()
        
        # 3. Processar dados agregados
        historico_evolucao = []
        global_stats_materia = {}
        tempo_total_estudo = 0
        total_questoes_respondidas = 0
        
        for row in todos_relatorios:
            try:
                relatorio = json.loads(row['relatorio'])
                data_fim_str = row['data_fim']
                
<<<<<<< HEAD
                # Para gráfico de evolução
=======
                # Para grÃ¡fico de evoluÃ§Ã£o
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                try:
                    data_obj = datetime.fromisoformat(data_fim_str.replace('Z', '+00:00'))
                except:
                    data_obj = datetime.fromisoformat(data_fim_str)
                    
                historico_evolucao.append({
                    'data': data_obj.strftime('%d/%m'),
                    'percentual': relatorio['geral']['percentual_acerto']
                })
                
                # Para stats de KPI
                tempo_total_estudo += relatorio['geral'].get('tempo_total_minutos', 0)
                total_questoes_respondidas += relatorio['geral'].get('questoes_respondidas', 0)
                
<<<<<<< HEAD
                # Para gráfico de desempenho por matéria
=======
                # Para grÃ¡fico de desempenho por matÃ©ria
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
                for materia, stats in relatorio.get('por_materia', {}).items():
                    if materia not in global_stats_materia:
                        global_stats_materia[materia] = {'acertos': 0, 'total': 0}
                    global_stats_materia[materia]['acertos'] += stats['acertos']
                    global_stats_materia[materia]['total'] += stats['total']
                    
            except Exception as e:
                logger.error(f"Erro ao processar relatorio: {e}")

<<<<<<< HEAD
        # Calcular percentuais globais por matéria
=======
        # Calcular percentuais globais por matÃ©ria
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        desempenho_global_materia = {}
        for materia, stats in global_stats_materia.items():
            percentual = (stats['acertos'] * 100 / stats['total']) if stats['total'] > 0 else 0
            desempenho_global_materia[materia] = round(percentual, 2)
            
<<<<<<< HEAD
        # 4. Histórico recente
=======
        # 4. HistÃ³rico recente
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        historico_recente_formatado = []
        for row in reversed(todos_relatorios[-10:]): 
            try:
                relatorio = json.loads(row['relatorio'])
                data_fim_str = row['data_fim']
                try:
                    data_obj = datetime.fromisoformat(data_fim_str.replace('Z', '+00:00'))
                except:
                    data_obj = datetime.fromisoformat(data_fim_str)
                    
                historico_recente_formatado.append({
                    'data': data_obj.strftime('%d/%m/%Y %H:%M'),
                    'geral': relatorio['geral']
                })
            except:
                pass

<<<<<<< HEAD
        # 5. Média geral
=======
        # 5. MÃ©dia geral
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
        media_geral = 0
        if historico_evolucao:
            media_geral = sum(h['percentual'] for h in historico_evolucao) / len(historico_evolucao)

        conn.close()
        
        return jsonify({
            "estatisticas": {
                "total_questoes_banco": total_questoes_banco,
                "total_simulados_realizados": len(todos_relatorios),
                "total_questoes_respondidas": total_questoes_respondidas,
                "tempo_total_estudo_min": round(tempo_total_estudo, 2),
                "media_geral_percentual": round(media_geral, 2),
                "evolucao_desempenho": historico_evolucao,
                "desempenho_global_materia": desempenho_global_materia,
                "historico_recente": historico_recente_formatado
            }
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/dashboard/estatisticas: {e}")
        conn.close()
        return jsonify({"estatisticas": {}})

<<<<<<< HEAD
# Inicialização
@app.before_request
def initialize_app():
    """Inicializa a aplicação"""
=======
# InicializaÃ§Ã£o
@app.before_request
def initialize_app():
    """Inicializa a aplicaÃ§Ã£o"""
>>>>>>> 2c20bceafa64cc4055e58c741f726b7d9baa78d8
    criar_tabelas_se_necessario()
    carregar_questoes_csv()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
