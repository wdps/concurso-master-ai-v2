from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
from datetime import datetime, timedelta
import logging
import os
import csv

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_secret_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Configuração do banco de dados
DATABASE = 'concurso.db'

def get_db_connection():
    \"\"\"Cria conexão com o banco de dados\"\"\"
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f\"Erro ao conectar com o banco: {e}\")
        return None

def criar_tabelas_se_necessario():
    \"\"\"Cria as tabelas necessárias se não existirem\"\"\"
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabela de questões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questões (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT NOT NULL,
                materia TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT,
                dificuldade TEXT DEFAULT 'Média',
                tempo_estimado INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de histórico de simulados
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
        logger.info(\"✅ Tabelas verificadas/criadas com sucesso!\")
        return True
        
    except sqlite3.Error as e:
        logger.error(f\"Erro ao criar tabelas: {e}\")
        return False
    finally:
        conn.close()

def carregar_questoes_csv():
    \"\"\"Carrega questões do CSV para o banco de dados\"\"\"
    if not os.path.exists('questoes.csv'):
        logger.warning(\"❌ Arquivo questoes.csv não encontrado\")
        criar_questoes_exemplo()
        return True
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            questões_carregadas = 0
            
            for row in csv_reader:
                try:
                    # Criar dicionário de alternativas
                    alternativas_dict = {}
                    for letra in ['A', 'B', 'C', 'D', 'E']:
                        if letra in row and row[letra] and row[letra].strip():
                            alternativas_dict[letra] = row[letra].strip()
                    
                    # Se não encontrou alternativas, criar padrão
                    if not alternativas_dict:
                        alternativas_dict = {
                            'A': 'Alternativa A',
                            'B': 'Alternativa B', 
                            'C': 'Alternativa C',
                            'D': 'Alternativa D'
                        }
                    
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
                        
                except Exception as e:
                    logger.error(f\"Erro ao processar linha do CSV: {e}\")
                    continue
        
        conn.commit()
        conn.close()
        logger.info(f\"✅ {questões_carregadas} questões carregadas com sucesso!\")
        return True
        
    except Exception as e:
        logger.error(f\"❌ Erro ao carregar questões do CSV: {e}\")
        criar_questoes_exemplo()
        return True

def criar_questoes_exemplo():
    \"\"\"Cria questões de exemplo\"\"\"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        questões_exemplo = [
            {
                'enunciado': 'Qual é a capital do Brasil?',
                'materia': 'Geografia',
                'alternativas': {'A': 'Rio de Janeiro', 'B': 'Brasília', 'C': 'São Paulo', 'D': 'Salvador'},
                'resposta_correta': 'B',
                'explicacao': 'Brasília é a capital federal do Brasil desde 1960.'
            },
            {
                'enunciado': 'Quem escreveu \"Dom Casmurro\"?',
                'materia': 'Literatura', 
                'alternativas': {'A': 'Machado de Assis', 'B': 'José de Alencar', 'C': 'Lima Barreto', 'D': 'Graciliano Ramos'},
                'resposta_correta': 'A',
                'explicacao': 'Machado de Assis é o autor de \"Dom Casmurro\", publicado em 1899.'
            }
        ]
        
        for questao in questões_exemplo:
            cursor.execute('''
                INSERT OR IGNORE INTO questões 
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
        logger.info(\"✅ Questões de exemplo criadas com sucesso!\")
        
    except Exception as e:
        logger.error(f\"Erro ao criar questões exemplo: {e}\")

# Rotas principais
@app.route('/')
def index():
    \"\"\"Página inicial\"\"\"
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    \"\"\"Página de configuração do simulado\"\"\"
    conn = get_db_connection()
    if not conn:
        return render_template('simulado.html', materias=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute(\"SELECT DISTINCT materia FROM questões WHERE materia IS NOT NULL AND materia != ''\")
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        
        return render_template('simulado.html', materias=materias)
    except Exception as e:
        logger.error(f\"Erro ao carregar matérias: {e}\")
        return render_template('simulado.html', materias=[])

@app.route('/redacao')
def redacao():
    \"\"\"Página de redação\"\"\"
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    \"\"\"Dashboard profissional\"\"\"
    return render_template('dashboard.html')

# API Routes
@app.route('/api/questoes/random')
def get_questoes_random():
    \"\"\"API para obter questões aleatórias\"\"\"
    try:
        quantidade = int(request.args.get('quantidade', 10))
        materias = request.args.getlist('materias') or []
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com o banco'}), 500
        
        cursor = conn.cursor()
        
        query = \"SELECT * FROM questões WHERE 1=1\"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f\" AND materia IN ({placeholders})\"
            params.extend(materias)
        
        query += \" ORDER BY RANDOM() LIMIT ?\"
        params.append(quantidade)
        
        cursor.execute(query, params)
        questões = cursor.fetchall()
        conn.close()
        
        questões_formatadas = []
        for questao in questões:
            try:
                alternativas = json.loads(questao['alternativas'])
            except:
                alternativas = {\"A\": \"Alternativa A\", \"B\": \"Alternativa B\", \"C\": \"Alternativa C\", \"D\": \"Alternativa D\"}
            
            questões_formatadas.append({
                'id': questao['id'],
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'alternativas': alternativas,
                'resposta_correta': questao['resposta_correta'],
                'explicacao': questao['explicacao'],
                'dificuldade': questao.get('dificuldade', 'Média')
            })
        
        return jsonify({'questoes': questões_formatadas})
        
    except Exception as e:
        logger.error(f\"Erro em /api/questoes/random: {e}\")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    \"\"\"Inicia um novo simulado\"\"\"
    try:
        data = request.get_json()
        quantidade = data.get('quantidade', 10)
        materias = data.get('materias', [])
        tempo_por_questao = data.get('tempo_por_questao', 60)
        
        # Buscar questões
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão'}), 500
        
        cursor = conn.cursor()
        
        query = \"SELECT * FROM questões WHERE 1=1\"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f\" AND materia IN ({placeholders})\"
            params.extend(materias)
        
        query += \" ORDER BY RANDOM() LIMIT ?\"
        params.append(quantidade)
        
        cursor.execute(query, params)
        questões_db = cursor.fetchall()
        conn.close()
        
        if not questões_db:
            return jsonify({'error': 'Nenhuma questão encontrada com os filtros selecionados'}), 404
        
        # Formatar questões
        questões_formatadas = []
        for questao in questões_db:
            try:
                alternativas = json.loads(questao['alternativas'])
            except:
                alternativas = {\"A\": \"Alternativa A\", \"B\": \"Alternativa B\", \"C\": \"Alternativa C\", \"D\": \"Alternativa D\"}
            
            questões_formatadas.append({
                'id': questao['id'],
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'alternativas': alternativas,
                'resposta_correta': questao['resposta_correta'],
                'explicacao': questao['explicacao'],
                'dificuldade': questao.get('dificuldade', 'Média')
            })
        
        # Iniciar sessão do simulado
        session['simulado_ativo'] = True
        session['questoes_simulado'] = questões_formatadas
        session['respostas_usuario'] = {}
        session['tempo_inicio'] = datetime.now().isoformat()
        session['config_simulado'] = {
            'quantidade': quantidade,
            'materias': materias,
            'tempo_por_questao': tempo_por_questao
        }
        
        return jsonify({
            'success': True,
            'total_questoes': len(questões_formatadas),
            'tempo_estimado': quantidade * tempo_por_questao
        })
        
    except Exception as e:
        logger.error(f\"Erro em /api/simulado/iniciar: {e}\")
        return jsonify({'error': str(e)}), 500

# Inicialização
@app.before_request
def initialize_app():
    \"\"\"Inicializa a aplicação\"\"\"
    criar_tabelas_se_necessario()
    carregar_questoes_csv()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
