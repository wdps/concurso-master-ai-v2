from flask import Flask, jsonify, send_from_directory, request, render_template, session
import os
import sqlite3
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any # Adicionado Any
import logging
import traceback # Para logar a pilha de erro completa

# --- Configurações ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Chave secreta (MUITO IMPORTANTE: Trocar em produção real ou usar variável de ambiente)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'v4_super_secret_key_needs_change_123!')

DATABASE = 'concurso.db' # Nome do arquivo do banco de dados

# --- Classe SistemaSimulado ---
class SistemaSimulado:
    '''Gerencia a lógica de simulados ativos em memória.'''
    def __init__(self):
        self.simulados_ativos: Dict[str, Dict[str, Any]] = {} # Tipagem adicionada

    def iniciar_simulado(self, user_id: str, config: Dict[str, Any]) -> Optional[str]:
        '''
        Cria um novo simulado em memória. Retorna ID ou None em caso de falha.
        '''
        simulado_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Tentando iniciar simulado {simulado_id} para user {user_id} com config: {config}")

        simulado_data: Dict[str, Any] = {
            'id': simulado_id, 'config': config, 'questoes': [], 'respostas': {},
            'inicio': datetime.now(), 'tempo_limite_min': config.get('tempo_minutos', 180),
            'status': 'ativo', 'historico_navegacao': [0] # Começa na questão 0
        }

        try:
            questoes = self._carregar_questoes_simulado(config)
        except Exception as e_load:
            logger.error(f"Erro CRÍTICO durante _carregar_questoes_simulado para {simulado_id}: {e_load}", exc_info=True)
            return None # Falha ao carregar

        if not questoes:
             logger.warning(f"Nenhuma questão encontrada para config: {config}. Simulado {simulado_id} não iniciado.")
             return None

        simulado_data['questoes'] = questoes
        self.simulados_ativos[simulado_id] = simulado_data
        logger.info(f"Simulado {simulado_id} iniciado com {len(questoes)} questões.")
        return simulado_id

    def _carregar_questoes_simulado(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        '''Busca questões no DB com base nos filtros.'''
        conn = get_db_connection()
        if not conn:
            logger.error("Falha ao carregar questões: Sem conexão com DB.")
            raise ConnectionError("Não foi possível conectar ao banco de dados.")

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
            # Seleciona todas as colunas V4.0
            query = f"SELECT id, disciplina, enunciado, alternativas, resposta_correta, dificuldade, justificativa, dica, formula FROM questoes WHERE disciplina IN ({placeholders})"
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
                logger.info(f"Colunas disponíveis: {list(colunas_disponiveis)}")

                for row_num, row in enumerate(resultados):
                    row_id_log = f"linha_{row_num}"
                    try:
                        row_id_log = f"ID_{row['id']}" if 'id' in colunas_disponiveis else row_id_log

                        logger.debug(f"Processando questão {row_id_log}...")
                        # Tratamento JSON robusto
                        alternativas_dict = {}
                        alternativas_json = row['alternativas'] if 'alternativas' in colunas_disponiveis else None
                        if alternativas_json and isinstance(alternativas_json, str):
                            try:
                                alternativas_dict = json.loads(alternativas_json)
                                if not isinstance(alternativas_dict, dict):
                                    logger.error(f"JSON 'alternativas' não é dict na Q {row_id_log}. Conteúdo: {alternativas_json}")
                                    alternativas_dict = {"ERRO": "Formato"}
                            except json.JSONDecodeError as json_err:
                                logger.error(f"Erro JSONDecode 'alternativas' Q {row_id_log}: {json_err}. Conteúdo: {alternativas_json}")
                                alternativas_dict = {"ERRO": "JSON inválido"}
                        elif alternativas_json is not None:
                             logger.warning(f"'alternativas' não é string na Q {row_id_log}. Tipo: {type(alternativas_json)}. Conteúdo: {alternativas_json}")

                        # Tratamento dados ausentes
                        disciplina_val = row['disciplina'] if 'disciplina' in colunas_disponiveis and row['disciplina'] else 'Sem Disciplina'
                        enunciado_val = row['enunciado'] if 'enunciado' in colunas_disponiveis and row['enunciado'] else '[Enunciado Ausente]'
                        resposta_val = row['resposta_correta'] if 'resposta_correta' in colunas_disponiveis and row['resposta_correta'] else None

                        if not resposta_val:
                            logger.error(f"Resposta correta VAZIA/NULA na Q {row_id_log}. Pulando.")
                            continue

                        questao = {
                            'id': row['id'] if 'id' in colunas_disponiveis else row_num + 1,
                            'enunciado': enunciado_val,
                            'materia': disciplina_val,
                            'alternativas': alternativas_dict,
                            'resposta_correta': resposta_val,
                            'dificuldade': row['dificuldade'] if 'dificuldade' in colunas_disponiveis and row['dificuldade'] else 'Médio',
                            'justificativa': row['justificativa'] if 'justificativa' in colunas_disponiveis else None,
                            'dica': row['dica'] if 'dica' in colunas_disponiveis else None, # Nova coluna
                            'formula': row['formula'] if 'formula' in colunas_disponiveis else None # Nova coluna
                        }
                        questoes.append(questao)
                        logger.debug(f"Questão {row_id_log} processada OK.")

                    except KeyError as key_err: logger.error(f"Erro Chave Q {row_id_log}: {key_err}. Colunas: {list(colunas_disponiveis)}"); continue
                    except Exception as parse_err: logger.error(f"Erro inesperado Q {row_id_log}: {parse_err}", exc_info=True); continue

            else: logger.warning(f"Nenhum resultado DB para query com params: {params}")

            logger.info(f"Carregadas {len(questoes)} questões válidas.")
            return questoes

        except sqlite3.Error as db_err: logger.error(f"Erro SQLite crítico carregar questões: {db_err}", exc_info=True); raise db_err
        except Exception as e: logger.error(f"Erro geral crítico carregar questões: {e}", exc_info=True); raise e
        finally:
            if conn: conn.close(); logger.debug("Conexão DB fechada em _carregar_questoes_simulado.")

    def registrar_resposta(self, simulado_id: str, questao_index: int, alternativa: str, tempo_gasto_na_questao: float) -> bool:
        '''Registra a resposta do usuário.'''
        simulado = self.simulados_ativos.get(simulado_id)
        if not simulado: logger.warning(f"Registro: Simulado {simulado_id} não ativo."); return False
        questoes = simulado.get('questoes', [])
        if not (0 <= questao_index < len(questoes)): logger.warning(f"Registro: Índice {questao_index} inválido para {simulado_id}."); return False

        questao = questoes[questao_index]
        acertou = str(alternativa).upper() == str(questao.get('resposta_correta', '')).upper()

        resposta = {'questao_id': questao.get('id'), 'alternativa_escolhida': alternativa, 'acertou': acertou,
                    'tempo_gasto': tempo_gasto_na_questao, 'timestamp': datetime.now().isoformat()}
        simulado['respostas'][questao_index] = resposta

        # Simplificado: Apenas registra a resposta, navegação é tratada no frontend
        logger.info(f"Registro: Simulado {simulado_id}, Q {questao_index}. Acertou: {acertou}")
        return True

    def finalizar_simulado(self, simulado_id: str) -> Optional[Dict[str, Any]]:
        '''Marca simulado como finalizado, calcula relatório, salva e remove da memória.'''
        simulado = self.simulados_ativos.get(simulado_id)
        if not simulado: logger.warning(f"Finalizar: Simulado {simulado_id} inexistente."); return None
        if simulado.get('status') == 'finalizado': logger.warning(f"Finalizar: Simulado {simulado_id} já finalizado."); return simulado.get('relatorio')

        simulado['fim'] = datetime.now(); simulado['status'] = 'finalizado'
        try:
            relatorio = self._gerar_relatorio(simulado)
            simulado['relatorio'] = relatorio
        except Exception as e_report:
            logger.error(f"Erro ao gerar relatório {simulado_id}: {e_report}", exc_info=True)
            relatorio = {"error": "Falha ao gerar relatório."} # Relatório de erro

        self._salvar_historico(simulado)
        if simulado_id in self.simulados_ativos: del self.simulados_ativos[simulado_id]; logger.info(f"Simulado {simulado_id} removido da memória.")
        logger.info(f"Simulado {simulado_id} finalizado.")
        return relatorio


    def _gerar_relatorio(self, simulado: Dict[str, Any]) -> Dict[str, Any]:
        '''Calcula estatísticas e gera recomendações.'''
        respostas = simulado.get('respostas', {}); questoes = simulado.get('questoes', [])
        total_q_plan = len(questoes); q_resp_obj = list(respostas.values()); q_resp_count = len(q_resp_obj)
        acertos = sum(1 for r in q_resp_obj if r.get('acertou', False))
        perc_acerto = (acertos / q_resp_count * 100) if q_resp_count > 0 else 0.0
        tempo_total_seg = sum(float(r.get('tempo_gasto', 0.0)) for r in q_resp_obj if isinstance(r.get('tempo_gasto'), (int, float)))

        stats_materia = {}
        for q_idx, resp in respostas.items():
            try:
                if q_idx < len(questoes):
                    q = questoes[q_idx]; materia = q.get('materia', 'Desconhecida') or 'Desconhecida'
                    if materia not in stats_materia: stats_materia[materia] = {'total': 0, 'acertos': 0, 'tempo': 0.0}
                    stats_materia[materia]['total'] += 1; stats_materia[materia]['tempo'] += float(resp.get('tempo_gasto', 0.0))
                    if resp.get('acertou', False): stats_materia[materia]['acertos'] += 1
                else: logger.warning(f"Índice {q_idx} inválido relatório.")
            except Exception as e_stat: logger.error(f"Erro stat Q {q_idx}: {e_stat}", exc_info=True)

        for mat, stats in stats_materia.items():
            total = stats.get('total', 0); stats['percentual'] = round((stats['acertos']/total*100),1) if total > 0 else 0.0; stats['tempo_medio'] = round(stats['tempo']/total,1) if total > 0 else 0.0

        recomendacoes = self._gerar_recomendacoes(stats_materia)
        relatorio_final = {
            'geral': {'total_questoes_planejadas': total_q_plan, 'questoes_respondidas': q_resp_count, 'acertos': acertos, 'erros': q_resp_count - acertos,
                      'percentual_acerto': round(perc_acerto, 1), 'tempo_total_minutos': round(tempo_total_seg / 60, 1),
                      'tempo_medio_questao': round(tempo_total_seg / q_resp_count, 1) if q_resp_count > 0 else 0.0},
            'por_materia': stats_materia, 'recomendacoes': recomendacoes,
            'questoes_com_detalhes': self._preparar_questoes_detalhadas(simulado)
        }
        logger.info(f"Relatório gerado {simulado['id']}: {acertos}/{q_resp_count}")
        return relatorio_final

    def _gerar_recomendacoes(self, estatisticas_materia: Dict[str, Dict[str, Any]]) -> List[str]:
        '''Gera recomendações em HTML.'''
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

    def _preparar_questoes_detalhadas(self, simulado: Dict[str, Any]) -> List[Dict[str, Any]]:
        '''Prepara lista de questões com detalhes para revisão.'''
        detalhes = []
        questoes = simulado.get('questoes', []); respostas = simulado.get('respostas', {})
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

    def _salvar_historico(self, simulado: Dict[str, Any]):
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

# --- Instância Global ---
sistema_simulado = SistemaSimulado()

# --- Funções de Banco de Dados ---
def get_db_connection() -> Optional[sqlite3.Connection]:
    '''Estabelece conexão com o banco de dados SQLite.'''
    try:
        conn = sqlite3.connect(DATABASE, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"❌ Erro CRÍTICO conexão DB ({DATABASE}): {e}", exc_info=True)
        return None

def criar_tabelas_se_necessario() -> bool:
    '''Verifica e cria todas as tabelas V4.0 se não existirem.'''
    conn = get_db_connection()
    if not conn: logger.critical("Falha CRÍTICA criar tabelas: Sem DB."); return False
    try:
        cursor = conn.cursor()
        # Tabela de questões (V4.0 - com dica e formula)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disciplina TEXT NOT NULL,
                enunciado TEXT NOT NULL,
                alternativas TEXT NOT NULL, -- JSON TEXT {'A': '...', 'B': ...}
                resposta_correta TEXT NOT NULL, -- "A", "B", etc.
                dificuldade TEXT DEFAULT 'Médio',
                justificativa TEXT,
                dica TEXT,                -- << NOVO
                formula TEXT,             -- << NOVO
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Outras tabelas (mesma estrutura V3.x)
        cursor.execute("CREATE TABLE IF NOT EXISTS redacoes (id INTEGER PRIMARY KEY, titulo TEXT, tema TEXT, texto_base TEXT, dicas TEXT, criterios_avaliacao TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS historico_simulados (id INTEGER PRIMARY KEY, simulado_id TEXT UNIQUE NOT NULL, config TEXT, relatorio TEXT, data_inicio TIMESTAMP, data_fim TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS historico_redacoes (id INTEGER PRIMARY KEY, redacao_id INTEGER, texto_redacao TEXT, correcao TEXT, nota INTEGER, feedback TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (redacao_id) REFERENCES redacoes (id) ON DELETE SET NULL)")
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questoes_disciplina ON questoes(disciplina)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_simulados_data ON historico_simulados(data_fim)")
        conn.commit()
        # logger.info("Verificação/Criação de tabelas concluída.") # Log menos verboso
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
    return jsonify({"status": "online", "database_status": "connected" if db_ok else "error", "version": "4.0"}), status_code

@app.route('/api/materias')
def materias():
    # (Manter código da V3.1 - Já era robusto)
    logger.debug("Acessando API /api/materias")
    if not criar_tabelas_se_necessario():
         logger.error("Falha ao verificar/criar tabelas na API /api/materias.")
         return jsonify({"error": "Erro ao inicializar o banco de dados."}), 500
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Erro de conexão com o banco de dados."}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT disciplina, COUNT(*) as total FROM questoes GROUP BY disciplina HAVING COUNT(*) > 0 ORDER BY disciplina ASC")
        rows = cursor.fetchall()
        materias_lista = []; estatisticas_dict = {}; total_geral = 0
        for row in rows: mat = row['disciplina']; total = row['total']; materias_lista.append(mat); estatisticas_dict[mat] = {'total': total}; total_geral += total
        logger.info(f"API /api/materias retornou {len(materias_lista)} matérias.")
        return jsonify({"materias": materias_lista, "estatisticas": estatisticas_dict, "total_geral": total_geral})
    except sqlite3.OperationalError as op_err: logger.error(f"Erro Op SQLite /api/materias: {op_err}", exc_info=True); criar_tabelas_se_necessario(); return jsonify({"error": "Erro operacional DB. Tente."}), 500
    except sqlite3.Error as db_err: logger.error(f"Erro SQLite /api/materias: {db_err}", exc_info=True); return jsonify({"error": "Erro consulta DB."}), 500
    except Exception as e: logger.error(f"Erro geral /api/materias: {e}", exc_info=True); return jsonify({"error": "Erro interno."}), 500
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

        # Validações
        materias_req = data.get('materias')
        if not materias_req or not isinstance(materias_req, list) or len(materias_req) == 0: return jsonify({"success": False, "error": "Seleção de matérias inválida."}), 400
        try: quantidade_int = int(data.get('quantidade_total', 50)); assert quantidade_int > 0
        except: return jsonify({"success": False, "error": "Quantidade inválida."}), 400
        try: tempo_int = int(data.get('tempo_minutos', 180)); assert tempo_int > 0
        except: return jsonify({"success": False, "error": "Tempo inválido."}), 400

        config = {'materias': materias_req, 'quantidade_total': quantidade_int, 'tempo_minutos': tempo_int, 'aleatorio': bool(data.get('aleatorio', True))}
        logger.info(f"Configuração recebida: {config}")

        user_id = session.get('user_id', 'anon_' + str(random.randint(10000, 99999)))
        simulado_id = sistema_simulado.iniciar_simulado(user_id, config) # Pode retornar None

        if not simulado_id:
             logger.error("Falha ao iniciar simulado (iniciar_simulado retornou None).")
             return jsonify({"success": False, "error": "Não foi possível iniciar. Verifique se há questões ou consulte logs."}), 500

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
    # (Manter código da V3.1 - Já era robusto)
    logger.debug(f"Acessando API GET /api/simulado/{simulado_id}/questao/{questao_index}")
    simulado = sistema_simulado.simulados_ativos.get(simulado_id)
    if not simulado: return jsonify({"error": "Simulado não ativo."}), 404
    questoes_list = simulado.get('questoes', [])
    if not (0 <= questao_index < len(questoes_list)): return jsonify({"error": "Índice inválido."}), 404
    questao = questoes_list[questao_index].copy()
    questao.pop('resposta_correta', None); questao.pop('justificativa', None)
    return jsonify({"questao": questao, "numero_questao": questao_index + 1, "total_questoes": len(questoes_list)})


@app.route('/api/simulado/<simulado_id>/responder', methods=['POST'])
def responder_questao_api(simulado_id):
    # (Manter código da V3.1 - Já era robusto)
    logger.debug(f"Acessando API POST /api/simulado/{simulado_id}/responder")
    try:
        data = request.get_json(); assert data
        q_idx = int(data['questao_index']); alt = str(data['alternativa']); tempo = float(data.get('tempo_gasto', 0))
        simulado = sistema_simulado.simulados_ativos.get(simulado_id); assert simulado
        questoes = simulado.get('questoes', []); assert 0 <= q_idx < len(questoes)
        q_orig = questoes[q_idx]; resp_correta = str(q_orig.get('resposta_correta', '')).upper(); acertou = alt.upper() == resp_correta
        success = sistema_simulado.registrar_resposta(simulado_id, q_idx, alt, tempo)
        if not success: raise Exception("Falha registro interno")
        # Retorna todos os dados de feedback
        return jsonify({"success": True, "acertou": acertou, "resposta_correta": resp_correta,
                        "justificativa": q_orig.get('justificativa'),
                        "dica": q_orig.get('dica'),
                        "formula": q_orig.get('formula')})
    except Exception as e: logger.error(f"Erro API /responder: {e}", exc_info=True); return jsonify({"success": False, "error": "Erro ao processar resposta."}), 500


@app.route('/api/simulado/<simulado_id>/finalizar', methods=['POST'])
def finalizar_simulado_api(simulado_id):
    # (Manter código da V3.1 - Já era robusto)
    logger.debug(f"Acessando API POST /api/simulado/{simulado_id}/finalizar")
    try:
        relatorio = sistema_simulado.finalizar_simulado(simulado_id)
        if relatorio: return jsonify({"success": True, "relatorio": relatorio})
        else: return jsonify({"success": False, "error": "Simulado não ativo."}), 404
    except Exception as e: logger.error(f"Erro API /finalizar: {e}", exc_info=True); return jsonify({"success": False, "error": "Erro ao finalizar."}), 500


# --- API do Sistema de Redação (com geração simulada de temas) ---
def gerar_temas_exemplo(quantidade=50) -> List[Dict[str, Any]]:
    ''' Simula a geração de temas de redação. '''
    # (Manter código da V4.0)
    temas_base = [
        ("Impacto das Redes Sociais na Saúde Mental dos Jovens", "Discuta os efeitos positivos e negativos...", "Foque em ansiedade, comparação social."),
        ("Desmatamento na Amazônia e suas Consequências Globais", "Analise as causas e os impactos ambientais e sociais...", "Cite dados recentes, acordos internacionais."),
        ("Inteligência Artificial no Mercado de Trabalho Brasileiro", "Debata as oportunidades e os desafios...", "Aborde automação, novas profissões, desigualdade."),
        ("Mobilidade Urbana Sustentável nas Grandes Cidades", "Proponha soluções para os problemas de trânsito e poluição...", "Pense em transporte público, ciclovias, carros elétricos."),
        ("A Persistência da Violência Contra a Mulher no Brasil", "Analise as raízes culturais e as medidas de combate...", "Cite a Lei Maria da Penha, feminicídio."),
        ("Democratização do Acesso ao Cinema no Brasil", "Discuta a importância cultural e os obstáculos existentes...", "Fale sobre preço dos ingressos, distribuição geográfica."),
        ("Desafios da Educação a Distância no Ensino Básico", "Avalie os prós e contras e o impacto na aprendizagem...", "Considere acesso à tecnologia, interação aluno-professor."),
        ("Fake News e seu Impacto na Democracia Brasileira", "Analise como a desinformação afeta o processo eleitoral e a sociedade...", "Discuta checagem de fatos, regulação."),
        ("Importância da Vacinação para a Saúde Coletiva", "Debata os movimentos antivacina e as consequências...", "Cite doenças erradicadas, campanhas de conscientização."),
        ("Obsolescência Programada e seus Impactos Ambientais", "Discuta as práticas da indústria e as alternativas...", "Fale sobre lixo eletrônico, economia circular.")
    ]
    temas_gerados = []
    for i in range(quantidade):
        base = temas_base[i % len(temas_base)]
        temas_gerados.append({
            "id": i + 1, "titulo": f"{base[0]} (Tema {i+1})", "tema": base[1],
            "texto_base": f"Texto base simulado para o tema {i+1}.", "dicas": base[2]
        })
    return temas_gerados

@app.route('/api/redacoes/temas')
def get_temas_redacao():
    '''Retorna lista simulada de temas de redação.'''
    # (Manter código da V4.0)
    logger.debug("Acessando API GET /api/redacoes/temas (simulado)")
    try:
        temas = gerar_temas_exemplo(50)
        logger.info(f"Retornando {len(temas)} temas de redação simulados.")
        return jsonify({"temas": temas})
    except Exception as e:
        logger.error(f"Erro ao gerar temas simulados: {e}", exc_info=True)
        return jsonify({"temas": [], "error": "Erro interno ao gerar temas."}), 500


@app.route('/api/redacoes/corrigir', methods=['POST'])
def corrigir_redacao_api():
    # (Manter código V4.0 com estrutura de feedback melhorada)
    logger.debug("Acessando API POST /api/redacoes/corrigir")
    try:
        data = request.get_json(); assert data; r_id = data['redacao_id']; texto = data['texto_redacao']; assert r_id and texto
        # Simulação
        nota = min(int(len(texto)/10.0 + random.uniform(200,400)), 1000)
        corr = {
            'nota': nota,
            'competencias': {
                 'c1': {'nome': 'Domínio da norma culta', 'nota': random.randint(120, 200), 'comentario': 'Avaliação C1 simulada.'},
                 'c2': {'nome': 'Compreensão do tema e repertório', 'nota': random.randint(120, 200), 'comentario': 'Avaliação C2 simulada.'},
                 'c3': {'nome': 'Seleção e organização de informações', 'nota': random.randint(100, 200), 'comentario': 'Avaliação C3 simulada.'},
                 'c4': {'nome': 'Coesão e coerência', 'nota': random.randint(120, 200), 'comentario': 'Avaliação C4 simulada.'},
                 'c5': {'nome': 'Proposta de intervenção', 'nota': random.randint(100, 200), 'comentario': 'Avaliação C5 simulada.'}
             },
            'feedback_geral': f'Correção simulada. Nota: {nota}. [Feedback geral simulado].',
            'sugestoes_melhoria': ['Sugestão 1 simulada.', 'Sugestão 2 simulada.', 'Sugestão 3 simulada.']
        }
        logger.info(f"Redação ID {r_id} corrigida (simulada). Nota: {nota}")
        # Salvar histórico (simplificado)
        conn = get_db_connection()
        if conn:
            try: cur = conn.cursor(); cur.execute('INSERT INTO historico_redacoes (redacao_id, texto_redacao, correcao, nota, feedback) VALUES (?, ?, ?, ?, ?)', (r_id, texto, json.dumps(corr), corr['nota'], corr['feedback_geral'])); conn.commit()
            finally: conn.close()
        return jsonify({"success": True, "correcao": corr})
    except Exception as e: logger.error(f"Erro API /corrigir: {e}", exc_info=True); return jsonify({"success": False, "error": "Erro interno."}), 500


# --- API Dashboard ---
@app.route('/api/dashboard/estatisticas')
def get_estatisticas_dashboard():
    # (Manter código da V3.1 - Já era robusto)
    # ... (código completo da V3.1 para esta rota) ...
    logger.debug("Acessando API GET /api/dashboard/estatisticas")
    if not criar_tabelas_se_necessario(): return jsonify({"estatisticas": {}, "error": "Erro DB init."}), 500
    conn = get_db_connection();
    if not conn: return jsonify({"estatisticas": {}, "error": "Erro conexão DB."}), 500
    try:
        cursor = conn.cursor(); cursor.execute("SELECT COUNT(*) as total FROM questoes"); res = cursor.fetchone(); total_questoes_banco = res['total'] if res else 0
        cursor.execute("SELECT id, relatorio, data_fim FROM historico_simulados ORDER BY data_fim ASC"); todos_relatorios = cursor.fetchall()
        historico_evolucao, global_stats_materia, tempo_total_estudo, total_questoes_respondidas = [], {}, 0.0, 0
        for row in todos_relatorios:
            row_id = row['id'] if 'id' in row.keys() else 'N/A'
            try:
                relatorio = json.loads(row['relatorio']) if row['relatorio'] else {}; data_fim_str = row['data_fim']
                if not data_fim_str: continue
                data_fim_dt = datetime.fromisoformat(data_fim_str); geral = relatorio.get('geral', {})
                historico_evolucao.append({'data': data_fim_dt.strftime('%d/%m'),'percentual': float(geral.get('percentual_acerto', 0.0))})
                tempo_total_estudo += float(geral.get('tempo_total_minutos', 0.0)); total_questoes_respondidas += int(geral.get('questoes_respondidas', 0))
                for materia, stats in relatorio.get('por_materia', {}).items():
                    if materia not in global_stats_materia: global_stats_materia[materia] = {'acertos': 0, 'total': 0}
                    global_stats_materia[materia]['acertos'] += int(stats.get('acertos', 0)); global_stats_materia[materia]['total'] += int(stats.get('total', 0))
            except json.JSONDecodeError as json_err: logger.error(f"Erro JSONDecode relatório ID {row_id}: {json_err}")
            except Exception as e_proc: logger.error(f"Erro processar relatório ID {row_id}: {e_proc}", exc_info=True)
        desempenho_global_materia = {m: round((s['acertos'] * 100.0 / s['total']), 1) if s['total'] > 0 else 0.0 for m, s in global_stats_materia.items()}
        historico_recente_formatado = []
        for row in reversed(todos_relatorios[-10:]):
            try:
                relatorio = json.loads(row['relatorio']) if row['relatorio'] else {}; data_fim_str = row['data_fim']
                if data_fim_str: historico_recente_formatado.append({'data': datetime.fromisoformat(data_fim_str).strftime('%d/%m/%Y %H:%M'), 'geral': relatorio.get('geral', {})})
            except Exception as e_hist: logger.error(f"Erro formatar histórico recente: {e_hist}")
        media_geral = round(sum(h['percentual'] for h in historico_evolucao) / len(historico_evolucao), 1) if historico_evolucao else 0.0
        logger.info("Estatísticas dashboard calculadas.")
        return jsonify({"estatisticas": {"total_questoes_banco": total_questoes_banco, "total_simulados_realizados": len(todos_relatorios), "total_questoes_respondidas": total_questoes_respondidas, "tempo_total_estudo_min": round(tempo_total_estudo, 1), "media_geral_percentual": media_geral, "evolucao_desempenho": historico_evolucao, "desempenho_global_materia": desempenho_global_materia, "historico_recente": historico_recente_formatado}})
    except sqlite3.Error as db_err: logger.error(f"Erro SQLite API stats: {db_err}", exc_info=True); return jsonify({"estatisticas": {}, "error": "Erro DB stats."}), 500
    except Exception as e: logger.error(f"Erro geral API stats: {e}", exc_info=True); return jsonify({"estatisticas": {}, "error": "Erro interno."}), 500
    finally:
        if conn: conn.close()


# --- Rotas Estáticas ---
@app.route('/static/<path:filename>')
def serve_static_files(filename): return send_from_directory('static', filename)

# --- Tratamento de Erros ---
@app.errorhandler(404)
def not_found_error(error):
    # (Manter código da V3.1)
    logger.warning(f"Rota 404: {request.url}")
    if request.path.startswith('/api/'): return jsonify({"error": "Endpoint não encontrado"}), 404
    try: return render_template('error.html', mensagem="Página não encontrada (404)."), 404
    except: return "<h1>Erro 404</h1>", 404

@app.errorhandler(500)
def internal_error(error):
    # (Manter código da V3.1)
    error_trace = traceback.format_exc()
    logger.error(f"Erro 500 na rota {request.url}:\n{error_trace}")
    if request.path.startswith('/api/'): return jsonify({"error": "Erro interno servidor."}), 500 # PROD
    try: return render_template('error.html', mensagem="Erro interno do servidor (500)."), 500
    except: return "<h1>Erro 500</h1>", 500


# --- Inicialização da Aplicação ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    if not criar_tabelas_se_necessario(): logger.critical("########## FALHA AO INICIALIZAR DB ##########")
    logger.info(f"========= INICIANDO App V4.0 NA PORTA {port} =========") # Versão atualizada
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    use_debug = not is_production and os.environ.get('FLASK_DEBUG') == '1'
    if use_debug: logger.warning("############## MODO DEBUG ATIVO ##############"); app.run(host='0.0.0.0', port=port, debug=True)
    else: logger.info("Rodando em modo PRODUÇÃO (debug=False)"); app.run(host='0.0.0.0', port=port, debug=False)

