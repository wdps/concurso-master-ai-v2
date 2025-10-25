from flask import Flask, jsonify, send_from_directory, request, render_template, session
import os
import sqlite3
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# Configurações
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Chave secreta para gerenciamento de sessão (necessário para futuros sistemas de usuário)
app.secret_key = 'concurso_master_secret_key_2024_super_segura'

class SistemaSimulado:
    """Gerencia a lógica de simulados ativos."""
    def __init__(self):
        self.simulados_ativos = {}
    
    def iniciar_simulado(self, user_id, config):
        """Inicia um novo simulado e armazena em memória."""
        simulado_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        simulado_data = {
            'id': simulado_id,
            'config': config,
            'questoes': [],
            'respostas': {}, # Usar um dicionário para respostas por índice
            'inicio': datetime.now(),
            'tempo_limite_min': config.get('tempo_minutos', 180),
            'status': 'ativo',
            'questao_atual': 0
        }
        
        # Carregar questões
        questoes = self._carregar_questoes_simulado(config)
        simulado_data['questoes'] = questoes
        
        self.simulados_ativos[simulado_id] = simulado_data
        logger.info(f"Simulado {simulado_id} iniciado com {len(questoes)} questões.")
        return simulado_id
    
    def _carregar_questoes_simulado(self, config):
        """Carrega questões do banco baseado na configuração. (CORRIGIDO)"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            materias = config.get('materias', [])
            quantidade = config.get('quantidade_total', 50)
            aleatorio = config.get('aleatorio', True)
            
            query = "SELECT * FROM questoes WHERE 1=1"
            params = []
            
            if materias:
                placeholders = ','.join(['?'] * len(materias))
                query += f" AND disciplina IN ({placeholders})"
                params.extend(materias)
            
            if aleatorio:
                query += " ORDER BY RANDOM()"
            else:
                query += " ORDER BY id" # Ou outra coluna de ordenação
            
            query += " LIMIT ?"
            params.append(quantidade)
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            questoes = []
            
            # CORREÇÃO: Acessar colunas de forma segura sem '.get()'
            # Vamos checar as colunas disponíveis primeiro
            if resultados:
                colunas_disponiveis = resultados[0].keys()
                
                for row in resultados:
                    # Desserializa o JSON das alternativas
                    alternativas_json = json.loads(row['alternativas'])
                    
                    questao = {
                        'id': row['id'],
                        'enunciado': row['enunciado'],
                        'materia': row['disciplina'],
                        'alternativas': alternativas_json, # Usa o JSON desserializado
                        'resposta_correta': row['resposta_correta'],
                        # --- AQUI ESTÁ A MUDANÇA ---
                        'dificuldade': row['dificuldade'] if 'dificuldade' in colunas_disponiveis else 'Médio',
                        'justificativa': row['justificativa'] if 'justificativa' in colunas_disponiveis else None,
                        'dica': row['dica'] if 'dica' in colunas_disponiveis else None,
                        'formula': row['formula'] if 'formula' in colunas_disponiveis else None
                        # --- FIM DA MUDANÇA ---
                    }
                    questoes.append(questao)
            
            return questoes
            
        except Exception as e:
            # Adicionamos um log mais detalhado
            logger.error(f"Erro detalhado ao carregar questões: {e}", exc_info=True)
            return []
        finally:
            conn.close()
    
    def registrar_resposta(self, simulado_id, questao_index, alternativa, tempo_gasto_na_questao):
        """Registra uma resposta do usuário para uma questão específica."""
        if simulado_id not in self.simulados_ativos:
            logger.warning(f"Tentativa de resposta para simulado {simulado_id} inexistente.")
            return False
        
        simulado = self.simulados_ativos[simulado_id]
        
        if questao_index >= len(simulado['questoes']):
            logger.warning(f"Índice de questão {questao_index} fora do limite.")
            return False
        
        questao = simulado['questoes'][questao_index]
        acertou = alternativa.upper() == questao['resposta_correta'].upper()
        
        resposta = {
            'questao_id': questao['id'],
            'alternativa_escolhida': alternativa,
            'acertou': acertou,
            'tempo_gasto': tempo_gasto_na_questao,
            'timestamp': datetime.now()
        }
        
        # Armazena a resposta usando o índice da questão como chave
        simulado['respostas'][questao_index] = resposta
        logger.info(f"Resposta registrada para simulado {simulado_id}, questão {questao_index}.")
        return True
    
    def finalizar_simulado(self, simulado_id):
        """Finaliza simulado, gera relatório e salva no histórico."""
        if simulado_id not in self.simulados_ativos:
            return None
        
        simulado = self.simulados_ativos[simulado_id]
        simulado['fim'] = datetime.now()
        simulado['status'] = 'finalizado'
        
        relatorio = self._gerar_relatorio(simulado)
        simulado['relatorio'] = relatorio
        
        # Salvar no histórico do banco de dados
        self._salvar_historico(simulado)
        
        # Remover da memória ativa
        if simulado_id in self.simulados_ativos:
             del self.simulados_ativos[simulado_id]
        
        logger.info(f"Simulado {simulado_id} finalizado e salvo no histórico.")
        return relatorio
    
    def _gerar_relatorio(self, simulado):
        """Gera relatório detalhado do simulado."""
        respostas = simulado['respostas'] # Agora é um dict {index: resposta}
        total_questoes_planejadas = len(simulado['questoes'])
        questoes_respondidas_obj = respostas.values()
        questoes_respondidas_count = len(questoes_respondidas_obj)
        
        # Estatísticas gerais
        acertos = sum(1 for r in questoes_respondidas_obj if r['acertou'])
        percentual_acerto = (acertos / questoes_respondidas_count * 100) if questoes_respondidas_count > 0 else 0
        
        # Tempo total
        tempo_total_gasto_seg = sum(r['tempo_gasto'] for r in questoes_respondidas_obj)
        
        # Estatísticas por matéria
        estatisticas_materia = {}
        for questao_index, resposta in respostas.items():
            # Garantir que o índice da questão ainda é válido
            if questao_index < len(simulado['questoes']):
                questao = simulado['questoes'][questao_index]
                materia = questao['materia']
                
                if materia not in estatisticas_materia:
                    estatisticas_materia[materia] = {'total': 0, 'acertos': 0, 'tempo': 0}
                
                estatisticas_materia[materia]['total'] += 1
                estatisticas_materia[materia]['tempo'] += resposta['tempo_gasto']
                if resposta['acertou']:
                    estatisticas_materia[materia]['acertos'] += 1
        
        # Calcular percentuais por matéria
        for materia, stats in estatisticas_materia.items():
            stats['percentual'] = (stats['acertos'] / stats['total'] * 100) if stats['total'] > 0 else 0
            stats['tempo_medio'] = stats['tempo'] / stats['total'] if stats['total'] > 0 else 0
        
        # Recomendações
        recomendacoes = self._gerar_recomendacoes(estatisticas_materia)
        
        return {
            'geral': {
                'total_questoes_planejadas': total_questoes_planejadas,
                'questoes_respondidas': questoes_respondidas_count,
                'acertos': acertos,
                'erros': questoes_respondidas_count - acertos,
                'percentual_acerto': round(percentual_acerto, 2),
                'tempo_total_minutos': round(tempo_total_gasto_seg / 60, 2),
                'tempo_medio_questao': round(tempo_total_gasto_seg / questoes_respondidas_count, 2) if questoes_respondidas_count > 0 else 0
            },
            'por_materia': estatisticas_materia,
            'recomendacoes': recomendacoes,
            'questoes_com_detalhes': self._preparar_questoes_detalhadas(simulado)
        }
    
    def _gerar_recomendacoes(self, estatisticas_materia):
        """Gera recomendações personalizadas com base no desempenho."""
        recomendacoes = []
        
        # Ordenar por pior desempenho
        materias_ordenadas = sorted(estatisticas_materia.items(), key=lambda item: item[1]['percentual'])
        
        for materia, stats in materias_ordenadas:
            if stats['percentual'] < 50:
                recomendacoes.append(f"🚨 Foco urgente em {materia} - Apenas {stats['percentual']:.1f}% de acerto.")
            elif stats['percentual'] < 70:
                recomendacoes.append(f"📚 Revisar {materia} - {stats['percentual']:.1f}% de acerto.")
            elif stats['percentual'] < 90:
                recomendacoes.append(f"✅ Bom desempenho em {materia} - {stats['percentual']:.1f}%. Continue mantendo.")
            else:
                recomendacoes.append(f"🎉 Excelente em {materia} - {stats['percentual']:.1f}%! Ótimo trabalho.")
        
        if not recomendacoes:
            recomendacoes.append("📈 Continue com estudos equilibrados em todas as matérias.")
        
        return recomendacoes
    
    def _preparar_questoes_detalhadas(self, simulado):
        """Prepara lista de questões com respostas para revisão do usuário."""
        detalhes = []
        
        for i, questao in enumerate(simulado['questoes']):
            resposta_usuario_obj = simulado['respostas'].get(i) # Busca a resposta pelo índice
            
            detalhe_questao = {
                'numero': i + 1,
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'alternativas': questao['alternativas'],
                'resposta_correta': questao['resposta_correta'],
                'justificativa': questao.get('justificativa'),
                'dica': questao.get('dica'),
                'formula': questao.get('formula'),
                'resposta_usuario': resposta_usuario_obj['alternativa_escolhida'] if resposta_usuario_obj else None,
                'acertou': resposta_usuario_obj['acertou'] if resposta_usuario_obj else None,
                'tempo_gasto': resposta_usuario_obj['tempo_gasto'] if resposta_usuario_obj else None
            }
            
            detalhes.append(detalhe_questao)
        
        return detalhes
    
    def _salvar_historico(self, simulado):
        """Salva o relatório final do simulado no banco de dados."""
        conn = get_db_connection()
        if not conn:
            logger.error("Falha ao salvar histórico: Sem conexão com DB.")
            return
        
        try:
            cursor = conn.cursor()
            
            # Tabela de histórico (criada em criar_tabelas_se_necessario)
            cursor.execute('''
                INSERT INTO historico_simulados 
                (simulado_id, config, relatorio, data_inicio, data_fim)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                simulado['id'],
                json.dumps(simulado['config']),
                json.dumps(simulado['relatorio']),
                simulado['inicio'].isoformat(),
                simulado['fim'].isoformat()
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Erro ao salvar histórico no DB: {e}")
            conn.rollback() # Desfaz a transação em caso de erro
        finally:
            conn.close()

# --- Instância Global ---
sistema_simulado = SistemaSimulado()

# --- Conexão e Criação do Banco ---

def get_db_connection():
    """Conexão segura com o banco SQLite."""
    try:
        conn = sqlite3.connect('concurso.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"❌ Erro na conexão com o DB: {e}")
        return None

def criar_tabelas_se_necessario():
    """Verifica e cria todas as tabelas necessárias na inicialização."""
    conn = get_db_connection()
    if not conn:
        logger.error("Falha ao criar tabelas: Sem conexão com DB.")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabela de questões (padronizada)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disciplina TEXT NOT NULL,
                enunciado TEXT NOT NULL,
                alternativas TEXT NOT NULL, -- ARMAZENAR COMO JSON TEXT
                resposta_correta TEXT NOT NULL, -- Ex: "A", "B"
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
                criterios_avaliacao TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de histórico de simulados (relatórios)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_simulados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulado_id TEXT UNIQUE,
                config TEXT,
                relatorio TEXT,
                data_inicio TIMESTAMP,
                data_fim TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de histórico de redações (submissões)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_redacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                redacao_id INTEGER,
                texto_redacao TEXT,
                correcao TEXT,
                nota INTEGER,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (redacao_id) REFERENCES redacoes (id)
            )
        ''')
        
        conn.commit()
        logger.info("Verificação de tabelas concluída. Banco pronto.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar/verificar tabelas: {e}")
        return False
    finally:
        conn.close()

# ========== ROTAS DE NAVEGAÇÃO (HTML) ==========

@app.route('/')
def home():
    """Página inicial / Hub principal."""
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    """Página do sistema de simulado."""
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    """Página do sistema de redação."""
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    """Página do dashboard avançado."""
    return render_template('dashboard.html')

# ========== API ENDPOINTS (JSON) ==========

@app.route('/api/health')
def health():
    """Verificação de saúde da API."""
    return jsonify({
        "status": "online", 
        "message": "ConcursoMaster AI 3.0",
        "version": "3.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/materias')
def materias():
    """API de matérias para preencher o formulário do simulado."""
    criar_tabelas_se_necessario()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"materias": [], "estatisticas": {}, "total_geral": 0})
    
    try:
        cursor = conn.cursor()
        
        # Agrupa por disciplina e conta o total de questões em cada
        cursor.execute("SELECT disciplina, COUNT(*) as total FROM questoes GROUP BY disciplina ORDER BY disciplina")
        rows = cursor.fetchall()
        
        materias_lista = []
        estatisticas_dict = {}
        total_geral = 0
        
        for row in rows:
            materia = row['disciplina']
            total = row['total']
            
            materias_lista.append(materia)
            estatisticas_dict[materia] = {
                'total': total,
                'faceis': 0,  # Simplificado, poderia ser calculado
                'medias': total,
                'dificeis': 0
            }
            total_geral += total
        
        conn.close()
        
        return jsonify({
            "materias": materias_lista,
            "estatisticas": estatisticas_dict,
            "total_geral": total_geral
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/materias: {e}")
        return jsonify({"materias": [], "estatisticas": {}, "total_geral": 0})

# --- API do Sistema de Simulado ---

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado_api():
    """Endpoint para iniciar um novo simulado."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Requisição sem dados"}), 400
        
        config = {
            'materias': data.get('materias', []),
            'quantidade_total': data.get('quantidade_total', 50),
            'tempo_minutos': data.get('tempo_minutos', 180),
            'aleatorio': data.get('aleatorio', True)
        }
        
        # Gerar um ID de usuário temporário (idealmente viria da sessão)
        user_id = session.get('user_id', 'anon_' + datetime.now().strftime('%f'))
        
        simulado_id = sistema_simulado.iniciar_simulado(user_id, config)
        
        # --- CORREÇÃO DE CRASH ---
        # Verificar se o simulado foi criado com questões
        simulado_ativo = sistema_simulado.simulados_ativos.get(simulado_id)
        if not simulado_ativo:
            logger.error(f"Falha ao recuperar simulado {simulado_id} da memória após criação.")
            return jsonify({"success": False, "error": "Erro interno ao criar simulado"}), 500

        questoes_carregadas = simulado_ativo['questoes']
        total_questoes = len(questoes_carregadas)

        # Se NENHUMA questão foi encontrada (DB vazio ou filtro ruim), retorna erro
        if total_questoes == 0:
            logger.warning(f"Simulado {simulado_id} iniciado, mas 0 questões encontradas para filtros.")
            # Remover o simulado vazio da memória
            if simulado_id in sistema_simulado.simulados_ativos:
                del sistema_simulado.simulados_ativos[simulado_id]
            return jsonify({
                "success": False, 
                "error": "Nenhuma questão foi encontrada para as matérias selecionadas. O banco de dados pode estar vazio."
            }), 404
        
        # Se deu tudo certo, pega a primeira questão
        primeira_questao = questoes_carregadas[0]
        # --- FIM DA CORREÇÃO ---

        return jsonify({
            "success": True,
            "simulado_id": simulado_id,
            "total_questoes": total_questoes,
            "primeira_questao": primeira_questao,
            "tempo_limite_seg": config['tempo_minutos'] * 60
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar simulado: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/simulado/<simulado_id>/questao/<int:questao_index>')
def get_questao_simulado(simulado_id, questao_index):
    """Obtém uma questão específica do simulado."""
    if simulado_id not in sistema_simulado.simulados_ativos:
        return jsonify({"error": "Simulado não encontrado ou finalizado"}), 404
    
    simulado = sistema_simulado.simulados_ativos[simulado_id]
    
    if questao_index >= len(simulado['questoes']):
        return jsonify({"error": "Questão não encontrada (índice fora do limite)"}), 404
    
    questao = simulado['questoes'][questao_index]
    
    return jsonify({
        "questao": questao,
        "numero_questao": questao_index + 1,
        "total_questoes": len(simulado['questoes'])
    })

@app.route('/api/simulado/<simulado_id>/responder', methods=['POST'])
def responder_questao_api(simulado_id):
    """Registra a resposta de uma questão."""
    try:
        data = request.get_json()
        
        questao_index = data.get('questao_index')
        alternativa = data.get('alternativa')
        tempo_gasto = data.get('tempo_gasto', 0)
        
        success = sistema_simulado.registrar_resposta(
            simulado_id, questao_index, alternativa, tempo_gasto
        )
        
        if not success:
            return jsonify({"success": False, "error": "Falha ao registrar resposta"}), 400
            
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Erro ao registrar resposta: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/simulado/<simulado_id>/finalizar', methods=['POST'])
def finalizar_simulado_api(simulado_id):
    """Endpoint para finalizar o simulado e obter o relatório."""
    try:
        relatorio = sistema_simulado.finalizar_simulado(simulado_id)
        
        if relatorio:
            return jsonify({
                "success": True,
                "relatorio": relatorio
            })
        else:
            return jsonify({"success": False, "error": "Simulado não encontrado ou já finalizado"}), 404
            
    except Exception as e:
        logger.error(f"Erro ao finalizar simulado: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- API do Sistema de Redação ---

@app.route('/api/redacoes/temas')
def get_temas_redacao():
    """Obtém temas de redação disponíveis no banco."""
    criar_tabelas_se_necessario()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"temas": []})
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, titulo, tema, texto_base, dicas FROM redacoes")
        temas = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({"temas": temas})
        
    except Exception as e:
        logger.error(f"Erro ao obter temas de redação: {e}")
        return jsonify({"temas": []})

@app.route('/api/redacoes/corrigir', methods=['POST'])
def corrigir_redacao_api():
    """Recebe uma redação e retorna uma correção simulada."""
    try:
        data = request.get_json()
        
        redacao_id = data.get('redacao_id')
        texto_redacao = data.get('texto_redacao')
        
        # --- SIMULAÇÃO DE CORREÇÃO (IA) ---
        nota_base = min(len(texto_redacao) / 10, 600) # Nota base pelo tamanho
        nota_final = min(int(nota_base + random.randint(200, 400)), 1000) # Nota final
        
        correcao = {
            'nota': nota_final,
            'competencia_1': {'nota': random.randint(120, 200), 'comentario': 'Bom domínio da norma culta, poucos desvios gramaticais.'},
            'competencia_2': {'nota': random.randint(120, 200), 'comentario': 'Tema bem compreendido, com uso de repertório pertinente.'},
            'competencia_3': {'nota': random.randint(100, 200), 'comentario': 'Argumentação consistente, mas pode aprofundar a relação entre os fatos.'},
            'competencia_4': {'nota': random.randint(120, 200), 'comentario': 'Boa organização textual e uso de conectivos.'},
            'competencia_5': {'nota': random.randint(100, 200), 'comentario': 'Proposta de intervenção presente, mas poderia ser mais detalhada.'},
            'feedback_geral': f'Ótimo esforço! Sua nota foi {nota_final}. A redação está bem estruturada. Continue praticando a profundidade dos argumentos e o detalhamento da proposta de intervenção para alcançar a nota máxima.',
            'sugestoes_melhoria': [
                'Tente usar um repertório sociocultural mais diversificado.',
                'Detalhe melhor os "agentes" e "meios" na sua proposta de intervenção.',
                'Revise o uso de vírgulas em orações subordinadas.'
            ]
        }
        
        # Salvar submissão e correção no histórico
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_redacoes 
                (redacao_id, texto_redacao, correcao, nota, feedback)
                VALUES (?, ?, ?, ?, ?)
            ''', (redacao_id, texto_redacao, json.dumps(correcao), correcao['nota'], correcao['feedback_geral']))
            conn.commit()
            conn.close()
        
        return jsonify({
            "success": True,
            "correcao": correcao
        })
        
    except Exception as e:
        logger.error(f"Erro ao corrigir redação: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- API do Dashboard Avançado ---

@app.route('/api/dashboard/estatisticas')
def get_estatisticas_dashboard():
    """Estatísticas avançadas para o dashboard profissional."""
    criar_tabelas_se_necessario()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"estatisticas": {}})
    
    try:
        cursor = conn.cursor()
        
        # 1. Total de questões no banco
        cursor.execute("SELECT COUNT(*) as total FROM questoes")
        total_questoes_banco = cursor.fetchone()['total']
        
        # 2. Histórico de simulados (para gráficos e tabela)
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
                historico_evolucao.append({
                    'data': datetime.fromisoformat(data_fim_str).strftime('%d/%m'),
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
            
        # 4. Histórico recente (para a tabela, 10 últimos)
        historico_recente_formatado = []
        # Pegar os 10 últimos e inverter (mais novo primeiro)
        for row in reversed(todos_relatorios[-10:]): 
            try:
                relatorio = json.loads(row['relatorio'])
                data_fim_str = row['data_fim']
                historico_recente_formatado.append({
                    'data': datetime.fromisoformat(data_fim_str).strftime('%d/%m/%Y %H:%M'),
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
                "evolucao_desempenho": historico_evolucao, # Para gráfico de linha
                "desempenho_global_materia": desempenho_global_materia, # Para gráfico de rosca
                "historico_recente": historico_recente_formatado # Para tabela
            }
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/dashboard/estatisticas: {e}")
        conn.close()
        return jsonify({"estatisticas": {}})

# --- Rota Estática ---

@app.route('/<path:path>')
def serve_static(path):
    """Serve arquivos estáticos como index.html (se não for pego por '/')"""
    # Tenta servir da pasta 'static' primeiro
    if os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    # Se não, tenta servir da raiz (para index.html, etc.)
    if os.path.exists(os.path.join('.', path)):
        return send_from_directory('.', path)
    
    # Fallback para o index.html principal
    return send_from_directory('.', 'index.html')


# --- Inicialização ---

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    # Garante que as tabelas existam antes de rodar
    criar_tabelas_se_necessario()
    logger.info(f"🚀 ConcursoMaster AI 3.0 iniciando na porta {port}")
    # debug=False é crucial para produção (Gunicorn/Railway vai gerenciar)
    app.run(host='0.0.0.0', port=port, debug=False)
