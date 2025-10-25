from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
from datetime import datetime, timedelta
import logging
import os
import csv

# Configura��o do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_secret_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Configura��o do banco de dados
DATABASE = 'concurso.db'

def get_db_connection():
    """Cria conex�o com o banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar com o banco: {e}")
        return None

def criar_tabelas_se_necessario():
    """Cria as tabelas necess�rias se n�o existirem"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabela de quest�es
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quest�es (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT NOT NULL,
                materia TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT,
                dificuldade TEXT DEFAULT 'M�dia',
                tempo_estimado INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de hist�rico de simulados
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
        logger.info("? Tabelas verificadas/criadas com sucesso!")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        return False
    finally:
        conn.close()

def carregar_questoes_csv():
    """Carrega quest�es do CSV para o banco de dados usando csv nativo"""
    if not os.path.exists('questoes.csv'):
        logger.warning("? Arquivo questoes.csv n�o encontrado")
        # Criar algumas quest�es de exemplo
        criar_questoes_exemplo()
        return True
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            quest�es_carregadas = 0
            
            for row in csv_reader:
                try:
                    # Criar dicion�rio de alternativas
                    alternativas_dict = {}
                    for letra in ['A', 'B', 'C', 'D', 'E']:
                        if letra in row and row[letra] and row[letra].strip():
                            alternativas_dict[letra] = row[letra].strip()
                    
                    # Se n�o encontrou alternativas, criar padr�o
                    if not alternativas_dict:
                        alternativas_dict = {
                            'A': 'Alternativa A',
                            'B': 'Alternativa B', 
                            'C': 'Alternativa C',
                            'D': 'Alternativa D'
                        }
                    
                    # Inserir quest�o
                    cursor.execute('''
                        INSERT OR IGNORE INTO quest�es 
                        (enunciado, materia, alternativas, resposta_correta, explicacao)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row.get('enunciado', 'Enunciado n�o dispon�vel'),
                        row.get('materia', 'Geral'),
                        json.dumps(alternativas_dict),
                        row.get('resposta_correta', 'A'),
                        row.get('explicacao', 'Explica��o n�o dispon�vel')
                    ))
                    
                    if cursor.rowcount > 0:
                        quest�es_carregadas += 1
                        
                except Exception as e:
                    logger.error(f"Erro ao processar linha do CSV: {e}")
                    continue
        
        conn.commit()
        conn.close()
        logger.info(f"? {quest�es_carregadas} quest�es carregadas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"? Erro ao carregar quest�es do CSV: {e}")
        # Criar quest�es de exemplo em caso de erro
        criar_questoes_exemplo()
        return True

def criar_questoes_exemplo():
    """Cria quest�es de exemplo se o CSV n�o existir ou falhar"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        quest�es_exemplo = [
            {
                'enunciado': 'Qual � a capital do Brasil?',
                'materia': 'Geografia',
                'alternativas': {'A': 'Rio de Janeiro', 'B': 'Bras�lia', 'C': 'S�o Paulo', 'D': 'Salvador'},
                'resposta_correta': 'B',
                'explicacao': 'Bras�lia � a capital federal do Brasil desde 1960.'
            },
            {
                'enunciado': 'Quem escreveu "Dom Casmurro"?',
                'materia': 'Literatura', 
                'alternativas': {'A': 'Machado de Assis', 'B': 'Jos� de Alencar', 'C': 'Lima Barreto', 'D': 'Graciliano Ramos'},
                'resposta_correta': 'A',
                'explicacao': 'Machado de Assis � o autor de "Dom Casmurro", publicado em 1899.'
            },
            {
                'enunciado': 'Qual � o resultado de 2 + 2?',
                'materia': 'Matem�tica',
                'alternativas': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
                'resposta_correta': 'B',
                'explicacao': 'A soma de 2 + 2 � igual a 4.'
            },
            {
                'enunciado': 'Qual oceano banha o litoral brasileiro?',
                'materia': 'Geografia',
                'alternativas': {'A': 'Oceano Pac�fico', 'B': 'Oceano �ndico', 'C': 'Oceano Atl�ntico', 'D': 'Oceano �rtico'},
                'resposta_correta': 'C',
                'explicacao': 'O Brasil � banhado pelo Oceano Atl�ntico.'
            },
            {
                'enunciado': 'Em que ano o Brasil foi descoberto?',
                'materia': 'Hist�ria',
                'alternativas': {'A': '1492', 'B': '1500', 'C': '1520', 'D': '1450'},
                'resposta_correta': 'B', 
                'explicacao': 'O Brasil foi descoberto em 1500 por Pedro �lvares Cabral.'
            }
        ]
        
        for questao in quest�es_exemplo:
            cursor.execute('''
                INSERT OR IGNORE INTO quest�es 
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
        logger.info("? 5 quest�es de exemplo criadas com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao criar quest�es exemplo: {e}")

# Rotas principais
@app.route('/')
def index():
    """P�gina inicial"""
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    """P�gina de configura��o do simulado"""
    conn = get_db_connection()
    if not conn:
        return render_template('simulado.html', materias=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT materia FROM quest�es WHERE materia IS NOT NULL AND materia != ''")
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        
        return render_template('simulado.html', materias=materias)
    except Exception as e:
        logger.error(f"Erro ao carregar mat�rias: {e}")
        return render_template('simulado.html', materias=[])

@app.route('/redacao')
def redacao():
    """P�gina de reda��o"""
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard profissional"""
    return render_template('dashboard.html')

# API Routes
@app.route('/api/questoes/random')
def get_questoes_random():
    """API para obter quest�es aleat�rias"""
    try:
        quantidade = int(request.args.get('quantidade', 10))
        materias = request.args.getlist('materias') or []
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conex�o com o banco'}), 500
        
        cursor = conn.cursor()
        
        query = "SELECT * FROM quest�es WHERE 1=1"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND materia IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade)
        
        cursor.execute(query, params)
        quest�es = cursor.fetchall()
        conn.close()
        
        quest�es_formatadas = []
        for questao in quest�es:
            try:
                alternativas = json.loads(questao['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
            quest�es_formatadas.append({
                'id': questao['id'],
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'alternativas': alternativas,
                'resposta_correta': questao['resposta_correta'],
                'explicacao': questao['explicacao'],
                'dificuldade': questao.get('dificuldade', 'M�dia')
            })
        
        return jsonify({'questoes': quest�es_formatadas})
        
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
        
        # Buscar quest�es
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conex�o'}), 500
        
        cursor = conn.cursor()
        
        query = "SELECT * FROM quest�es WHERE 1=1"
        params = []
        
        if materias:
            placeholders = ','.join(['?'] * len(materias))
            query += f" AND materia IN ({placeholders})"
            params.extend(materias)
        
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade)
        
        cursor.execute(query, params)
        quest�es_db = cursor.fetchall()
        conn.close()
        
        if not quest�es_db:
            return jsonify({'error': 'Nenhuma quest�o encontrada com os filtros selecionados'}), 404
        
        # Formatar quest�es
        quest�es_formatadas = []
        for questao in quest�es_db:
            try:
                alternativas = json.loads(questao['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
            quest�es_formatadas.append({
                'id': questao['id'],
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'alternativas': alternativas,
                'resposta_correta': questao['resposta_correta'],
                'explicacao': questao['explicacao'],
                'dificuldade': questao.get('dificuldade', 'M�dia')
            })
        
        # Iniciar sess�o do simulado
        session['simulado_ativo'] = True
        session['questoes_simulado'] = quest�es_formatadas
        session['respostas_usuario'] = {}
        session['tempo_inicio'] = datetime.now().isoformat()
        session['config_simulado'] = {
            'quantidade': quantidade,
            'materias': materias,
            'tempo_por_questao': tempo_por_questao
        }
        
        return jsonify({
            'success': True,
            'total_questoes': len(quest�es_formatadas),
            'tempo_estimado': quantidade * tempo_por_questao
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/simulado/iniciar: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/questao/<int:questao_id>')
def get_questao_simulado(questao_id):
    """Obt�m uma quest�o espec�fica do simulado atual"""
    if not session.get('simulado_ativo'):
        return jsonify({'error': 'Nenhum simulado ativo'}), 400
    
    quest�es = session.get('questoes_simulado', [])
    questao = next((q for q in quest�es if q['id'] == questao_id), None)
    
    if not questao:
        return jsonify({'error': 'Quest�o n�o encontrada'}), 404
    
    return jsonify({'questao': questao})

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    """Registra resposta do usu�rio"""
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
    """Finaliza o simulado e gera relat�rio"""
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'error': 'Nenhum simulado ativo'}), 400
        
        quest�es = session.get('questoes_simulado', [])
        respostas = session.get('respostas_usuario', {})
        tempo_inicio = datetime.fromisoformat(session.get('tempo_inicio', datetime.now().isoformat()))
        tempo_fim = datetime.now()
        
        # Calcular estat�sticas
        estatisticas = calcular_estatisticas_simulado(quest�es, respostas, tempo_inicio, tempo_fim)
        
        # Salvar no hist�rico
        salvar_historico_simulado(estatisticas, session.get('config_simulado', {}))
        
        # Limpar sess�o
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

def calcular_estatisticas_simulado(quest�es, respostas, tempo_inicio, tempo_fim):
    """Calcula estat�sticas detalhadas do simulado"""
    total_questoes = len(quest�es)
    acertos = 0
    erros = 0
    nao_respondidas = 0
    
    # Estat�sticas por mat�ria
    stats_por_materia = {}
    
    for questao in quest�es:
        questao_id = str(questao['id'])
        materia = questao['materia']
        resposta_usuario = respostas.get(questao_id, {}).get('resposta')
        resposta_correta = questao['resposta_correta']
        
        # Inicializar estat�sticas da mat�ria
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
    
    # Calcular percentuais por mat�ria
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
    """Salva o relat�rio do simulado no hist�rico"""
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
        logger.error(f"Erro ao salvar hist�rico: {e}")
        return False

@app.route('/api/dashboard/estatisticas')
def get_estatisticas_dashboard():
    """Estat�sticas para o dashboard profissional"""
    criar_tabelas_se_necessario()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"estatisticas": {}})
    
    try:
        cursor = conn.cursor()
        
        # 1. Total de quest�es no banco
        cursor.execute("SELECT COUNT(*) as total FROM quest�es")
        total_questoes_banco = cursor.fetchone()['total']
        
        # 2. Hist�rico de simulados
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
                
                # Para gr�fico de evolu��o
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
                
                # Para gr�fico de desempenho por mat�ria
                for materia, stats in relatorio.get('por_materia', {}).items():
                    if materia not in global_stats_materia:
                        global_stats_materia[materia] = {'acertos': 0, 'total': 0}
                    global_stats_materia[materia]['acertos'] += stats['acertos']
                    global_stats_materia[materia]['total'] += stats['total']
                    
            except Exception as e:
                logger.error(f"Erro ao processar relatorio: {e}")

        # Calcular percentuais globais por mat�ria
        desempenho_global_materia = {}
        for materia, stats in global_stats_materia.items():
            percentual = (stats['acertos'] * 100 / stats['total']) if stats['total'] > 0 else 0
            desempenho_global_materia[materia] = round(percentual, 2)
            
        # 4. Hist�rico recente
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

        # 5. M�dia geral
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

# Inicializa��o
@app.before_request
def initialize_app():
    """Inicializa a aplica��o"""
    criar_tabelas_se_necessario()
    carregar_questoes_csv()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
