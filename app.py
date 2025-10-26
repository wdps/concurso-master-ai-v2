from flask import Flask, jsonify, send_from_directory, request, render_template, session
import os
import sqlite3
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import traceback # Para logar a pilha de erro completa

# Configurações
# Formato de log mais detalhado
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Chave secreta (MUITO IMPORTANTE: Trocar em produção real ou usar variável de ambiente)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_secret_key_that_is_very_secure_and_long_enough_12345_abc') # Chave atualizada

DATABASE = 'concurso.db' # Nome do arquivo do banco de dados

class SistemaSimulado:
    '''Gerencia a lógica de simulados ativos em memória.'''
    def __init__(self):
        self.simulados_ativos = {}

    def iniciar_simulado(self, user_id, config):
        '''
        Cria um novo registro de simulado em memória com base na configuração.
        Retorna o ID do simulado ou None se não encontrar questões ou ocorrer erro.
        '''
        simulado_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Tentando iniciar simulado {simulado_id} para user {user_id} com config: {config}")

        simulado_data = {
            'id': simulado_id, 'config': config, 'questoes': [], 'respostas': {},
            'inicio': datetime.now(), 'tempo_limite_min': config.get('tempo_minutos', 180),
            'status': 'ativo', 'questao_atual': 0
        }

        # Carrega as questões do banco de dados com base na configuração
        try:
            questoes = self._carregar_questoes_simulado(config)
        except ConnectionError as conn_err: # Erro específico de conexão
             logger.error(f"Erro de conexão ao carregar questões para simulado {simulado_id}: {conn_err}")
             return None # Falha ao carregar questões devido à conexão
        except sqlite3.Error as db_err_load: # Erro específico do SQLite no carregamento
            logger.error(f"Erro SQLite durante _carregar_questoes_simulado para simulado {simulado_id}: {db_err_load}", exc_info=True)
            return None # Falha ao carregar questões devido a erro DB
        except Exception as e_load: # Qualquer outro erro no carregamento
            logger.error(f"Erro CRÍTICO durante _carregar_questoes_simulado para simulado {simulador_id}: {e_load}", exc_info=True)
            return None # Falha ao carregar questões

        # Se nenhuma questão for encontrada, retorna None
        if not questoes:
             logger.warning(f"Nenhuma questão encontrada para a config: {config}. Simulado {simulado_id} não iniciado.")
             return None

        simulado_data['questoes'] = questoes
        self.simulados_ativos[simulado_id] = simulado_data
        logger.info(f"Simulado {simulado_id} iniciado com {len(questoes)} questões.")
        return simulado_id

    def _carregar_questoes_simulado(self, config):
        '''
        Busca questões no banco de dados SQLite com base nos filtros da configuração.
        Retorna uma lista de dicionários representando as questões.
        *** VERSÃO MAIS ROBUSTA contra erros de dados e com mais LOGS ***
        '''
        conn = get_db_connection()
        if not conn:
            logger.error("Falha ao carregar questões: Sem conexão com DB.")
            raise ConnectionError("Não foi possível conectar ao banco de dados.") # Lança exceção

        cursor = None
        try:
            cursor = conn.cursor()
            logger.debug("Cursor DB obtido.")

            materias = config.get('materias', [])
            try:
                 quantidade = int(config.get('quantidade_total', 50))
                 if quantidade <= 0: raise ValueError("Quantidade deve ser > 0")
            except (ValueError, TypeError):
                 logger.warning(f"Quantidade inválida: {config.get('quantidade_total')}. Usando 50.")
                 quantidade = 50
            aleatorio = config.get('aleatorio', True)

            if not materias or not isinstance(materias, list):
                logger.warning("Seleção de matérias inválida. Retornando vazio.")
                return []

            placeholders = ','.join(['?'] * len(materias))
            query = f"SELECT * FROM questoes WHERE disciplina IN ({placeholders})"
            params = list(materias)

            if aleatorio: query += " ORDER BY RANDOM()"
            else: query += " ORDER BY id"
            query += " LIMIT ?"
            params.append(quantidade)

            logger.info(f"Executando query: {query} com params: {params}")
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            logger.info(f"Query retornou {len(resultados)} resultados.")

            questoes = []
            if resultados:
                colunas_disponiveis = resultados[0].keys()
                logger.info(f"Colunas disponíveis na tabela 'questoes': {list(colunas_disponiveis)}")

                # ** LOG DETALHADO POR LINHA **
                for row_num, row in enumerate(resultados):
                    row_id_log = f"linha_{row_num}" # Default
                    try:
                        # Tenta pegar o ID real para o log, se existir
                        if 'id' in colunas_disponiveis:
                             row_id_log = f"ID_{row['id']}"

                        logger.debug(f"Processando questão {row_id_log}...")
                        # ** Tratamento robusto de JSON **
                        alternativas_dict = {}
                        alternativas_json = row['alternativas'] if 'alternativas' in colunas_disponiveis else None
                        if alternativas_json and isinstance(alternativas_json, str):
                            try:
                                alternativas_dict = json.loads(alternativas_json)
                                if not isinstance(alternativas_dict, dict):
                                    logger.error(f"JSON 'alternativas' não é dict na Q {row_id_log}. Conteúdo: {alternativas_json}")
                                    alternativas_dict = {"ERRO": "Formato"}
                            except json.JSONDecodeError as json_err:
                                logger.error(f"Erro JSONDecode em 'alternativas' na Q {row_id_log}: {json_err}. Conteúdo: {alternativas_json}")
                                alternativas_dict = {"ERRO": "JSON inválido"}
                        elif alternativas_json is not None:
                             logger.warning(f"'alternativas' não é string na Q {row_id_log}. Tipo: {type(alternativas_json)}. Conteúdo: {alternativas_json}")

                        # ** Tratamento de dados ausentes ou None **
                        disciplina_val = row['disciplina'] if 'disciplina' in colunas_disponiveis and row['disciplina'] else 'Sem Disciplina'
                        enunciado_val = row['enunciado'] if 'enunciado' in colunas_disponiveis and row['enunciado'] else '[Enunciado Ausente]'
                        resposta_val = row['resposta_correta'] if 'resposta_correta' in colunas_disponiveis and row['resposta_correta'] else None # ** Default None é mais seguro **

                        # ** Verifica se a resposta é válida ANTES de criar o objeto **
                        if not resposta_val:
                            logger.error(f"Resposta correta (gabarito) está VAZIA ou NULA na Q {row_id_log}. Pulando questão.")
                            continue # Pula esta questão

                        questao = {
                            'id': row['id'] if 'id' in colunas_disponiveis else row_num + 1, # Usa ID ou número da linha
                            'enunciado': enunciado_val,
                            'materia': disciplina_val,
                            'alternativas': alternativas_dict,
                            'resposta_correta': resposta_val,
                            'dificuldade': row['dificuldade'] if 'dificuldade' in colunas_disponiveis and row['dificuldade'] else 'Médio',
                            'justificativa': row['justificativa'] if 'justificativa' in colunas_disponiveis else None,
                            'dica': row['dica'] if 'dica' in colunas_disponiveis else None,
                            'formula': row['formula'] if 'formula' in colunas_disponiveis else None
                        }
                        questoes.append(questao)
                        logger.debug(f"Questão {row_id_log} processada com sucesso.")

                    except KeyError as key_err:
                        logger.error(f"Erro de Chave ao processar Q {row_id_log}: {key_err}. Colunas: {list(colunas_disponiveis)}")
                        continue # Pula
                    except Exception as parse_err:
                        logger.error(f"Erro inesperado ao processar Q {row_id_log}: {parse_err}", exc_info=True)
                        continue # Pula

            else:
                 logger.warning(f"Nenhum resultado DB para query com params: {params}")

            logger.info(f"Carregadas {len(questoes)} questões válidas.")
            return questoes

        except sqlite3.Error as db_err:
             logger.error(f"Erro SQLite crítico ao carregar questões: {db_err}", exc_info=True)
             raise db_err # Relança para ser pego acima
        except Exception as e:
            logger.error(f"Erro geral crítico ao carregar questões: {e}", exc_info=True)
            raise e # Relança
        finally:
            if conn: conn.close()
            logger.debug("Conexão DB fechada em _carregar_questoes_simulado.")

    def registrar_resposta(self, simulado_id, questao_index, alternativa, tempo_gasto_na_questao):
        '''Registra a resposta do usuário para uma questão específica no simulado ativo.'''
        simulado = self.simulados_ativos.get(simulado_id)
        if not simulado:
            logger.warning(f"Tentativa de resposta para simulado {simulado_id} inexistente ou finalizado.")
            return False

        if not isinstance(questao_index, int) or questao_index < 0 or questao_index >= len(simulado.get('questoes', [])):
            logger.warning(f"Índice de questão inválido ({questao_index}) para simulado {simulado_id}.")
            return False

        questao = simulado['questoes'][questao_index]
        acertou = str(alternativa).upper() == str(questao.get('resposta_correta', '')).upper()

        resposta = {
            'questao_id': questao.get('id'),
            'alternativa_escolhida': alternativa,
            'acertou': acertou,
            'tempo_gasto': tempo_gasto_na_questao,
            'timestamp': datetime.now().isoformat()
        }
        simulado['respostas'][questao_index] = resposta
        logger.info(f"Resposta registrada para simulado {simulado_id}, Q {questao_index}. Acertou: {acertou}")
        return True

    def finalizar_simulado(self, simulado_id):
        '''Marca simulado como finalizado, calcula relatório, salva e remove da memória.'''
        simulado = self.simulados_ativos.get(simulado_id)
        if not simulado:
             logger.warning(f"Tentativa de finalizar simulado {simulado_id} inexistente.")
             return None
        if simulado.get('status') == 'finalizado':
             logger.warning(f"Simulado {simulado_id} já finalizado.")
             return simulado.get('relatorio')

        simulado['fim'] = datetime.now()
        simulado['status'] = 'finalizado'
        try:
            relatorio = self._gerar_relatorio(simulado)
            simulado['relatorio'] = relatorio
        except Exception as e_report:
            logger.error(f"Erro ao gerar relatório para simulado {simulado_id}: {e_report}", exc_info=True)
            relatorio = {"error": "Falha ao gerar relatório."}

        self._salvar_historico(simulado)
        if simulado_id in self.simulados_ativos:
             del self.simulados_ativos[simulado_id]
             logger.info(f"Simulado {simulado_id} removido da memória ativa.")
        logger.info(f"Simulado {simulado_id} finalizado.")
        return relatorio

    def _gerar_relatorio(self, simulado):
        '''Calcula as estatísticas do simulado e gera recomendações.'''
        respostas = simulado.get('respostas', {})
        questoes = simulado.get('questoes', [])
        total_q_planejadas = len(questoes)
        q_respondidas_obj = list(respostas.values())
        q_respondidas_count = len(q_respondidas_obj)
        acertos = sum(1 for r in q_respondidas_obj if r.get('acertou', False))
        perc_acerto = (acertos / q_respondidas_count * 100) if q_respondidas_count > 0 else 0.0
        tempo_total_seg = sum(float(r.get('tempo_gasto', 0.0)) for r in q_respondidas_obj if isinstance(r.get('tempo_gasto'), (int, float)))

        stats_materia = {}
        for q_idx, resp in respostas.items():
            try:
                if q_idx < len(questoes):
                    q = questoes[q_idx]
                    materia = q.get('materia', 'Desconhecida') or 'Desconhecida'
                    if materia not in stats_materia: stats_materia[materia] = {'total': 0, 'acertos': 0, 'tempo': 0.0}
                    stats_materia[materia]['total'] += 1
                    stats_materia[materia]['tempo'] += float(resp.get('tempo_gasto', 0.0))
                    if resp.get('acertou', False): stats_materia[materia]['acertos'] += 1
                else: logger.warning(f"Índice {q_idx} inválido ao gerar relatório.")
            except Exception as e_stat: logger.error(f"Erro stat Q {q_idx}: {e_stat}", exc_info=True)

        for mat, stats in stats_materia.items():
            total = stats.get('total', 0)
            stats['percentual'] = round((stats['acertos'] / total * 100), 1) if total > 0 else 0.0
            stats['tempo_medio'] = round(stats['tempo'] / total, 1) if total > 0 else 0.0

        recomendacoes = self._gerar_recomendacoes(stats_materia)

        relatorio_final = {
            'geral': {'total_questoes_planejadas': total_q_planejadas, 'questoes_respondidas': q_respondidas_count,
                      'acertos': acertos, 'erros': q_respondidas_count - acertos,
                      'percentual_acerto': round(perc_acerto, 1), 'tempo_total_minutos': round(tempo_total_seg / 60, 1),
                      'tempo_medio_questao': round(tempo_total_seg / q_respondidas_count, 1) if q_respondidas_count > 0 else 0.0},
            'por_materia': stats_materia, 'recomendacoes': recomendacoes,
            'questoes_com_detalhes': self._preparar_questoes_detalhadas(simulado)
        }
        logger.info(f"Relatório gerado simulado {simulado['id']}: {acertos}/{q_respondidas_count}")
        return relatorio_final

    def _gerar_recomendacoes(self, estatisticas_materia):
        '''Gera recomendações em HTML com base no desempenho.'''
        recomendacoes = []
        materias_ordenadas = sorted(estatisticas_materia.items(), key=lambda item: item[1].get('percentual', 0.0))
        for materia, stats in materias_ordenadas:
            perc = stats.get('percentual', 0.0)
            if perc < 50: recomendacoes.append(f"<li class='list-group-item border-start-0 border-end-0 border-top-0 border-danger border-3'><i class='fas fa-exclamation-triangle text-danger me-2'></i> <strong>Foco Urgente:</strong> {materia} ({perc:.1f}%)</li>")
            elif perc < 70: recomendacoes.append(f"<li class='list-group-item border-start-0 border-end-0 border-top-0 border-warning border-3'><i class='fas fa-book-open text-warning me-2'></i> <strong>Revisar:</strong> {materia} ({perc:.1f}%)</li>")
            elif perc < 90: recomendacoes.append(f"<li class='list-group-item border-start-0 border-end-0 border-top-0 border-info border-3'><i class='fas fa-check text-info me-2'></i> <strong>Bom Desempenho:</strong> {materia} ({perc:.1f}%)</li>")
            else: recomendacoes.append(f"<li class='list-group-item border-start-0 border-end-0 border-top-0 border-success border-3'><i class='fas fa-star text-success me-2'></i> <strong>Excelente:</strong> {materia} ({perc:.1f}%)</li>")
        if not recomendacoes: recomendacoes.append("<li class='list-group-item border-0 text-muted'><i class='fas fa-chart-line text-primary me-2'></i> Complete um simulado.</li>")
        return recomendacoes

    def _preparar_questoes_detalhadas(self, simulado):
        '''Prepara lista de questões com detalhes para revisão.'''
        detalhes = []
        questoes = simulado.get('questoes', [])
        respostas = simulado.get('respostas', {})
        for i, q in enumerate(questoes):
            resp_obj = respostas.get(i)
            detalhes.append({
                'numero': i + 1, 'enunciado': q.get('enunciado', 'N/A'), 'materia': q.get('materia', 'N/A'),
                'alternativas': q.get('alternativas', {}), 'resposta_correta': q.get('resposta_correta'),
                'justificativa': q.get('justificativa'), 'dica': q.get('dica'), 'formula': q.get('formula'),
                'resposta_usuario': resp_obj.get('alternativa_escolhida') if resp_obj else None,
                'acertou': resp_obj.get('acertou') if resp_obj else None,
                'tempo_gasto': resp_obj.get('tempo_gasto') if resp_obj else None
            })
        return detalhes

    def _salvar_historico(self, simulado):
        '''Salva o relatório final no banco de dados.'''
        conn = get_db_connection()
        if not conn: logger.error(f"Falha salvar histórico {simulado.get('id', 'N/A')}: Sem DB."); return
        sid = simulado.get('id', ''); cfg = json.dumps(simulado.get('config', {})); rep = json.dumps(simulado.get('relatorio', {}));
        ini = simulado.get('inicio').isoformat() if simulado.get('inicio') else None; fim = simulado.get('fim').isoformat() if simulado.get('fim') else None
        try:
            cur = conn.cursor(); cur.execute('INSERT INTO historico_simulados (simulado_id, config, relatorio, data_inicio, data_fim) VALUES (?, ?, ?, ?, ?)', (sid, cfg, rep, ini, fim)); conn.commit()
            logger.info(f"Histórico simulado {sid} salvo.")
        except sqlite3.IntegrityError: logger.error(f"Erro Integridade: Simulado ID {sid} já existe."); conn.rollback()
        except sqlite3.Error as db_err: logger.error(f"Erro SQLite salvar histórico ({sid}): {db_err}", exc_info=True); conn.rollback()
        except Exception as e: logger.error(f"Erro geral salvar histórico ({sid}): {e}", exc_info=True); conn.rollback()
        finally:
            if conn: conn.close()

# --- Instância Global --- ## <<< CORREÇÃO AQUI >>> ###
sistema_simulado = SistemaSimulado() ## <<< ESTA LINHA CRIA A INSTÂNCIA GLOBAL >>> ###

# --- Funções de Banco de Dados ---
def get_db_connection():
    '''Estabelece conexão com o banco de dados SQLite.'''
    try:
        conn = sqlite3.connect(DATABASE, timeout=10) # Timeout aumentado
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"❌ Erro CRÍTICO conexão DB ({DATABASE}): {e}", exc_info=True)
        return None

def criar_tabelas_se_necessario():
    '''Verifica e cria todas as tabelas do schema V3.0 se não existirem.'''
    # Implementação simplificada para brevidade (usar a versão anterior completa)
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS questoes (id INTEGER PRIMARY KEY, disciplina TEXT, enunciado TEXT, alternativas TEXT, resposta_correta TEXT, dificuldade TEXT, justificativa TEXT, dica TEXT, formula TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS redacoes (id INTEGER PRIMARY KEY, titulo TEXT, tema TEXT, texto_base TEXT, dicas TEXT, criterios_avaliacao TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS historico_simulados (id INTEGER PRIMARY KEY, simulado_id TEXT UNIQUE NOT NULL, config TEXT, relatorio TEXT, data_inicio TIMESTAMP, data_fim TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS historico_redacoes (id INTEGER PRIMARY KEY, redacao_id INTEGER, texto_redacao TEXT, correcao TEXT, nota INTEGER, feedback TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (redacao_id) REFERENCES redacoes (id) ON DELETE SET NULL)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questoes_disciplina ON questoes(disciplina)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_simulados_data ON historico_simulados(data_fim)")
        conn.commit()
        return True
    except sqlite3.Error as db_err: logger.error(f"❌ Erro SQLite criar/verificar tabelas: {db_err}", exc_info=True); conn.rollback(); return False
    except Exception as e: logger.error(f"❌ Erro geral criar/verificar tabelas: {e}", exc_info=True); conn.rollback(); return False
    finally:
        if conn: conn.close()

# ========== ROTAS DE NAVEGAÇÃO (PÁGINAS HTML) ==========
@app.route('/')
def index(): return render_template('index.html')
@app.route('/simulado')
def simulado(): return render_template('simulado.html')
@app.route('/redacao')
def redacao(): return render_template('redacao.html')
@app.route('/dashboard')
def dashboard(): return render_template('dashboard.html')

# ========== API ENDPOINTS (RETORNAM JSON) ==========
@app.route('/api/health')
def health():
    # Implementação simplificada (usar a versão anterior completa)
    db_ok = bool(get_db_connection())
    status_code = 200 if db_ok else 503
    return jsonify({"status": "online", "database_status": "connected" if db_ok else "error", "version": "3.4"}), status_code

@app.route('/api/materias')
def materias():
    # Implementação simplificada (usar a versão anterior completa)
    if not criar_tabelas_se_necessario(): return jsonify({"error": "Erro DB init."}), 500
    conn = get_db_connection();
    if not conn: return jsonify({"error": "Erro conexão DB."}), 500
    try:
        cursor = conn.cursor(); cursor.execute("SELECT disciplina, COUNT(*) as total FROM questoes GROUP BY disciplina HAVING COUNT(*) > 0 ORDER BY disciplina ASC")
        rows = cursor.fetchall(); materias_lista = []; estatisticas_dict = {}; total_geral = 0
        for row in rows: mat = row['disciplina']; total = row['total']; materias_lista.append(mat); estatisticas_dict[mat] = {'total': total}; total_geral += total
        return jsonify({"materias": materias_lista, "estatisticas": estatisticas_dict, "total_geral": total_geral})
    except Exception as e: logger.error(f"Erro API /materias: {e}", exc_info=True); return jsonify({"error": "Erro interno."}), 500
    finally:
         if conn: conn.close()

# --- API do Sistema de Simulado ---
@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado_api():
    '''Recebe a config, inicia o simulado e retorna dados iniciais.'''
    logger.info("Recebida requisição POST /api/simulado/iniciar")
    try:
        data = request.get_json()
        if not data: return jsonify({"success": False, "error": "Requisição inválida (sem JSON)"}), 400

        # Validações (simplificadas, usar versão anterior para mais detalhes)
        materias_req = data.get('materias')
        if not materias_req or not isinstance(materias_req, list) or len(materias_req) == 0:
             return jsonify({"success": False, "error": "Seleção de matérias inválida."}), 400
        try: quantidade_int = int(data.get('quantidade_total', 50)); assert quantidade_int > 0
        except: return jsonify({"success": False, "error": "Quantidade inválida."}), 400
        try: tempo_int = int(data.get('tempo_minutos', 180)); assert tempo_int > 0
        except: return jsonify({"success": False, "error": "Tempo inválido."}), 400

        config = {'materias': materias_req, 'quantidade_total': quantidade_int, 'tempo_minutos': tempo_int, 'aleatorio': bool(data.get('aleatorio', True))}
        logger.info(f"Configuração recebida: {config}")

        user_id = session.get('user_id', 'anon_' + str(random.randint(10000, 99999)))
        # ** Ponto Crítico: Chamar a instância global correta **
        simulado_id = sistema_simulado.iniciar_simulado(user_id, config)

        if not simulado_id:
             logger.error("Falha ao iniciar simulado (iniciar_simulado retornou None).")
             return jsonify({"success": False, "error": "Não foi possível iniciar. Verifique se há questões disponíveis ou logs do servidor."}), 500

        simulado_ativo = sistema_simulado.simulados_ativos.get(simulado_id)
        if not simulado_ativo or not simulado_ativo.get('questoes'):
             logger.critical(f"INCONSISTÊNCIA GRAVE PÓS-INÍCIO: Simulado {simulado_id} sem dados.")
             if simulado_id in sistema_simulado.simulados_ativos: del sistema_simulado.simulados_ativos[simulado_id]
             return jsonify({"success": False, "error": "Erro interno crítico (S01)."}), 500

        primeira_questao = simulado_ativo['questoes'][0].copy()
        primeira_questao.pop('resposta_correta', None); primeira_questao.pop('justificativa', None)
        total_questoes = len(simulado_ativo['questoes'])

        logger.info(f"Simulado {simulado_id} iniciado com {total_questoes}q. Enviando dados.")
        return jsonify({"success": True, "simulado_id": simulado_id, "total_questoes": total_questoes,
                        "primeira_questao": primeira_questao, "tempo_limite_seg": config['tempo_minutos'] * 60})

    except Exception as e_api:
        error_trace = traceback.format_exc()
        logger.error(f"Erro 500 NÃO TRATADO API /iniciar: {e_api}\n{error_trace}")
        return jsonify({"success": False, "error": "Erro interno inesperado (S02)."}), 500


@app.route('/api/simulado/<simulado_id>/questao/<int:questao_index>')
def get_questao_simulado(simulado_id, questao_index):
    # Implementação simplificada (usar a versão anterior completa)
    simulado = sistema_simulado.simulados_ativos.get(simulado_id)
    if not simulado: return jsonify({"error": "Simulado não ativo."}), 404
    questoes_list = simulado.get('questoes', [])
    if not (0 <= questao_index < len(questoes_list)): return jsonify({"error": "Índice inválido."}), 404
    questao = questoes_list[questao_index].copy()
    questao.pop('resposta_correta', None); questao.pop('justificativa', None)
    return jsonify({"questao": questao, "numero_questao": questao_index + 1, "total_questoes": len(questoes_list)})


@app.route('/api/simulado/<simulado_id>/responder', methods=['POST'])
def responder_questao_api(simulado_id):
    # Implementação simplificada (usar a versão anterior completa)
    try:
        data = request.get_json(); assert data
        q_idx = int(data['questao_index']); alt = str(data['alternativa']); tempo = float(data.get('tempo_gasto', 0))
        simulado = sistema_simulado.simulados_ativos.get(simulado_id); assert simulado
        questoes = simulado.get('questoes', []); assert 0 <= q_idx < len(questoes)
        q_orig = questoes[q_idx]; resp_correta = str(q_orig.get('resposta_correta', '')).upper(); acertou = alt.upper() == resp_correta
        success = sistema_simulado.registrar_resposta(simulado_id, q_idx, alt, tempo)
        if not success: raise Exception("Falha registro interno")
        return jsonify({"success": True, "acertou": acertou, "resposta_correta": resp_correta, "justificativa": q_orig.get('justificativa'), "dica": q_orig.get('dica'), "formula": q_orig.get('formula')})
    except Exception as e: logger.error(f"Erro API /responder: {e}", exc_info=True); return jsonify({"success": False, "error": "Erro ao processar resposta."}), 500


@app.route('/api/simulado/<simulado_id>/finalizar', methods=['POST'])
def finalizar_simulado_api(simulado_id):
    # Implementação simplificada (usar a versão anterior completa)
    try:
        relatorio = sistema_simulado.finalizar_simulado(simulado_id)
        if relatorio: return jsonify({"success": True, "relatorio": relatorio})
        else: return jsonify({"success": False, "error": "Simulado não ativo."}), 404
    except Exception as e: logger.error(f"Erro API /finalizar: {e}", exc_info=True); return jsonify({"success": False, "error": "Erro ao finalizar."}), 500


# --- API Redação e Dashboard ---
# ... (manter o código das rotas /api/redacoes/* e /api/dashboard/* da V3.1) ...
@app.route('/api/redacoes/temas')
def get_temas_redacao():
    # Implementação simplificada (usar a versão anterior completa)
    if not criar_tabelas_se_necessario(): return jsonify({"temas": [], "error": "Erro DB init."}), 500
    conn = get_db_connection();
    if not conn: return jsonify({"temas": [], "error": "Erro conexão DB."}), 500
    try: cur = conn.cursor(); cur.execute("SELECT id, titulo, tema, texto_base, dicas FROM redacoes ORDER BY id DESC"); temas = [dict(row) for row in cur.fetchall()]; return jsonify({"temas": temas})
    except Exception as e: logger.error(f"Erro API /temas: {e}", exc_info=True); return jsonify({"temas": [], "error": "Erro interno."}), 500
    finally:
        if conn: conn.close()

@app.route('/api/redacoes/corrigir', methods=['POST'])
def corrigir_redacao_api():
    # Implementação simplificada (usar a versão anterior completa)
    try:
        data = request.get_json(); assert data; r_id = data['redacao_id']; texto = data['texto_redacao']; assert r_id and texto
        nota = min(int(len(texto)/10.0 + random.uniform(200,400)), 1000)
        corr = {'nota': nota, 'feedback_geral': f'Correção simulada. Nota: {nota}', 'sugestoes_melhoria': ['Sugestão 1', 'Sugestão 2']}
        conn = get_db_connection()
        if conn:
            try: cur = conn.cursor(); cur.execute('INSERT INTO historico_redacoes (redacao_id, texto_redacao, correcao, nota, feedback) VALUES (?, ?, ?, ?, ?)', (r_id, texto, json.dumps(corr), corr['nota'], corr['feedback_geral'])); conn.commit()
            finally: conn.close()
        return jsonify({"success": True, "correcao": corr})
    except Exception as e: logger.error(f"Erro API /corrigir: {e}", exc_info=True); return jsonify({"success": False, "error": "Erro interno."}), 500

@app.route('/api/dashboard/estatisticas')
def get_estatisticas_dashboard():
    # Implementação simplificada (usar a versão anterior completa)
    if not criar_tabelas_se_necessario(): return jsonify({"estatisticas": {}, "error": "Erro DB init."}), 500
    conn = get_db_connection();
    if not conn: return jsonify({"estatisticas": {}, "error": "Erro conexão DB."}), 500
    try:
        cur = conn.cursor(); cur.execute("SELECT COUNT(*) as total FROM questoes"); total_q = cur.fetchone()['total']
        cur.execute("SELECT relatorio, data_fim FROM historico_simulados ORDER BY data_fim ASC"); rels = cur.fetchall()
        hist_ev = []; t_estudo = 0; q_resp = 0; stats_mat = {}
        for row in rels:
            try: r = json.loads(row['relatorio']); df = datetime.fromisoformat(row['data_fim']); g = r.get('geral', {})
            except: continue
            hist_ev.append({'data': df.strftime('%d/%m'), 'percentual': float(g.get('percentual_acerto', 0.0))})
            t_estudo += float(g.get('tempo_total_minutos', 0.0)); q_resp += int(g.get('questoes_respondidas', 0))
            for m, s in r.get('por_materia', {}).items(): stats_mat[m] = stats_mat.get(m,{'a':0,'t':0}); stats_mat[m]['a']+=int(s.get('acertos',0)); stats_mat[m]['t']+=int(s.get('total',0))
        dgm = {m: round(s['a']*100.0/s['t'],1) if s['t']>0 else 0.0 for m,s in stats_mat.items()}
        hist_rec = []
        for row in reversed(rels[-10:]):
             try: r = json.loads(row['relatorio']); df = datetime.fromisoformat(row['data_fim']); hist_rec.append({'data': df.strftime('%d/%m/%Y %H:%M'), 'geral': r.get('geral',{})})
             except: continue
        media = round(sum(h['percentual'] for h in hist_ev)/len(hist_ev),1) if hist_ev else 0.0
        return jsonify({"estatisticas": {"total_questoes_banco": total_q, "total_simulados_realizados": len(rels), "total_questoes_respondidas": q_resp, "tempo_total_estudo_min": round(t_estudo,1), "media_geral_percentual": media, "evolucao_desempenho": hist_ev, "desempenho_global_materia": dgm, "historico_recente": hist_rec}})
    except Exception as e: logger.error(f"Erro API /estatisticas: {e}", exc_info=True); return jsonify({"estatisticas": {}, "error": "Erro interno."}), 500
    finally:
        if conn: conn.close()


# --- Rotas Estáticas ---
@app.route('/static/<path:filename>')
def serve_static_files(filename): return send_from_directory('static', filename)

# --- Tratamento de Erros ---
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"Rota 404: {request.url}")
    if request.path.startswith('/api/'): return jsonify({"error": "Endpoint não encontrado"}), 404
    try: return render_template('error.html', mensagem="Página não encontrada (404)."), 404
    except: return "<h1>Erro 404</h1>", 404

@app.errorhandler(500)
def internal_error(error):
    error_trace = traceback.format_exc()
    logger.error(f"Erro 500 na rota {request.url}:\n{error_trace}")
    if request.path.startswith('/api/'): return jsonify({"error": "Erro interno servidor."}), 500 # PROD
    try: return render_template('error.html', mensagem="Erro interno do servidor (500)."), 500
    except: return "<h1>Erro 500</h1>", 500


# --- Inicialização da Aplicação ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    if not criar_tabelas_se_necessario(): logger.critical("########## FALHA AO INICIALIZAR DB ##########")
    logger.info(f"========= INICIANDO App V3.4 NA PORTA {port} =========")
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    use_debug = not is_production and os.environ.get('FLASK_DEBUG') == '1'
    if use_debug: logger.warning("############## MODO DEBUG ATIVO ##############"); app.run(host='0.0.0.0', port=port, debug=True)
    else: logger.info("Rodando em modo PRODUÇÃO (debug=False)"); app.run(host='0.0.0.0', port=port, debug=False)

