from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
from datetime import datetime, timedelta
import logging
import pandas as pd
import os

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_secret_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Configuração do banco de dados
DATABASE = 'concurso.db'

def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar com o banco: {e}")
        return None

def criar_tabelas_se_necessario():
    """Cria as tabelas necessárias se não existirem"""
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
        logger.info("✅ Tabelas verificadas/criadas com sucesso!")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        return False
    finally:
        conn.close()

def carregar_questoes_csv():
    """Carrega questões do CSV para o banco de dados"""
    if not os.path.exists('questoes.csv'):
        logger.warning("❌ Arquivo questoes.csv não encontrado")
        # Criar algumas questões de exemplo
        criar_questoes_exemplo()
        return True
    
    try:
        df = pd.read_csv('questoes.csv')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        questões_carregadas = 0
        for index, row in df.iterrows():
            try:
                # Verificar se a linha tem dados válidos
                if pd.isna(row.get('enunciado')) or pd.isna(row.get('resposta_correta')):
                    continue
                    
                # Converter alternativas para JSON
                alternativas_dict = {}
                for letra in ['A', 'B', 'C', 'D', 'E']:
                    if letra in row and not pd.isna(row[letra]):
                        alternativas_dict[letra] = str(row[letra])
                
                # Se não encontrou alternativas, criar padrão
                if not alternativas_dict:
                    alternativas_dict = {
                        'A': 'Alternativa A',
                        'B': 'Alternativa B', 
                        'C': 'Alternativa C',
                        'D': 'Alternativa D'
                    }
                
                cursor.execute('''
                    INSERT OR IGNORE INTO questões 
                    (enunciado, materia, alternativas, resposta_correta, explicacao)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    str(row['enunciado']),
                    str(row.get('materia', 'Geral')),
                    json.dumps(alternativas_dict),
                    str(row['resposta_correta']),
                    str(row.get('explicacao', 'Explicação não disponível'))
                ))
                
                if cursor.rowcount > 0:
                    questões_carregadas += 1
                    
            except Exception as e:
                logger.error(f"Erro ao inserir questão {index}: {e}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"✅ {questões_carregadas} questões carregadas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar questões do CSV: {e}")
        # Criar questões de exemplo em caso de erro
        criar_questoes_exemplo()
        return True

def criar_questoes_exemplo():
    """Cria questões de exemplo se o CSV não existir"""
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
                'enunciado': 'Quem escreveu "Dom Casmurro"?',
                'materia': 'Literatura',
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
        logger.info("✅ Questões de exemplo criadas com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao criar questões exemplo: {e}")

# Rotas principais
@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    """Página de configuração do simulado"""
    conn = get_db_connection()
    if not conn:
        return render_template('simulado.html', materias=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT materia FROM questões WHERE materia IS NOT NULL AND materia != ''")
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        
        return render_template('simulado.html', materias=materias)
    except Exception as e:
        logger.error(f"Erro ao carregar matérias: {e}")
        return render_template('simulado.html', materias=[])

@app.route('/redacao')
def redacao():
    """Página de redação"""
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard profissional"""
    return render_template('dashboard.html')

# API Routes
@app.route('/api/questoes/random')
def get_questoes_random():
    """API para obter questões aleatórias"""
    try:
        quantidade = int(request.args.get('quantidade', 10))
        materias = request.args.getlist('materias') or []
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com o banco'}), 500
        
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
        questões = cursor.fetchall()
        conn.close()
        
        questões_formatadas = []
        for questao in questões:
            try:
                alternativas = json.loads(questao['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
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
        
        # Buscar questões
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão'}), 500
        
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
        
        # Formatar questões
        questões_formatadas = []
        for questao in questões_db:
            try:
                alternativas = json.loads(questao['alternativas'])
            except:
                alternativas = {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D"}
            
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
        logger.error(f"Erro em /api/simulado/iniciar: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/questao/<int:questao_id>')
def get_questao_simulado(questao_id):
    """Obtém uma questão específica do simulado atual"""
    if not session.get('simulado_ativo'):
        return jsonify({'error': 'Nenhum simulado ativo'}), 400
    
    questões = session.get('questoes_simulado', [])
    questao = next((q for q in questões if q['id'] == questao_id), None)
    
    if not questao:
        return jsonify({'error': 'Questão não encontrada'}), 404
    
    return jsonify({'questao': questao})

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    """Registra resposta do usuário"""
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
    """Finaliza o simulado e gera relatório"""
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'error': 'Nenhum simulado ativo'}), 400
        
        questões = session.get('questoes_simulado', [])
        respostas = session.get('respostas_usuario', {})
        tempo_inicio = datetime.fromisoformat(session.get('tempo_inicio', datetime.now().isoformat()))
        tempo_fim = datetime.now()
        
        # Calcular estatísticas
        estatisticas = calcular_estatisticas_simulado(questões, respostas, tempo_inicio, tempo_fim)
        
        # Salvar no histórico
        salvar_historico_simulado(estatisticas, session.get('config_simulado', {}))
        
        # Limpar sessão
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

def calcular_estatisticas_simulado(questões, respostas, tempo_inicio, tempo_fim):
    """Calcula estatísticas detalhadas do simulado"""
    total_questoes = len(questões)
    acertos = 0
    erros = 0
    nao_respondidas = 0
    
    # Estatísticas por matéria
    stats_por_materia = {}
    
    for questao in questões:
        questao_id = str(questao['id'])
        materia = questao['materia']
        resposta_usuario = respostas.get(questao_id, {}).get('resposta')
        resposta_correta = questao['resposta_correta']
        
        # Inicializar estatísticas da matéria
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
    
    # Calcular percentuais por matéria
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
    """Salva o relatório do simulado no histórico"""
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
        logger.error(f"Erro ao salvar histórico: {e}")
        return False

@app.route('/api/dashboard/estatisticas')
def get_estatisticas_dashboard():
    """Estatísticas para o dashboard profissional"""
    criar_tabelas_se_necessario()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"estatisticas": {}})
    
    try:
        cursor = conn.cursor()
        
        # 1. Total de questões no banco
        cursor.execute("SELECT COUNT(*) as total FROM questões")
        total_questoes_banco = cursor.fetchone()['total']
        
        # 2. Histórico de simulados
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
                
                # Para gráfico de evolução
                data_obj = datetime.fromisoformat(data_fim_str.replace('Z', '+00:00'))
                historico_evolucao.append({
                    'data': data_obj.strftime('%d/%m'),
                    'percentual': relatorio['geral']['percentual_acerto']
                })
                
                # Para stats de KPI
                tempo_total_estudo += relatorio['geral'].get('tempo_total_minutos', 0)
                total_questoes_respondidas += relatorio['geral'].get('questoes_respondidas', 0)
                
                # Para gráfico de desempenho por matéria
                for materia, stats in relatorio.get('por_materia', {}).items():
                    if materia not in global_stats_materia:
                        global_stats_materia[materia] = {'acertos': 0, 'total': 0}
                    global_stats_materia[materia]['acertos'] += stats['acertos']
                    global_stats_materia[materia]['total'] += stats['total']
                    
            except Exception as e:
                logger.error(f"Erro ao processar relatorio: {e}")

        # Calcular percentuais globais por matéria
        desempenho_global_materia = {}
        for materia, stats in global_stats_materia.items():
            percentual = (stats['acertos'] * 100 / stats['total']) if stats['total'] > 0 else 0
            desempenho_global_materia[materia] = round(percentual, 2)
            
        # 4. Histórico recente
        historico_recente_formatado = []
        for row in reversed(todos_relatorios[-10:]): 
            try:
                relatorio = json.loads(row['relatorio'])
                data_fim_str = row['data_fim']
                data_obj = datetime.fromisoformat(data_fim_str.replace('Z', '+00:00'))
                historico_recente_formatado.append({
                    'data': data_obj.strftime('%d/%m/%Y %H:%M'),
                    'geral': relatorio['geral']
                })
            except:
                pass

        # 5. Média geral
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

# Inicialização
@app.before_request
def initialize_app():
    """Inicializa a aplicação"""
    criar_tabelas_se_necessario()
    carregar_questoes_csv()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
