from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
from datetime import datetime, timedelta
import logging
import os
import csv

# Configuracao
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_super_2024_v2'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

DATABASE = 'concurso.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas_se_necessario():
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
            dificuldade TEXT DEFAULT 'Media',
            tempo_estimado INTEGER DEFAULT 60,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temas_redacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT NOT NULL,
            categoria TEXT NOT NULL,
            palavras_chave TEXT,
            dicas TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Tabelas criadas/verificadas!")
    return True

def carregar_dados_iniciais():
    criar_tabelas_se_necessario()
    carregar_questoes_csv()
    carregar_temas_redacao()

def carregar_questoes_csv():
    if not os.path.exists('questoes.csv'):
        criar_questoes_exemplo()
        return True
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                try:
                    alternativas_dict = {}
                    for letra in ['A', 'B', 'C', 'D', 'E']:
                        if letra in row and row[letra] and row[letra].strip():
                            alternativas_dict[letra] = row[letra].strip()
                    
                    if not alternativas_dict:
                        alternativas_dict = {
                            'A': 'Alternativa A', 'B': 'Alternativa B', 
                            'C': 'Alternativa C', 'D': 'Alternativa D'
                        }
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO questoes 
                        (enunciado, materia, alternativas, resposta_correta, explicacao)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row.get('enunciado', ''),
                        row.get('materia', 'Geral'),
                        json.dumps(alternativas_dict),
                        row.get('resposta_correta', 'A'),
                        row.get('explicacao', 'Explicacao nao disponivel.')
                    ))
                    
                except Exception as e:
                    continue
        
        conn.commit()
        conn.close()
        logger.info("Questoes carregadas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao carregar questoes: {e}")
        criar_questoes_exemplo()
        return True

def carregar_temas_redacao():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    temas = [
        {
            'tema': 'Os impactos da inteligencia artificial no mercado de trabalho',
            'categoria': 'Tecnologia e Sociedade',
            'palavras_chave': 'IA, automacao, emprego, qualificacao',
            'dicas': 'Aborde tanto os beneficios quanto os desafios. Discuta a necessidade de requalificacao profissional.'
        },
        {
            'tema': 'Desafios da educacao publica no Brasil pos-pandemia',
            'categoria': 'Educacao',
            'palavras_chave': 'educacao publica, desigualdade, tecnologia, evasao escolar',
            'dicas': 'Foque nas desigualdades educacionais agravadas pela pandemia e proponha solucoes inovadoras.'
        }
    ]
    
    for tema in temas:
        cursor.execute('''
            INSERT OR IGNORE INTO temas_redacao 
            (tema, categoria, palavras_chave, dicas)
            VALUES (?, ?, ?, ?)
        ''', (
            tema['tema'],
            tema['categoria'],
            tema['palavras_chave'],
            tema['dicas']
        ))
    
    conn.commit()
    conn.close()
    logger.info("Temas de redacao carregados!")

def criar_questoes_exemplo():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    questoes = [
        {
            'enunciado': 'Qual e a capital do Brasil?',
            'materia': 'Geografia',
            'alternativas': {
                'A': 'Rio de Janeiro', 
                'B': 'Brasilia', 
                'C': 'Sao Paulo', 
                'D': 'Salvador'
            },
            'resposta_correta': 'B',
            'explicacao': '✅ CORRETO: Brasilia e a capital federal do Brasil desde 1960, projetada por Lucio Costa e Oscar Niemeyer para ser a sede do governo.'
        },
        {
            'enunciado': 'Quem escreveu "Dom Casmurro"?',
            'materia': 'Literatura',
            'alternativas': {
                'A': 'Machado de Assis', 
                'B': 'Jose de Alencar', 
                'C': 'Lima Barreto', 
                'D': 'Graciliano Ramos'
            },
            'resposta_correta': 'A',
            'explicacao': '✅ CORRETO: Machado de Assis, maior escritor brasileiro, publicou "Dom Casmurro" em 1899. A obra e marcada pela duvida sobre a traicao de Capitu.'
        }
    ]
    
    for questao in questoes:
        cursor.execute('''
            INSERT OR IGNORE INTO questoes 
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
    logger.info("Questoes exemplo criadas!")

# ========== ROTAS PRINCIPAIS ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT materia FROM questoes")
    materias = [row['materia'] for row in cursor.fetchall()]
    conn.close()
    return render_template('simulado.html', materias=materias)

@app.route('/redacao')
def redacao():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM temas_redacao ORDER BY RANDOM() LIMIT 1")
    tema = cursor.fetchone()
    conn.close()
    
    tema_dict = dict(tema) if tema else {
        'tema': 'Os desafios da educacao no seculo XXI',
        'categoria': 'Educacao',
        'palavras_chave': 'tecnologia, metodologias, aprendizagem',
        'dicas': 'Aborde as novas tecnologias e metodologias de ensino.'
    }
    
    return render_template('redacao.html', tema=tema_dict)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ========== API ==========
@app.route('/api/questoes/random')
def get_questoes_random():
    try:
        quantidade = int(request.args.get('quantidade', 10))
        materias = request.args.getlist('materias')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM questoes WHERE 1=1"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND materia IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade)
        
        cursor.execute(query, params)
        questoes_db = cursor.fetchall()
        conn.close()
        
        questoes = []
        for q in questoes_db:
            try:
                alternativas = json.loads(q['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
            questoes.append({
                'id': q['id'],
                'enunciado': q['enunciado'],
                'materia': q['materia'],
                'alternativas': alternativas,
                'resposta_correta': q['resposta_correta'],
                'explicacao': q['explicacao'],
                'dificuldade': q.get('dificuldade', 'Media')
            })
        
        return jsonify({'questoes': questoes})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    try:
        data = request.get_json()
        quantidade = data.get('quantidade', 5)
        materias = data.get('materias', [])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM questoes WHERE 1=1"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND materia IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade)
        
        cursor.execute(query, params)
        questoes_db = cursor.fetchall()
        conn.close()
        
        if not questoes_db:
            return jsonify({'error': 'Nenhuma questao encontrada com os filtros selecionados'}), 404
        
        questoes = []
        for q in questoes_db:
            try:
                alternativas = json.loads(q['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
            questoes.append({
                'id': q['id'],
                'enunciado': q['enunciado'],
                'materia': q['materia'],
                'alternativas': alternativas,
                'resposta_correta': q['resposta_correta'],
                'explicacao': q['explicacao'],
                'dificuldade': q.get('dificuldade', 'Media')
            })
        
        session['simulado_ativo'] = True
        session['questoes'] = questoes
        session['respostas'] = {}
        session['inicio'] = datetime.now().isoformat()
        session['config'] = {
            'quantidade': quantidade,
            'materias': materias
        }
        
        return jsonify({
            'success': True,
            'total': len(questoes),
            'questoes_ids': [q['id'] for q in questoes]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== INICIALIZACAO ==========
@app.before_request
def initialize():
    carregar_dados_iniciais()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
