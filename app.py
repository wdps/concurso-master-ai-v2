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
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_secret_key_that_is_very_secure_and_long_enough_12345')

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
        # ** Ponto Crítico: Envolver em try-except aqui também **
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

    # --- Funções registrar_resposta, finalizar_simulado, _gerar_relatorio, etc. (sem mudanças significativas) ---
    # ... (O restante da classe SistemaSimulado permanece o mesmo da V3.1) ...
    # (Cole aqui o restante das funções da classe SistemaSimulado da sua versão V3.1)
    # ... (exemplo: registrar_resposta, finalizar_simulado, _gerar_relatorio, _gerar_recomendacoes, _preparar_questoes_detalhadas, _salvar_historico) ...
    def registrar_resposta(self, simulado_id, questao_index, alternativa, tempo_gasto_na_questao):
        '''
        Registra a resposta do usuário para uma questão específica no simulado ativo.
        Retorna True se bem-sucedido, False caso contrário.
        '''
        simulado = self.simulados_ativos.get(simulado_id)
        if not simulado:
            logger.warning(f"Tentativa de resposta para simulado {simulado_id} inexistente ou finalizado.")
            return False

        # Validação do índice da questão
        if not isinstance(questao_index, int) or questao_index < 0 or questao_index >= len(simulado.get('questoes', [])): # Checa se 'questoes' existe
            logger.warning(f"Índice de questão inválido ({questao_index}) para simulado {simulado_id}.")
            return False

        questao = simulado['questoes'][questao_index]
        # Comparação segura como string e case-insensitive
        acertou = str(alternativa).upper() == str(questao.get('resposta_correta', '')).upper()

        resposta = {
            'questao_id': questao.get('id'),
            'alternativa_escolhida': alternativa,
            'acertou': acertou,
            'tempo_gasto': tempo_gasto_na_questao, # Tempo em segundos
            'timestamp': datetime.now().isoformat() # Formato padrão ISO 8601
        }

        # Armazena a resposta no dicionário do simulado, usando o índice como chave
        simulado['respostas'][questao_index] = resposta
        logger.info(f"Resposta registrada para simulado {simulado_id}, questão {questao_index}. Acertou: {acertou}")
        return True

    def finalizar_simulado(self, simulado_id):
        '''
        Marca um simulado como finalizado, calcula o relatório, salva no histórico
        e remove da memória ativa. Retorna o relatório calculado ou None.
        '''
        simulado = self.simulados_ativos.get(simulado_id)
        if not simulado:
             logger.warning(f"Tentativa de finalizar simulado {simulado_id} inexistente.")
             return None

        # Evita finalizar duas vezes
        if simulado.get('status') == 'finalizado':
             logger.warning(f"Simulado {simulado_id} já está finalizado. Retornando relatório.")
             return simulado.get('relatorio')

        simulado['fim'] = datetime.now()
        simulado['status'] = 'finalizado'

        try:
            relatorio = self._gerar_relatorio(simulado)
            simulado['relatorio'] = relatorio # Guarda o relatório
        except Exception as e_report:
            logger.error(f"Erro ao gerar relatório para simulado {simulado_id}: {e_report}", exc_info=True)
            # Mesmo com erro no relatório, tenta salvar o histórico e remover da memória
            relatorio = {"error": "Falha ao gerar relatório detalhado."} # Relatório de erro

        # Salva o resultado no banco de dados (mesmo se relatório falhar)
        self._salvar_historico(simulado)

        # Remove o simulado da lista de ativos para liberar memória
        if simulado_id in self.simulados_ativos:
             del self.simulados_ativos[simulado_id]
             logger.info(f"Simulado {simulado_id} removido da memória ativa.")

        logger.info(f"Simulado {simulado_id} finalizado.")
        # Retorna o relatório (ou o objeto de erro se a geração falhou)
        return relatorio


    def _gerar_relatorio(self, simulado):
        '''
        Calcula as estatísticas do simulado (geral e por matéria)
        e gera recomendações com base nas respostas registradas.
        Retorna um dicionário com o relatório completo.
        *** VERSÃO MAIS ROBUSTA ***
        '''
        respostas = simulado.get('respostas', {}) # Dict {index: resposta}
        questoes = simulado.get('questoes', [])
        total_questoes_planejadas = len(questoes)
        questoes_respondidas_obj = list(respostas.values())
        questoes_respondidas_count = len(questoes_respondidas_obj)

        acertos = sum(1 for r in questoes_respondidas_obj if r.get('acertou', False))
        percentual_acerto = (acertos / questoes_respondidas_count * 100) if questoes_respondidas_count > 0 else 0.0
        # Somar apenas se tempo_gasto for número
        tempo_total_gasto_seg = sum(float(r.get('tempo_gasto', 0.0)) for r in questoes_respondidas_obj if isinstance(r.get('tempo_gasto'), (int, float)))

        estatisticas_materia = {}
        for questao_index, resposta in respostas.items():
            try:
                # Acessa a questão correspondente com segurança
                if questao_index < len(questoes):
                    questao = questoes[questao_index]
                    materia = questao.get('materia', 'Desconhecida') # Fallback
                    if not materia: materia = 'Desconhecida' # Trata string vazia

                    if materia not in estatisticas_materia:
                        estatisticas_materia[materia] = {'total': 0, 'acertos': 0, 'tempo': 0.0}

                    estatisticas_materia[materia]['total'] += 1
                    tempo_gasto_resp = float(resposta.get('tempo_gasto', 0.0)) # Garante float
                    estatisticas_materia[materia]['tempo'] += tempo_gasto_resp
                    if resposta.get('acertou', False):
                        estatisticas_materia[materia]['acertos'] += 1
                else:
                     logger.warning(f"Índice de resposta {questao_index} inválido ao gerar relatório.")
            except Exception as e_stat:
                logger.error(f"Erro ao processar estatística para Q index {questao_index}: {e_stat}", exc_info=True)


        # Calcula percentuais e médias por matéria com arredondamento
        for materia, stats in estatisticas_materia.items():
            total_materia = stats.get('total', 0)
            acertos_materia = stats.get('acertos', 0)
            tempo_materia = stats.get('tempo', 0.0)
            stats['percentual'] = round((acertos_materia / total_materia * 100), 1) if total_materia > 0 else 0.0
            stats['tempo_medio'] = round(tempo_materia / total_materia, 1) if total_materia > 0 else 0.0

        recomendacoes = self._gerar_recomendacoes(estatisticas_materia)

        # Monta o dicionário final do relatório
        relatorio_final = {
            'geral': {
                'total_questoes_planejadas': total_questoes_planejadas,
                'questoes_respondidas': questoes_respondidas_count,
                'acertos': acertos,
                'erros': questoes_respondidas_count - acertos,
                'percentual_acerto': round(percentual_acerto, 1),
                'tempo_total_minutos': round(tempo_total_gasto_seg / 60, 1),
                'tempo_medio_questao': round(tempo_total_gasto_seg / questoes_respondidas_count, 1) if questoes_respondidas_count > 0 else 0.0
            },
            'por_materia': estatisticas_materia,
            'recomendacoes': recomendacoes,
            'questoes_com_detalhes': self._preparar_questoes_detalhadas(simulado)
        }
        logger.info(f"Relatório gerado para simulado {simulado['id']}. Acertos: {acertos}/{questoes_respondidas_count}")
        return relatorio_final

    def _gerar_recomendacoes(self, estatisticas_materia):
        '''
        Gera uma lista de strings (HTML formatado) com recomendações
        com base no percentual de acerto por matéria.
        '''
        recomendacoes = []
        # Ordena as matérias pelo menor percentual de acerto primeiro
        materias_ordenadas = sorted(estatisticas_materia.items(), key=lambda item: item[1].get('percentual', 0.0))

        for materia, stats in materias_ordenadas:
            percentual = stats.get('percentual', 0.0)
            if percentual < 50:
                recomendacoes.append(f"<li class='list-group-item border-start-0 border-end-0 border-top-0 border-danger border-3'><i class='fas fa-exclamation-triangle text-danger me-2'></i> <strong>Foco Urgente:</strong> {materia} ({percentual:.1f}%)</li>")
            elif percentual < 70:
                recomendacoes.append(f"<li class='list-group-item border-start-0 border-end-0 border-top-0 border-warning border-3'><i class='fas fa-book-open text-warning me-2'></i> <strong>Revisar:</strong> {materia} ({percentual:.1f}%)</li>")
            elif percentual < 90:
                recomendacoes.append(f"<li class='list-group-item border-start-0 border-end-0 border-top-0 border-info border-3'><i class='fas fa-check text-info me-2'></i> <strong>Bom Desempenho:</strong> {materia} ({percentual:.1f}%)</li>")
            else: # >= 90
                recomendacoes.append(f"<li class='list-group-item border-start-0 border-end-0 border-top-0 border-success border-3'><i class='fas fa-star text-success me-2'></i> <strong>Excelente:</strong> {materia} ({percentual:.1f}%)</li>")

        if not recomendacoes:
            recomendacoes.append("<li class='list-group-item border-0 text-muted'><i class='fas fa-chart-line text-primary me-2'></i> Complete um simulado para ver suas recomendações.</li>")

        return recomendacoes


    def _preparar_questoes_detalhadas(self, simulado):
        '''
        Cria uma lista de dicionários, cada um representando uma questão do simulado
        com a resposta do usuário e informações adicionais para a tela de revisão.
        '''
        detalhes = []
        questoes = simulado.get('questoes', [])
        respostas = simulado.get('respostas', {})

        for i, questao in enumerate(questoes):
            resposta_usuario_obj = respostas.get(i) # Busca a resposta pelo índice i
            detalhe_questao = {
                'numero': i + 1,
                'enunciado': questao.get('enunciado', 'Enunciado não disponível'),
                'materia': questao.get('materia', 'Desconhecida'),
                'alternativas': questao.get('alternativas', {}),
                'resposta_correta': questao.get('resposta_correta'),
                'justificativa': questao.get('justificativa'),
                'dica': questao.get('dica'),
                'formula': questao.get('formula'),
                # Inclui informações da resposta do usuário, se existir
                'resposta_usuario': resposta_usuario_obj.get('alternativa_escolhida') if resposta_usuario_obj else None,
                'acertou': resposta_usuario_obj.get('acertou') if resposta_usuario_obj else None,
                'tempo_gasto': resposta_usuario_obj.get('tempo_gasto') if resposta_usuario_obj else None
            }
            detalhes.append(detalhe_questao)
        return detalhes


    def _salvar_historico(self, simulado):
        '''
        Salva o registro final do simulado (configuração, relatório, datas)
        na tabela 'historico_simulados' do banco de dados.
        '''
        conn = get_db_connection()
        if not conn:
            logger.error(f"Falha ao salvar histórico do simulado {simulado.get('id', 'N/A')}: Sem conexão com DB.")
            return

        simulado_id_str = simulado.get('id', '')
        # Usar .get com default vazio evita erros se config/relatorio não existirem
        config_json = json.dumps(simulado.get('config', {}))
        relatorio_json = json.dumps(simulado.get('relatorio', {}))
        # Trata caso inicio/fim sejam None
        inicio_iso = simulado.get('inicio').isoformat() if simulado.get('inicio') else None
        fim_iso = simulado.get('fim').isoformat() if simulado.get('fim') else None

        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_simulados
                (simulado_id, config, relatorio, data_inicio, data_fim)
                VALUES (?, ?, ?, ?, ?)
            ''', (simulado_id_str, config_json, relatorio_json, inicio_iso, fim_iso))
            conn.commit()
            logger.info(f"Histórico do simulado {simulado_id_str} salvo no DB com sucesso.")
        except sqlite3.IntegrityError:
             logger.error(f"Erro de Integridade: Simulado ID {simulado_id_str} já existe no histórico. Atualização não implementada.")
             conn.rollback() # Não salva se o ID já existe
        except sqlite3.Error as db_err:
             logger.error(f"Erro de SQLite ao salvar histórico ({simulado_id_str}): {db_err}", exc_info=True)
             conn.rollback()
        except Exception as e:
            logger.error(f"Erro geral ao salvar histórico ({simulado_id_str}) no DB: {e}", exc_info=True)
            conn.rollback()
        finally:
            if conn:
                conn.close()


# --- Funções de Banco de Dados ---

def get_db_connection():
    '''Estabelece conexão com o banco de dados SQLite.'''
    try:
        conn = sqlite3.connect(DATABASE)
        # Otimizações podem ser benéficas
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row # Retorna linhas como objetos tipo dicionário
        return conn
    except Exception as e:
        logger.error(f"❌ Erro CRÍTICO na conexão com o DB ({DATABASE}): {e}", exc_info=True)
        return None

def criar_tabelas_se_necessario():
    '''Verifica e cria todas as tabelas do schema V3.0 se não existirem.'''
    conn = get_db_connection()
    if not conn:
        logger.critical("Falha CRÍTICA ao criar tabelas: Sem conexão com DB.")
        return False

    try:
        cursor = conn.cursor()

        # Tabela de questões (schema V3.0)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disciplina TEXT NOT NULL,
                enunciado TEXT NOT NULL,
                alternativas TEXT NOT NULL, -- JSON TEXT {'A': '...', 'B': ...}
                resposta_correta TEXT NOT NULL, -- "A", "B", etc.
                dificuldade TEXT DEFAULT 'Médio',
                justificativa TEXT,
                dica TEXT,
                formula TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de redações (temas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                tema TEXT NOT NULL,
                texto_base TEXT,
                dicas TEXT,
                criterios_avaliacao TEXT, -- Pode ser JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de histórico de simulados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_simulados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulado_id TEXT UNIQUE NOT NULL, -- Garante ID único
                config TEXT, -- JSON da configuração
                relatorio TEXT, -- JSON do relatório final
                data_inicio TIMESTAMP,
                data_fim TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de histórico de redações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_redacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                redacao_id INTEGER, -- FK para a tabela redacoes
                texto_redacao TEXT,
                correcao TEXT, -- JSON da correção
                nota INTEGER,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (redacao_id) REFERENCES redacoes (id) ON DELETE SET NULL -- Opcional: o que fazer se o tema for deletado
            )
        ''')

        # Índices para otimizar consultas comuns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questoes_disciplina ON questoes(disciplina)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_simulados_data ON historico_simulados(data_fim)")

        conn.commit() # Salva as alterações (criação de tabelas/índices)
        # logger.info("Verificação/Criação de tabelas concluída.") # Log menos verboso
        return True

    except sqlite3.Error as db_err:
        logger.error(f"❌ Erro de SQLite ao criar/verificar tabelas: {db_err}", exc_info=True)
        conn.rollback() # Desfaz alterações em caso de erro
        return False
    except Exception as e:
        logger.error(f"❌ Erro geral ao criar/verificar tabelas: {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# ========== ROTAS DE NAVEGAÇÃO (PÁGINAS HTML) ==========

@app.route('/')
def index():
    '''Renderiza a página inicial (index.html).'''
    logger.debug("Acessando rota /")
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    '''Renderiza a página do simulado (simulado.html).'''
    logger.debug("Acessando rota /simulado")
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    '''Renderiza a página de redação (redacao.html).'''
    logger.debug("Acessando rota /redacao")
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    '''Renderiza a página do dashboard (dashboard.html).'''
    logger.debug("Acessando rota /dashboard")
    return render_template('dashboard.html')

# ========== API ENDPOINTS (RETORNAM JSON) ==========

@app.route('/api/health')
def health():
    '''Verifica a saúde da aplicação e a conexão com o banco.'''
    logger.debug("Acessando API /api/health")
    db_ok = False
    conn = get_db_connection()
    if conn:
        try:
            conn.execute("SELECT 1") # Testa a conexão executando um comando simples
            db_ok = True
        except Exception as e:
            logger.error(f"Erro ao testar conexão DB na health check: {e}")
        finally:
            conn.close()

    status_code = 200 if db_ok else 503 # Service Unavailable se DB falhar
    return jsonify({
        "status": "online",
        "message": "ConcursoMaster AI 3.0",
        "version": "3.3", # Atualizar versão
        "database_status": "connected" if db_ok else "error",
        "timestamp": datetime.now().isoformat()
    }), status_code

@app.route('/api/materias')
def materias():
    '''Retorna a lista de matérias disponíveis com a contagem de questões.'''
    logger.debug("Acessando API /api/materias")
    if not criar_tabelas_se_necessario():
         logger.error("Falha ao verificar/criar tabelas na API /api/materias.")
         return jsonify({"error": "Erro ao inicializar o banco de dados."}), 500

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erro de conexão com o banco de dados."}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT disciplina, COUNT(*) as total
            FROM questoes
            GROUP BY disciplina
            HAVING COUNT(*) > 0
            ORDER BY disciplina ASC
        """)
        rows = cursor.fetchall()

        materias_lista = []
        estatisticas_dict = {}
        total_geral = 0

        for row in rows:
            materia = row['disciplina']
            total = row['total']
            materias_lista.append(materia)
            estatisticas_dict[materia] = {'total': total}
            total_geral += total

        logger.info(f"API /api/materias retornou {len(materias_lista)} matérias com questões.")
        return jsonify({
            "materias": materias_lista,
            "estatisticas": estatisticas_dict,
            "total_geral": total_geral
        })

    except sqlite3.OperationalError as op_err:
        logger.error(f"Erro Operacional SQLite em /api/materias: {op_err}", exc_info=True)
        logger.info("Tentando recriar tabelas devido a erro operacional...")
        criar_tabelas_se_necessario()
        return jsonify({"error": "Erro operacional no banco. Tente novamente."}), 500
    except sqlite3.Error as db_err:
        logger.error(f"Erro SQLite em /api/materias: {db_err}", exc_info=True)
        return jsonify({"error": "Erro ao consultar matérias no banco."}), 500
    except Exception as e:
        logger.error(f"Erro geral em /api/materias: {e}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor."}), 500
    finally:
         if conn: conn.close()


# --- API do Sistema de Simulado ---

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado_api():
    '''
    Recebe a config, inicia o simulado e retorna dados iniciais.
    *** VERSÃO COM TRATAMENTO DE ERRO REFORÇADO ***
    '''
    logger.debug("Acessando API POST /api/simulado/iniciar")
    # ** Bloco try-except principal para capturar QUALQUER erro na rota **
    try:
        data = request.get_json()
        if not data:
            logger.warning("Tentativa de iniciar simulado sem dados JSON.")
            return jsonify({"success": False, "error": "Requisição inválida (sem JSON)"}), 400

        # Validação robusta dos dados de entrada
        materias_req = data.get('materias')
        quantidade_req = data.get('quantidade_total')
        tempo_req = data.get('tempo_minutos')
        aleatorio_req = data.get('aleatorio', True)

        # Validar Matérias
        if not materias_req or not isinstance(materias_req, list) or len(materias_req) == 0:
             logger.warning(f"Matérias inválidas: {materias_req}")
             return jsonify({"success": False, "error": "Seleção de matérias inválida."}), 400
        # Validar Quantidade
        try:
            quantidade_int = int(quantidade_req)
            if quantidade_int <= 0: raise ValueError("Quantidade <= 0")
        except (ValueError, TypeError, AttributeError):
             logger.warning(f"Quantidade inválida: {quantidade_req}")
             return jsonify({"success": False, "error": f"Quantidade inválida: '{quantidade_req}'."}), 400
        # Validar Tempo
        try:
            tempo_int = int(tempo_req)
            if tempo_int <= 0: raise ValueError("Tempo <= 0")
        except (ValueError, TypeError, AttributeError):
             logger.warning(f"Tempo inválido: {tempo_req}")
             return jsonify({"success": False, "error": f"Tempo inválido: '{tempo_req}'."}), 400

        config = {
            'materias': materias_req,
            'quantidade_total': quantidade_int,
            'tempo_minutos': tempo_int,
            'aleatorio': bool(aleatorio_req)
        }
        logger.info(f"Requisição para iniciar simulado com config: {config}")

        user_id = session.get('user_id', 'anon_' + str(random.randint(10000, 99999)))

        # Chama o método que pode retornar None ou lançar exceção
        simulado_id = sistema_simulado.iniciar_simulado(user_id, config)

        # Se iniciar_simulado retornou None (nenhuma questão ou erro interno no carregamento)
        if not simulado_id:
             # O log específico já ocorreu dentro de iniciar_simulado ou _carregar_questoes
             return jsonify({
                "success": False,
                "error": "Não foi possível iniciar o simulado. Verifique se há questões para os filtros selecionados ou se ocorreu um erro no servidor (consulte os logs)."
             }), 500 # Usar 500 aqui indica falha do servidor em preparar o simulado

        # Se chegou aqui, simulado_id é válido, busca os dados na memória
        simulado_ativo = sistema_simulado.simulados_ativos.get(simulado_id)
        if not simulado_ativo or not simulado_ativo.get('questoes'):
             logger.critical(f"INCONSISTÊNCIA GRAVE: Simulado {simulado_id} registrado, mas dados ausentes na memória.")
             # Tenta remover o registro inconsistente
             if simulado_id in sistema_simulado.simulados_ativos: del sistema_simulado.simulados_ativos[simulado_id]
             return jsonify({"success": False, "error": "Erro interno crítico após iniciar o simulado."}), 500

        # Prepara a resposta de sucesso
        primeira_questao = simulado_ativo['questoes'][0]
        total_questoes = len(simulado_ativo['questoes'])
        primeira_questao_frontend = primeira_questao.copy()
        primeira_questao_frontend.pop('resposta_correta', None)
        primeira_questao_frontend.pop('justificativa', None)

        logger.info(f"Simulado {simulado_id} iniciado. Enviando dados iniciais.")
        return jsonify({
            "success": True,
            "simulado_id": simulado_id,
            "total_questoes": total_questoes,
            "primeira_questao": primeira_questao_frontend,
            "tempo_limite_seg": config['tempo_minutos'] * 60
        })

    # ** Captura QUALQUER exceção não prevista que possa ocorrer na rota **
    except Exception as e_api:
        error_trace = traceback.format_exc() # Pega a pilha de erro completa
        logger.error(f"Erro 500 NÃO TRATADO na API /iniciar: {e_api}\n{error_trace}")
        # Retorna um JSON de erro genérico para o frontend
        return jsonify({"success": False, "error": "Erro interno inesperado no servidor. O administrador foi notificado."}), 500


@app.route('/api/simulado/<simulado_id>/questao/<int:questao_index>')
def get_questao_simulado(simulado_id, questao_index):
    '''
    Retorna os dados de uma questão específica de um simulado ativo,
    excluindo a resposta correta e a justificativa.
    '''
    logger.debug(f"Acessando API GET /api/simulado/{simulado_id}/questao/{questao_index}")
    simulado = sistema_simulado.simulados_ativos.get(simulado_id)
    if not simulado:
        logger.warning(f"Tentativa de acesso à questão de simulado inexistente ou finalizado: {simulado_id}")
        return jsonify({"error": "Simulado não encontrado ou já foi finalizado."}), 404

    # Validação do índice
    questoes_list = simulado.get('questoes', []) # Acesso seguro
    if not isinstance(questao_index, int) or questao_index < 0 or questao_index >= len(questoes_list):
        logger.warning(f"Índice de questão inválido ({questao_index}) solicitado para simulado {simulado_id}.")
        return jsonify({"error": "Número da questão inválido."}), 404

    questao = questoes_list[questao_index]

    # Cria uma cópia e remove campos sensíveis antes de enviar
    questao_para_frontend = questao.copy()
    questao_para_frontend.pop('resposta_correta', None)
    questao_para_frontend.pop('justificativa', None)

    return jsonify({
        "questao": questao_para_frontend,
        "numero_questao": questao_index + 1, # Número 1-based para exibição
        "total_questoes": len(questoes_list)
    })


@app.route('/api/simulado/<simulado_id>/responder', methods=['POST'])
def responder_questao_api(simulado_id):
    '''
    Registra a resposta do usuário para uma questão específica e retorna
    o feedback (se acertou, resposta correta, justificativa, etc.).
    '''
    logger.debug(f"Acessando API POST /api/simulado/{simulado_id}/responder")
    try:
        data = request.get_json()
        if not data:
             logger.warning(f"Requisição POST para responder sem dados JSON (simulado {simulado_id}).")
             return jsonify({"success": False, "error": "Dados da resposta não fornecidos."}), 400

        questao_index = data.get('questao_index')
        alternativa = data.get('alternativa')
        tempo_gasto = data.get('tempo_gasto', 0) # Tempo em segundos, default 0

        # Validação dos dados recebidos
        if questao_index is None or not isinstance(questao_index, int) or questao_index < 0:
             logger.warning(f"Índice de questão inválido recebido: {questao_index} (simulado {simulado_id}).")
             return jsonify({"success": False, "error": "Índice da questão inválido."}), 400
        if not alternativa or not isinstance(alternativa, str):
             logger.warning(f"Alternativa inválida recebida: {alternativa} (simulado {simulado_id}, questão {questao_index}).")
             return jsonify({"success": False, "error": "Alternativa inválida."}), 400
        try:
             tempo_gasto_float = float(tempo_gasto)
             if tempo_gasto_float < 0: tempo_gasto_float = 0.0
        except (ValueError, TypeError):
             logger.warning(f"Tempo gasto inválido: {tempo_gasto}. Usando 0. (simulado {simulado_id}, Q {questao_index})")
             tempo_gasto_float = 0.0

        simulado = sistema_simulado.simulados_ativos.get(simulado_id)
        if not simulado:
            logger.warning(f"Tentativa de responder simulado inexistente/finalizado: {simulado_id}")
            return jsonify({"success": False, "error": "Simulado não ativo."}), 404

        questoes_list = simulado.get('questoes', [])
        if questao_index >= len(questoes_list):
             logger.warning(f"Índice {questao_index} fora do limite para simulado {simulado_id}.")
             return jsonify({"success": False, "error": "Índice da questão fora do limite."}), 400

        # Pega a questão original completa do cache do servidor
        questao_original = questoes_list[questao_index]
        resposta_correta = str(questao_original.get('resposta_correta', '')).upper()
        acertou = alternativa.upper() == resposta_correta

        # Chama o método da classe para registrar a resposta
        success_registro = sistema_simulado.registrar_resposta(
            simulado_id, questao_index, alternativa, tempo_gasto_float
        )

        if not success_registro:
            return jsonify({"success": False, "error": "Falha ao registrar a resposta."}), 500

        # Retorna o feedback completo
        return jsonify({
            "success": True,
            "acertou": acertou,
            "resposta_correta": resposta_correta,
            "justificativa": questao_original.get('justificativa'),
            "dica": questao_original.get('dica'),
            "formula": questao_original.get('formula')
        })

    except Exception as e:
        logger.error(f"Erro EXCEPCIONAL API /responder (simulado {simulado_id}): {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno inesperado no servidor."}), 500


@app.route('/api/simulado/<simulado_id>/finalizar', methods=['POST'])
def finalizar_simulado_api(simulado_id):
    '''
    Endpoint para finalizar manualmente um simulado ativo e obter o relatório final.
    '''
    logger.debug(f"Acessando API POST /api/simulado/{simulado_id}/finalizar")
    try:
        relatorio = sistema_simulado.finalizar_simulado(simulado_id)
        if relatorio:
            logger.info(f"Simulado {simulado_id} finalizado via API.")
            return jsonify({"success": True, "relatorio": relatorio})
        else:
            logger.warning(f"Tentativa finalizar simulado {simulado_id} falhou (não ativo?).")
            return jsonify({"success": False, "error": "Simulado não encontrado ou já finalizado."}), 404
    except Exception as e:
        logger.error(f"Erro EXCEPCIONAL API /finalizar (simulado {simulado_id}): {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno ao finalizar simulado."}), 500

# --- API do Sistema de Redação ---
# ... (manter o código das rotas /api/redacoes/temas e /api/redacoes/corrigir da V3.1) ...
@app.route('/api/redacoes/temas')
def get_temas_redacao():
    '''Retorna a lista de temas de redação disponíveis.'''
    logger.debug("Acessando API GET /api/redacoes/temas")
    if not criar_tabelas_se_necessario():
         return jsonify({"temas": [], "error": "Erro ao verificar DB"}), 500
    conn = get_db_connection()
    if not conn: return jsonify({"temas": [], "error": "Erro de conexão com DB"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, titulo, tema, texto_base, dicas FROM redacoes ORDER BY id DESC") # Mais recentes primeiro
        temas = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Retornando {len(temas)} temas de redação.")
        return jsonify({"temas": temas})
    except sqlite3.Error as db_err:
        logger.error(f"Erro SQLite ao buscar temas: {db_err}", exc_info=True)
        return jsonify({"temas": [], "error": "Erro ao consultar temas no banco."}), 500
    except Exception as e:
        logger.error(f"Erro geral ao buscar temas: {e}", exc_info=True)
        return jsonify({"temas": [], "error": "Erro interno do servidor."}), 500
    finally:
         if conn: conn.close()


@app.route('/api/redacoes/corrigir', methods=['POST'])
def corrigir_redacao_api():
    '''Recebe texto da redação, simula correção e salva no histórico.'''
    logger.debug("Acessando API POST /api/redacoes/corrigir")
    try:
        data = request.get_json()
        if not data: return jsonify({"success": False, "error": "Dados não fornecidos"}), 400
        redacao_id = data.get('redacao_id')
        texto_redacao = data.get('texto_redacao')
        if not redacao_id or not texto_redacao:
             logger.warning("Tentativa de corrigir redação sem ID ou texto.")
             return jsonify({"success": False, "error": "ID do tema e texto da redação são obrigatórios."}), 400

        # --- SIMULAÇÃO DE CORREÇÃO ---
        nota_base = min(len(texto_redacao) / 10.0, 600.0) # Usar float para divisão
        nota_final = min(int(nota_base + random.uniform(200, 400)), 1000) # Usar uniform para float
        correcao = {
            'nota': nota_final,
            'competencia_1': {'nota': random.randint(120, 200), 'comentario': 'Avaliação simulada da norma culta.'},
            'competencia_2': {'nota': random.randint(120, 200), 'comentario': 'Avaliação simulada da compreensão do tema e repertório.'},
            'competencia_3': {'nota': random.randint(100, 200), 'comentario': 'Avaliação simulada da argumentação.'},
            'competencia_4': {'nota': random.randint(120, 200), 'comentario': 'Avaliação simulada da coesão textual.'},
            'competencia_5': {'nota': random.randint(100, 200), 'comentario': 'Avaliação simulada da proposta de intervenção.'},
            'feedback_geral': f'Correção simulada. Sua nota foi {nota_final}. O texto demonstra [ponto positivo simulado]. Sugestão: [ponto de melhoria simulado].',
            'sugestoes_melhoria': ['Ampliar repertório sociocultural.', 'Detalhar melhor a proposta de intervenção.', 'Revisar concordância verbal/nominal.']
        }
        logger.info(f"Redação ID {redacao_id} corrigida (simulada). Nota: {nota_final}")

        # Salvar histórico
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO historico_redacoes (redacao_id, texto_redacao, correcao, nota, feedback) VALUES (?, ?, ?, ?, ?)',
                               (redacao_id, texto_redacao, json.dumps(correcao), correcao['nota'], correcao['feedback_geral']))
                conn.commit()
                logger.info(f"Histórico da redação ID {redacao_id} salvo.")
            except sqlite3.Error as db_err:
                 logger.error(f"Erro SQLite ao salvar histórico de redação: {db_err}", exc_info=True)
                 conn.rollback()
            except Exception as e_save:
                 logger.error(f"Erro geral ao salvar histórico de redação: {e_save}", exc_info=True)
                 conn.rollback()
            finally:
                conn.close()
        else:
            logger.error("Não foi possível salvar histórico da redação - falha na conexão DB.")


        return jsonify({"success": True, "correcao": correcao})
    except Exception as e:
        logger.error(f"Erro EXCEPCIONAL na API /corrigir: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno inesperado no servidor."}), 500

# --- API do Dashboard Avançado ---
@app.route('/api/dashboard/estatisticas')
def get_estatisticas_dashboard():
    '''Retorna estatísticas agregadas para preencher o dashboard.'''
    logger.debug("Acessando API GET /api/dashboard/estatisticas")
    if not criar_tabelas_se_necessario():
        return jsonify({"estatisticas": {}, "error": "Erro ao verificar DB"}), 500
    conn = get_db_connection()
    if not conn: return jsonify({"estatisticas": {}, "error": "Erro de conexão com DB"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM questoes")
        res = cursor.fetchone()
        total_questoes_banco = res['total'] if res else 0

        # Usar índice para buscar histórico
        cursor.execute("SELECT id, relatorio, data_fim FROM historico_simulados ORDER BY data_fim ASC") # Adiciona ID para logs
        todos_relatorios = cursor.fetchall()

        historico_evolucao, global_stats_materia, tempo_total_estudo, total_questoes_respondidas = [], {}, 0.0, 0
        for row in todos_relatorios:
            row_id = row['id'] if 'id' in row.keys() else 'N/A' # Acesso seguro ao ID
            try:
                # Tratamento mais seguro de dados
                relatorio = json.loads(row['relatorio']) if row['relatorio'] else {}
                data_fim_str = row['data_fim']
                if not data_fim_str: continue

                data_fim_dt = datetime.fromisoformat(data_fim_str)
                geral = relatorio.get('geral', {})

                historico_evolucao.append({'data': data_fim_dt.strftime('%d/%m'),
                                           'percentual': float(geral.get('percentual_acerto', 0.0))})

                tempo_total_estudo += float(geral.get('tempo_total_minutos', 0.0))
                total_questoes_respondidas += int(geral.get('questoes_respondidas', 0))

                for materia, stats in relatorio.get('por_materia', {}).items():
                    if materia not in global_stats_materia: global_stats_materia[materia] = {'acertos': 0, 'total': 0}
                    global_stats_materia[materia]['acertos'] += int(stats.get('acertos', 0))
                    global_stats_materia[materia]['total'] += int(stats.get('total', 0))

            except json.JSONDecodeError as json_err:
                 logger.error(f"Erro JSONDecode relatório histórico ID {row_id}: {json_err}")
            except Exception as e_proc:
                 logger.error(f"Erro processar relatório histórico ID {row_id}: {e_proc}", exc_info=True)


        desempenho_global_materia = {
            m: round((s['acertos'] * 100.0 / s['total']), 1) if s['total'] > 0 else 0.0
            for m, s in global_stats_materia.items()
        }

        historico_recente_formatado = []
        for row in reversed(todos_relatorios[-10:]): # Pega os 10 últimos
            try:
                relatorio = json.loads(row['relatorio']) if row['relatorio'] else {}
                data_fim_str = row['data_fim']
                if data_fim_str:
                     historico_recente_formatado.append({
                        'data': datetime.fromisoformat(data_fim_str).strftime('%d/%m/%Y %H:%M'),
                        'geral': relatorio.get('geral', {})})
            except Exception as e_hist:
                 logger.error(f"Erro ao formatar histórico recente: {e_hist}")

        media_geral = round(sum(h['percentual'] for h in historico_evolucao) / len(historico_evolucao), 1) if historico_evolucao else 0.0

        logger.info("Estatísticas do dashboard calculadas.")
        return jsonify({"estatisticas": {
            "total_questoes_banco": total_questoes_banco,
            "total_simulados_realizados": len(todos_relatorios),
            "total_questoes_respondidas": total_questoes_respondidas,
            "tempo_total_estudo_min": round(tempo_total_estudo, 1),
            "media_geral_percentual": media_geral,
            "evolucao_desempenho": historico_evolucao,
            "desempenho_global_materia": desempenho_global_materia,
            "historico_recente": historico_recente_formatado
        }})
    except sqlite3.Error as db_err:
        logger.error(f"Erro SQLite API estatísticas: {db_err}", exc_info=True)
        return jsonify({"estatisticas": {}, "error": "Erro DB estatísticas."}), 500
    except Exception as e:
        logger.error(f"Erro geral API estatísticas: {e}", exc_info=True)
        return jsonify({"estatisticas": {}, "error": "Erro interno servidor."}), 500
    finally:
        if conn: conn.close()


# --- Rotas Estáticas ---
@app.route('/static/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('static', filename)

# --- Tratamento de Erros ---
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"Rota 404: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint não encontrado"}), 404
    try:
        return render_template('error.html', mensagem="Página não encontrada (404)."), 404
    except:
        return "<h1>Erro 404</h1>", 404

@app.errorhandler(500)
def internal_error(error):
    error_trace = traceback.format_exc()
    logger.error(f"Erro 500 na rota {request.url}:\n{error_trace}")
    if request.path.startswith('/api/'):
         # Em APIs, retornar o traceback em DEV pode ser útil, mas NUNCA em PROD
         # return jsonify({"error": "Erro interno servidor", "trace": error_trace}), 500 # DEV ONLY
         return jsonify({"error": "Erro interno servidor."}), 500 # PROD
    try:
        return render_template('error.html', mensagem="Erro interno do servidor (500)."), 500
    except:
        return "<h1>Erro 500</h1>", 500


# --- Inicialização da Aplicação ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))

    if not criar_tabelas_se_necessario():
         logger.critical("########## FALHA AO INICIALIZAR DB - APP PODE FALHAR ##########")

    logger.info(f"========= INICIANDO ConcursoMaster AI 3.0 NA PORTA {port} =========")

    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    use_debug = not is_production and os.environ.get('FLASK_DEBUG') == '1'

    if use_debug:
        logger.warning("############## Rodando em modo DEBUG ##############")
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        logger.info("Rodando em modo PRODUÇÃO (debug=False)")
        # Em produção real, é melhor usar um servidor WSGI como Waitress ou Gunicorn
        # from waitress import serve
        # serve(app, host='0.0.0.0', port=port)
        app.run(host='0.0.0.0', port=port, debug=False) # Fallback para o servidor Flask (não ideal para prod)

