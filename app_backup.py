from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
from datetime import datetime, timedelta
import logging
import os
import csv

# Configuração
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
    
    # Tabela de temas de redação
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
                        INSERT OR IGNORE INTO questões 
                        (enunciado, materia, alternativas, resposta_correta, explicacao)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row.get('enunciado', ''),
                        row.get('materia', 'Geral'),
                        json.dumps(alternativas_dict),
                        row.get('resposta_correta', 'A'),
                        row.get('explicacao', 'Explicação não disponível.')
                    ))
                    
                except Exception as e:
                    continue
        
        conn.commit()
        conn.close()
        logger.info("Questões carregadas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao carregar questões: {e}")
        criar_questoes_exemplo()
        return True

def carregar_temas_redacao():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 20 temas diversificados
    temas = [
        {
            'tema': 'Os impactos da inteligência artificial no mercado de trabalho',
            'categoria': 'Tecnologia e Sociedade',
            'palavras_chave': 'IA, automação, emprego, qualificação',
            'dicas': 'Aborde tanto os benefícios quanto os desafios. Discuta a necessidade de requalificação profissional.'
        },
        {
            'tema': 'Desafios da educação pública no Brasil pós-pandemia',
            'categoria': 'Educação',
            'palavras_chave': 'educação pública, desigualdade, tecnologia, evasão escolar',
            'dicas': 'Foque nas desigualdades educacionais agravadas pela pandemia e proponha soluções inovadoras.'
        },
        {
            'tema': 'Sustentabilidade e desenvolvimento econômico: é possível conciliar?',
            'categoria': 'Meio Ambiente',
            'palavras_chave': 'sustentabilidade, desenvolvimento, meio ambiente, economia verde',
            'dicas': 'Apresente exemplos concretos de desenvolvimento sustentável e analise políticas públicas eficazes.'
        },
        {
            'tema': 'A crise habitacional nas grandes cidades brasileiras',
            'categoria': 'Urbanismo',
            'palavras_chave': 'habitação, mobilidade urbana, desigualdade, políticas públicas',
            'dicas': 'Discuta causas estruturais e proponha soluções integradas para moradia digna.'
        },
        {
            'tema': 'Os desafios do sistema de saúde pública no Brasil',
            'categoria': 'Saúde',
            'palavras_chave': 'SUS, saúde pública, acesso, qualidade, financiamento',
            'dicas': 'Aborde desde a prevenção até o tratamento, com foco na universalidade e equidade.'
        },
        {
            'tema': 'A influência das redes sociais na formação da opinião pública',
            'categoria': 'Comunicação',
            'palavras_chave': 'redes sociais, opinião pública, desinformação, democracia',
            'dicas': 'Analise tanto os aspectos positivos quanto os riscos para a democracia e o debate público.'
        },
        {
            'tema': 'Mobilidade urbana e qualidade de vida nas metrópoles',
            'categoria': 'Urbanismo',
            'palavras_chave': 'transporte, trânsito, poluição, planejamento urbano',
            'dicas': 'Proponha soluções integradas que priorizem o transporte público e modos não poluentes.'
        },
        {
            'tema': 'O papel do Brasil no combate às mudanças climáticas',
            'categoria': 'Meio Ambiente',
            'palavras_chave': 'mudanças climáticas, Amazônia, energias renováveis, políticas ambientais',
            'dicas': 'Destaque a importância do Brasil no cenário global e proponha ações concretas.'
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
    logger.info("Temas de redação carregados!")

def criar_questoes_exemplo():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    questões = [
        {
            'enunciado': 'Qual é a capital do Brasil?',
            'materia': 'Geografia',
            'alternativas': {
                'A': 'Rio de Janeiro', 
                'B': 'Brasília', 
                'C': 'São Paulo', 
                'D': 'Salvador'
            },
            'resposta_correta': 'B',
            'explicacao': '✅ CORRETO: Brasília é a capital federal do Brasil desde 1960, projetada por Lúcio Costa e Oscar Niemeyer para ser a sede do governo.'
        },
        {
            'enunciado': 'Quem escreveu "Dom Casmurro"?',
            'materia': 'Literatura',
            'alternativas': {
                'A': 'Machado de Assis', 
                'B': 'José de Alencar', 
                'C': 'Lima Barreto', 
                'D': 'Graciliano Ramos'
            },
            'resposta_correta': 'A',
            'explicacao': '✅ CORRETO: Machado de Assis, maior escritor brasileiro, publicou "Dom Casmurro" em 1899. A obra é marcada pela dúvida sobre a traição de Capitu.'
        },
        {
            'enunciado': 'Qual oceano banha o litoral brasileiro?',
            'materia': 'Geografia',
            'alternativas': {
                'A': 'Oceano Pacífico', 
                'B': 'Oceano Índico', 
                'C': 'Oceano Atlântico', 
                'D': 'Oceano Ártico'
            },
            'resposta_correta': 'C',
            'explicacao': '✅ CORRETO: O Brasil possui mais de 7.000 km de litoral banhado pelo Oceano Atlântico, com grande diversidade de ecossistemas costeiros.'
        },
        {
            'enunciado': 'Em que ano o Brasil foi descoberto?',
            'materia': 'História',
            'alternativas': {
                'A': '1492', 
                'B': '1500', 
                'C': '1520', 
                'D': '1450'
            },
            'resposta_correta': 'B',
            'explicacao': '✅ CORRETO: O Brasil foi oficialmente descoberto em 22 de abril de 1500 pela frota portuguesa comandada por Pedro Álvares Cabral.'
        },
        {
            'enunciado': 'Qual é o maior bioma brasileiro?',
            'materia': 'Geografia',
            'alternativas': {
                'A': 'Mata Atlântica', 
                'B': 'Cerrado', 
                'C': 'Amazônia', 
                'D': 'Caatinga'
            },
            'resposta_correta': 'C',
            'explicacao': '✅ CORRETO: A Amazônia é o maior bioma brasileiro, cobrindo cerca de 49% do território nacional.'
        }
    ]
    
    for questao in questões:
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
    logger.info("Questões exemplo criadas!")

# ========== ROTAS PRINCIPAIS ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT materia FROM questões")
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
        'tema': 'Os desafios da educação no século XXI',
        'categoria': 'Educação',
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
        
        query = "SELECT * FROM questões WHERE 1=1"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND materia IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade)
        
        cursor.execute(query, params)
        questões_db = cursor.fetchall()
        conn.close()
        
        questões = []
        for q in questões_db:
            try:
                alternativas = json.loads(q['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
            questões.append({
                'id': q['id'],
                'enunciado': q['enunciado'],
                'materia': q['materia'],
                'alternativas': alternativas,
                'resposta_correta': q['resposta_correta'],
                'explicacao': q['explicacao'],
                'dificuldade': q.get('dificuldade', 'Média')
            })
        
        return jsonify({'questoes': questões})
        
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
        
        query = "SELECT * FROM questões WHERE 1=1"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND materia IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade)
        
        cursor.execute(query, params)
        questões_db = cursor.fetchall()
        conn.close()
        
        if not questões_db:
            return jsonify({'error': 'Nenhuma questão encontrada com os filtros selecionados'}), 404
        
        questões = []
        for q in questões_db:
            try:
                alternativas = json.loads(q['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
            questões.append({
                'id': q['id'],
                'enunciado': q['enunciado'],
                'materia': q['materia'],
                'alternativas': alternativas,
                'resposta_correta': q['resposta_correta'],
                'explicacao': q['explicacao'],
                'dificuldade': q.get('dificuldade', 'Média')
            })
        
        session['simulado_ativo'] = True
        session['questoes'] = questões
        session['respostas'] = {}
        session['inicio'] = datetime.now().isoformat()
        session['config'] = {
            'quantidade': quantidade,
            'materias': materias
        }
        
        return jsonify({
            'success': True,
            'total': len(questões),
            'questoes_ids': [q['id'] for q in questões]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/questao/<int:questao_id>')
def get_questao(questao_id):
    if not session.get('simulado_ativo'):
        return jsonify({'error': 'Simulado não iniciado'}), 400
    
    questões = session.get('questoes', [])
    questao = next((q for q in questões if q['id'] == questao_id), None)
    
    if not questao:
        return jsonify({'error': 'Questão não encontrada'}), 404
    
    questao_sem_resposta = questao.copy()
    questao_sem_resposta.pop('resposta_correta', None)
    questao_sem_resposta.pop('explicacao', None)
    
    return jsonify({'questao': questao_sem_resposta})

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    try:
        data = request.get_json()
        questao_id = data['questao_id']
        resposta = data['resposta']
        
        if not session.get('simulado_ativo'):
            return jsonify({'error': 'Simulado não iniciado'}), 400
        
        session['respostas'][str(questao_id)] = {
            'resposta': resposta,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/finalizar', methods=['POST'])
def finalizar_simulado():
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'error': 'Simulado não iniciado'}), 400
        
        questões = session['questoes']
        respostas = session['respostas']
        inicio = datetime.fromisoformat(session['inicio'])
        fim = datetime.now()
        
        total = len(questões)
        acertos = 0
        detalhes = []
        
        for questao in questões:
            questao_id = str(questao['id'])
            resposta_usuario = respostas.get(questao_id, {}).get('resposta')
            correta = questao['resposta_correta']
            
            acertou = resposta_usuario == correta
            if acertou:
                acertos += 1
            
            detalhes.append({
                'id': questao['id'],
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'resposta_usuario': resposta_usuario,
                'resposta_correta': correta,
                'acertou': acertou,
                'explicacao': questao['explicacao'],
                'alternativas': questao['alternativas']
            })
        
        percentual = (acertos / total) * 100 if total > 0 else 0
        tempo_total = (fim - inicio).total_seconds()
        
        relatorio = {
            'geral': {
                'total_questoes': total,
                'acertos': acertos,
                'erros': total - acertos,
                'percentual_acerto': round(percentual, 2),
                'tempo_total_minutos': round(tempo_total / 60, 2),
                'questoes_respondidas': len(respostas)
            },
            'detalhes': detalhes,
            'tempo_inicio': inicio.isoformat(),
            'tempo_fim': fim.isoformat()
        }
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO historico_simulados 
            (relatorio, tipo_simulado, quantidade_questoes, materias_selecionadas)
            VALUES (?, ?, ?, ?)
        ''', (
            json.dumps(relatorio, ensure_ascii=False),
            'Personalizado',
            total,
            json.dumps(session['config']['materias'])
        ))
        conn.commit()
        conn.close()
        
        session.pop('simulado_ativo', None)
        session.pop('questoes', None)
        session.pop('respostas', None)
        session.pop('inicio', None)
        session.pop('config', None)
        
        return jsonify({
            'success': True,
            'relatorio': relatorio
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/temas/redacao')
def get_temas_redacao():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM temas_redacao ORDER BY RANDOM() LIMIT 10")
    temas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'temas': temas})

@app.route('/api/dashboard/estatisticas')
def get_estatisticas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM questões")
    total_questoes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM historico_simulados")
    total_simulados = cursor.fetchone()[0]
    
    cursor.execute("SELECT relatorio FROM historico_simulados ORDER BY data_fim ASC")
    historico = []
    tempo_total = 0
    
    for row in cursor.fetchall():
        try:
            relatorio = json.loads(row[0])
            historico.append({
                'percentual': relatorio['geral']['percentual_acerto'],
                'data': 'Simulado'
            })
            tempo_total += relatorio['geral'].get('tempo_total_minutos', 0)
        except:
            continue
    
    conn.close()
    
    media_geral = round(sum(h['percentual'] for h in historico) / len(historico), 2) if historico else 0
    
    return jsonify({
        'estatisticas': {
            'total_questoes_banco': total_questoes,
            'total_simulados_realizados': total_simulados,
            'media_geral_percentual': media_geral,
            'tempo_total_estudo_min': round(tempo_total, 2),
            'total_questoes_respondidas': total_simulados * 5,
            'evolucao_desempenho': historico[-10:] if historico else [],
            'desempenho_global_materia': {'Geografia': 75, 'História': 80, 'Literatura': 85},
            'historico_recente': []
        }
    })

# ========== INICIALIZAÇÃO ==========
@app.before_request
def initialize():
    carregar_dados_iniciais()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
