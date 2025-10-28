"""
ESQUEMATIZA.AI - SISTEMA DE SIMULADOS PARA CONCURSOS
Versão Robusta - Configuração Avançada e Tratamento de Erros Aprimorado
"""

from whitenoise import WhiteNoise
from flask import Flask, render_template, jsonify, request, session, send_from_directory
import sqlite3
import json
import random
import time
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import traceback
import logging
from logging.handlers import RotatingFileHandler
import sys

# --- Configuração de Logging Robusta ---
def setup_logging():
    """Configura sistema de logging robusto com rotação de arquivos"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger = logging.getLogger('esquematiza')
    logger.setLevel(logging.INFO)
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        f'{log_dir}/app.log', 
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Inicializar logging
logger = setup_logging()

# --- Configuração Inicial ---
load_dotenv()

# Definir o caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'concursos.db')
logger.info(f'--- CAMINHO DO BANCO DE DADOS DEFINIDO: {DB_PATH} ---')

app = Flask(__name__)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'chave_secreta_forte_esquematiza_2024')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['JSON_SORT_KEYS'] = False  # Manter ordem dos JSONs

# --- Configuração da API Gemini com Fallback ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "models/gemini-2.0-flash"

def configure_gemini():
    """Configura Gemini com fallback robusto"""
    if not GEMINI_API_KEY:
        logger.warning("❌ GEMINI_API_KEY não encontrada - Correção de redação desativada")
        return False
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Teste de conexão
        model = genai.GenerativeModel(MODEL_NAME)
        model.generate_content("Teste de conexão")
        logger.info(f"✅ Gemini configurado: {MODEL_NAME}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro na configuração do Gemini: {e}")
        return False

gemini_configured = configure_gemini()

# --- Dicionário de Áreas (Expansível) ---
AREAS_CONHECIMENTO = {
    "Atualidades": "Atualidades",
    "Mercado Financeiro": "Conhecimentos Bancários", 
    "Conhecimentos Bancários": "Conhecimentos Bancários",
    "Direito Administrativo": "Direito (Admin. e Const.)",
    "Direito Constitucional": "Direito (Admin. e Const.)",
    "Informática": "Informática",
    "Língua Portuguesa": "Língua Portuguesa",
    "Literatura": "Língua Portuguesa",
    "Matemática": "Matemática e Raciocínio Lógico",
    "Raciocínio Lógico": "Matemática e Raciocínio Lógico",
    "Psicologia": "Psicologia e Negociação",
    "Vendas": "Psicologia e Negociação", 
    "Negociação": "Psicologia e Negociação",
    "Geografia": "Atualidades",
    "História": "Atualidades",
    "Economia": "Atualidades",
    "Administração": "Conhecimentos Bancários",
    "Contabilidade": "Conhecimentos Bancários"
}

# --- Cache para melhor performance ---
class SimpleCache:
    def __init__(self, ttl=300):  # 5 minutos default
        self._cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def set(self, key, value):
        self._cache[key] = (value, time.time())

# Cache para matérias e temas
materias_cache = SimpleCache(ttl=600)  # 10 minutos
temas_cache = SimpleCache(ttl=600)

def get_area(materia):
    """Retorna a Área de Conhecimento para dada Matéria com fallback."""
    if not materia:
        return "Outras Matérias"
    
    materia_lower = materia.lower()
    for mat, area in AREAS_CONHECIMENTO.items():
        if mat.lower() in materia_lower:
            return area
    return "Outras Matérias"

def corrigir_encoding(texto):
    """Corrige problemas comuns de encoding de forma robusta."""
    if texto is None:
        return ""
    
    if not isinstance(texto, str):
        try:
            texto = str(texto)
        except:
            return "[Texto não decodificável]"
    
    correcoes = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã£': 'ã', 'Ãµ': 'õ', 'Ã¢': 'â', 'Ãª': 'ê', 'Ã§': 'ç',
        'Âº': 'º', 'Ã‰': 'É', 'ÃŠ': 'Ê', 'Ã‘': 'Ñ',
        'â‚¬': '€', 'â€š': '‚', 'â€ž': '„', 'â€¦': '…'
    }
    
    for erro, correcao in correcoes.items():
        texto = texto.replace(erro, correcao)
        
    return texto

def get_db_connection(max_retries=3):
    """Conexão com banco de dados com retry e timeout."""
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect('concurso.db', check_same_thread=False, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout = 5000")
            return conn
        except sqlite3.Error as e:
            logger.warning(f"Tentativa {attempt + 1}/{max_retries} - Erro DB: {e}")
            if attempt == max_retries - 1:
                logger.error(f"Falha após {max_retries} tentativas: {e}")
                raise
            time.sleep(1)

def safe_json_loads(text, default=None):
    """Carrega JSON de forma segura com fallback."""
    if default is None:
        default = {}
    
    if not text:
        return default
    
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"JSON inválido: {text[:100]}...")
        return default

# --- Rotas Principais com Error Handling ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    session.pop('simulado_atual', None)
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/health')
def health_check():
    """Endpoint de health check para monitoramento"""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'gemini_configured': gemini_configured,
            'project': 'ESQUEMATIZA.AI'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# --- API: Matérias (Cacheada) ---
@app.route('/api/materias')
def api_materias():
    cache_key = 'materias_all'
    cached_data = materias_cache.get(cache_key)
    if cached_data:
        logger.info("Retornando matérias do cache")
        return jsonify(cached_data)
    
    conn = None
    try:
        conn = get_db_connection()
        materias_db = conn.execute('''
            SELECT materia, disciplina, COUNT(*) as total_questoes 
            FROM questoes 
            GROUP BY materia, disciplina 
            ORDER BY disciplina, materia
        ''').fetchall()
        
        materias_por_area = {}
        
        for row in materias_db:
            materia_dict = dict(row)
            materia_chave = materia_dict['materia'] 
            
            materia_nome_exibicao = corrigir_encoding(materia_chave)
            disciplina = corrigir_encoding(materia_dict['disciplina'])
            area = get_area(materia_nome_exibicao)
            
            if area not in materias_por_area:
                materias_por_area[area] = []
            
            if not any(m['materia_chave'] == materia_chave for m in materias_por_area[area]):
                materias_por_area[area].append({
                    'materia_chave': materia_chave,
                    'materia_nome': materia_nome_exibicao,
                    'disciplina': disciplina,
                    'total_questoes': materia_dict['total_questoes']
                })
        
        areas_focadas = list(set(AREAS_CONHECIMENTO.values()))
        materias_finais = {
            area: dados for area, dados in materias_por_area.items() 
            if area in areas_focadas
        }

        response_data = {'success': True, 'areas': materias_finais}
        materias_cache.set(cache_key, response_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"ERRO /api/materias: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500
    finally:
        if conn:
            conn.close()
# --- API: Simulado ROBUSTA com Validação ---
@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    conn = None
    logger.info("🎯 Iniciando simulado...")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados JSON inválidos'}), 400
            
        materias = data.get('materias', [])
        quantidade = int(data.get('quantidade', 10))

        # Validação robusta
        if not materias or not isinstance(materias, list):
            return jsonify({'success': False, 'error': 'Lista de matérias inválida'}), 400
        
        if quantidade < 1 or quantidade > 100:
            return jsonify({'success': False, 'error': 'Quantidade deve ser entre 1 e 100'}), 400

        conn = get_db_connection()
        
        placeholders = ','.join(['?'] * len(materias))
        query = f'''
            SELECT id, disciplina, materia, enunciado, alternativas, resposta_correta, 
                   justificativa, dificuldade, peso, dica, formula 
            FROM questoes 
            WHERE materia IN ({placeholders}) 
            ORDER BY RANDOM() 
            LIMIT ?
        '''
        
        params = materias + [quantidade]
        logger.info(f"🔍 Buscando {quantidade} questões em {len(materias)} matérias")
        
        questoes_db = conn.execute(query, params).fetchall()
        
        if not questoes_db:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada para as matérias selecionadas'}), 404

        # Preparar simulado
        simulado_id = f"sim_{int(time.time())}_{random.randint(1000, 9999)}"
        
        if 'user_id' not in session:
            session['user_id'] = f"user_{random.randint(10000, 99999)}"

        simulado_data = {
            'simulado_id': simulado_id,
            'questoes': [],
            'respostas': {},
            'indice_atual': 0,
            'data_inicio': datetime.now().isoformat(),
            'materias_selecionadas': materias
        }

        # Processar questões
        for questao_db in questoes_db:
            questao_dict = dict(questao_db)
            
            # Aplicar encoding correction em todos os campos de texto
            for key in ['disciplina', 'materia', 'enunciado', 'justificativa', 'dica', 'formula', 'resposta_correta']:
                if questao_dict.get(key) is not None:
                    questao_dict[key] = corrigir_encoding(questao_dict[key])
            
            # Processar alternativas
            if isinstance(questao_dict.get('alternativas'), str):
                questao_dict['alternativas'] = safe_json_loads(questao_dict['alternativas'])
            
            # Calcular peso se não existir
            if questao_dict.get('peso') is None:
                dificuldade = questao_dict.get('dificuldade', 'Baixa').lower()
                peso = 1
                if 'média' in dificuldade: peso = 2
                elif 'alta' in dificuldade: peso = 3
                questao_dict['peso'] = peso
            
            simulado_data['questoes'].append(questao_dict)

        session['simulado_atual'] = simulado_data
        session.modified = True

        # Preparar primeira questão
        primeira_questao = simulado_data['questoes'][0]
        
        questao_frontend = {
            'id': primeira_questao.get('id'),
            'disciplina': primeira_questao.get('disciplina'),
            'materia': primeira_questao.get('materia'),
            'enunciado': primeira_questao.get('enunciado'),
            'alternativas': primeira_questao.get('alternativas'),
            'dificuldade': primeira_questao.get('dificuldade'),
            'peso': primeira_questao.get('peso'),
            'dica': primeira_questao.get('dica'),
            'formula': primeira_questao.get('formula')
        }

        logger.info(f"✅ Simulado {simulado_id} iniciado com {len(questoes_db)} questões")
        
        return jsonify({
            'success': True, 
            'total_questoes': len(questoes_db),
            'questao': questao_frontend,
            'indice_atual': 0
        })

    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return jsonify({'success': False, 'error': 'Dados de entrada inválidos'}), 400
    except Exception as e:
        logger.error(f"ERRO CRÍTICO /simulado/iniciar: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500
    finally:
        if conn:
            conn.close()
# ... (mantido o restante das rotas do simulado com a mesma robustez)

@app.route('/api/simulado/questao/<int:indice>')
def get_questao_simulado(indice):
    try:
        if 'simulado_atual' not in session:
            return jsonify({'success': False, 'error': 'Nenhum simulado ativo'}), 400

        simulado = session['simulado_atual']
        questoes = simulado['questoes']
        
        if indice < 0 or indice >= len(questoes):
            return jsonify({'success': False, 'error': 'Índice inválido'}), 400

        simulado['indice_atual'] = indice
        session.modified = True

        questao = questoes[indice]
        
        resposta_anterior = simulado['respostas'].get(str(questao['id']))
        
        questao_frontend = {
            'id': questao.get('id'),
            'disciplina': questao.get('disciplina'),
            'materia': questao.get('materia'),
            'enunciado': questao.get('enunciado'),
            'alternativas': questao.get('alternativas'),
            'dificuldade': questao.get('dificuldade'),
            'peso': questao.get('peso'),
            'dica': questao.get('dica'),
            'formula': questao.get('formula')
        }

        return jsonify({
            'success': True,
            'questao': questao_frontend,
            'resposta_anterior': resposta_anterior,
            'indice_atual': indice,
            'total_questoes': len(questoes)
        })

    except Exception as e:
        logger.error(f"ERRO /simulado/questao: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    try:
        if 'simulado_atual' not in session:
            return jsonify({'success': False, 'error': 'Nenhum simulado ativo'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
            
        questao_id = data.get('questao_id')
        alternativa = data.get('alternativa', '').strip().upper()

        if not questao_id:
            return jsonify({'success': False, 'error': 'ID da questão não fornecido'}), 400
            
        if not alternativa or alternativa not in ['A', 'B', 'C', 'D', 'E']:
            return jsonify({'success': False, 'error': 'Alternativa inválida'}), 400

        simulado = session['simulado_atual']
        
        questao_atual = None
        for q in simulado['questoes']:
            if str(q['id']) == str(questao_id):
                questao_atual = q
                break

        if not questao_atual:
            return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404

        resposta_correta = questao_atual['resposta_correta'].strip().upper()
        acertou = (alternativa == resposta_correta)
        
        peso_questao = questao_atual.get('peso', 1)
        pontos = peso_questao if acertou else 0

        simulado['respostas'][str(questao_id)] = {
            'alternativa_escolhida': alternativa,
            'acertou': acertou,
            'timestamp': datetime.now().isoformat(),
            'pontos': pontos, 
            'peso': peso_questao
        }
        
        session.modified = True
        
        # Lógica de Dicas de Interpretação
        materia = questao_atual.get('materia', '').lower()
        dicas_interpretacao = "Dica: Analise o enunciado e o comando (o que a questão realmente pede). Cuidado com generalizações como 'sempre' ou 'nunca'."
        
        if 'matemática' in materia or 'raciocínio' in materia:
             dicas_interpretacao = "Dica: Estruture os dados. Se for Raciocínio, tente desenhar diagramas. Se for Matemática, identifique a fórmula chave antes de calcular."
        elif 'direito' in materia:
             dicas_interpretacao = "Dica: Identifique a base legal (artigo, lei). Questões de Direito costumam ter 'pegadinhas' em palavras como 'pode' vs 'deve'."
        elif 'portuguesa' in materia:
             dicas_interpretacao = "Dica: Volte ao texto para conferir a interpretação. Diferencie 'interpretar' (inferir) de 'compreender' (o que está escrito)."
        
        return jsonify({
            'success': True,
            'acertou': acertou,
            'resposta_correta': resposta_correta,
            'justificativa': questao_atual.get('justificativa', 'Sem justificativa disponível.'),
            'dica': questao_atual.get('dica', ''),
            'formula': questao_atual.get('formula', ''),
            'dicas_interpretacao': dicas_interpretacao
        })

    except Exception as e:
        logger.error(f"ERRO /simulado/responder: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@app.route('/api/simulado/finalizar', methods=['POST'])
def finalizar_simulado():
    conn = None
    try:
        if 'simulado_atual' not in session:
            return jsonify({'success': False, 'error': 'Nenhum simulado ativo'}), 400

        simulado = session['simulado_atual']
        
        total_questoes = len(simulado['questoes'])
        total_respondidas = len(simulado['respostas'])
        total_acertos = sum(1 for r in simulado['respostas'].values() if r['acertou'])
        
        total_peso = sum(q.get('peso', 1) for q in simulado['questoes'])
        pontos_obtidos = sum(r.get('pontos', 0) for r in simulado['respostas'].values())
        
        nota_final = (pontos_obtidos / total_peso) * 100 if total_peso > 0 else 0
        percentual_acerto_simples = (total_acertos / total_questoes) * 100 if total_questoes > 0 else 0

        relatorio = {
            'simulado_id': simulado['simulado_id'],
            'total_questoes': total_questoes,
            'total_respondidas': total_respondidas,
            'total_acertos': total_acertos,
            'pontos_obtidos': round(pontos_obtidos, 2),
            'total_peso': round(total_peso, 2),
            'percentual_acerto_simples': round(percentual_acerto_simples, 2),
            'nota_final': round(nota_final, 2), 
            'data_fim': datetime.now().isoformat(),
            'materias': simulado.get('materias_selecionadas', [])
        }

        # Salvar histórico
        try:
            conn = get_db_connection()
            if conn:
                conn.execute('''
                    INSERT INTO historico_simulados 
                    (user_id, simulado_id, respostas, relatorio, data_fim)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    session.get('user_id', 'anon'),
                    simulado['simulado_id'],
                    json.dumps(simulado['respostas']),
                    json.dumps(relatorio),
                    relatorio['data_fim']
                ))
                conn.commit()
        except Exception as db_error:
            logger.error(f"Erro ao salvar histórico: {db_error}")
        finally:
            if conn:
                conn.close()
# Limpar simulado
        session.pop('simulado_atual', None)
        
        logger.info(f"✅ Simulado finalizado. Nota: {nota_final:.2f}%")
        
        return jsonify({
            'success': True,
            'relatorio': relatorio
        })

    except Exception as e:
        logger.error(f"ERRO /simulado/finalizar: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

# --- API: Redação com Melhor Tratamento de Erros ---
@app.route('/api/redacao/temas')
def get_temas_redacao():
    cache_key = 'temas_redacao'
    cached_data = temas_cache.get(cache_key)
    if cached_data:
        return jsonify(cached_data)
    
    conn = None
    try:
        conn = get_db_connection()
        temas_db = conn.execute("SELECT * FROM temas_redacao ORDER BY titulo").fetchall()
        temas = []
        for row in temas_db:
            tema_dict = dict(row)
            tema_dict['titulo'] = corrigir_encoding(tema_dict['titulo'])
            tema_dict['descricao'] = corrigir_encoding(tema_dict.get('descricao', ''))
            temas.append(tema_dict)

        response_data = {'success': True, 'temas': temas}
        temas_cache.set(cache_key, response_data)
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"ERRO /api/redacao/temas: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500
    finally:
        if conn:
            conn.close()
@app.route('/api/redacao/corrigir-gemini', methods=['POST'])
def corrigir_redacao_gemini():
    logger.info("📝 Iniciando correção de redação...")

    if not gemini_configured:
        return jsonify({'success': False, 'error': 'API Gemini não configurada'}), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
            
        texto_redacao = data.get('texto', '').strip()
        tema_titulo = data.get('tema', '').strip()

        if not texto_redacao:
            return jsonify({'success': False, 'error': 'Texto da redação não fornecido'}), 400
        if not tema_titulo:
            return jsonify({'success': False, 'error': 'Tema não fornecido'}), 400

        if len(texto_redacao) < 100:
            return jsonify({'success': False, 'error': 'Texto muito curto (mínimo 100 caracteres)'}), 400

        logger.info(f"📋 Tema: {tema_titulo}")

        model = genai.GenerativeModel(MODEL_NAME)

        prompt = f"""
        CORRIJA ESTA DISSERTAÇÃO PARA CONCURSOS PÚBLICOS COM BASE NO TEMA: "{tema_titulo}"
        A nota máxima é 100 pontos (cada competência vale no máximo 20). Utilize métricas rigorosas de correção de concursos públicos.

        TEXTO DO CANDIDATO:
        {texto_redacao}

        MÉTRICAS DE CORREÇÃO (0-20 PONTOS CADA):
        1. Estrutura e Formato (Introdução, Dvl, Conclusão, Concisão).
        2. Coerência e Coesão (Uso de Conectivos, Lógica Argumentativa).
        3. Desenvolvimento do Tema e Fundamentação (Repertório e Profundidade).
        4. Norma Culta (Gramática, Ortografia, Sintaxe, Vocabulário).
        5. Proposta de Intervenção/Solução (Clareza e Pertinência, se cabível ao tema).

        RETORNE APENAS JSON com esta estrutura EXATA, GARANTINDO QUE OS COMENTÁRIOS SEJAM DETALHADOS E CONSTRUTIVOS:
        {{
            "nota_final": 0-100,
            "analise_competencias": [
                {{"competencia": "1. Estrutura e Formato (Concisão)", "nota": 0-20, "comentario": "Análise detalhada..."}},
                {{"competencia": "2. Coerência e Coesão", "nota": 0-20, "comentario": "Análise detalhada..."}},
                {{"competencia": "3. Desenvolvimento do Tema e Fundamentação", "nota": 0-20, "comentario": "Análise detalhada..."}},
                {{"competencia": "4. Norma Culta", "nota": 0-20, "comentario": "Análise detalhada..."}},
                {{"competencia": "5. Proposta de Intervenção/Solução", "nota": 0-20, "comentario": "Análise detalhada..."}}
            ],
            "pontos_fortes": ["lista", "de", "pontos", "fortes"],
            "pontos_fracos": ["lista", "de", "pontos", "a", "melhorar"],
            "sugestoes_melhoria": ["sugestões", "concretas"],
            "dicas_concursos": ["dicas", "específicas", "para", "concursos"]
        }}
        """

        logger.info("🔄 Enviando para Gemini...")
        response = model.generate_content(prompt)
        logger.info("✅ Resposta recebida")

        raw_text = response.text.strip()
        
        # Limpar JSON
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        correcao_data = json.loads(raw_text)
        
        # Recalcular nota
        nota_calculada = sum(comp['nota'] for comp in correcao_data['analise_competencias'])
        correcao_data['nota_final'] = min(100, max(0, nota_calculada))  # Garantir entre 0-100

        logger.info(f"✅ Correção concluída - Nota: {nota_calculada}")
        return jsonify({'success': True, 'correcao': correcao_data})

    except Exception as e:
        logger.error(f"❌ ERRO na correção: {e}")
        return jsonify({'success': False, 'error': f'Erro na correção: {str(e)}'}), 500

# --- API: Dashboard com Cache ---
@app.route('/api/dashboard/estatisticas')
def api_dashboard_estatisticas():
    logger.info(f'API /dashboard/estatisticas: Iniciando...') # Log inicio
    try:
        logger.info(f'API /dashboard/estatisticas: Conectando ao DB em {DB_PATH}')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Estatísticas do banco
        logger.info('API /dashboard: Executando queries de contagem...')
        cursor.execute("SELECT COUNT(*) FROM questions")
        total_questoes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM redacao_temas")
        total_temas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT materia) FROM questions")
        total_materias = cursor.fetchone()[0]

        conn.close()
        logger.info('API /dashboard: Conexão com DB fechada.')

        resultado = {
            'total_questoes': total_questoes,
            'total_temas': total_temas,
            'total_materias': total_materias,
            'ultima_atualizacao': datetime.now().isoformat()
        }
        logger.info(f'API /dashboard: Estatísticas calculadas: {resultado}')
        return jsonify(resultado) # <--- Return DENTRO do try

    except Exception as e: # <--- Bloco EXCEPT CORRETO
        logger.error(f'API /dashboard/estatisticas: ERRO CRÍTICO - {e}')
        return jsonify({'error': 'Erro interno ao buscar estatísticas'}), 500

        historico = [safe_json_loads(row['relatorio']) for row in historico_db]
        
        total_simulados = len(historico)
        total_questoes_respondidas = sum(h.get('total_respondidas', 0) for h in historico)
        media_geral = sum(h.get('nota_final', 0) for h in historico) / total_simulados if total_simulados > 0 else 0
        media_acertos = sum(h.get('percentual_acerto_simples', 0) for h in historico) / total_simulados if total_simulados > 0 else 0

        return jsonify({
            'success': True,
            'total_simulados': total_simulados,
            'total_questoes_respondidas': total_questoes_respondidas,
            'media_geral': round(media_geral, 2),
            'media_acertos': round(media_acertos, 2),
            'historico_recente': historico[:5]
        })

    except Exception as e:
        logger.error(f"ERRO /api/dashboard/estatisticas: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500
    finally:
        if conn:
            conn.close()
# --- Error Handlers Globais ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro 500: {error}")
    return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'success': False, 'error': 'Arquivo muito grande'}), 413

# --- Inicialização Robusta ---
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 SISTEMA ESQUEMATIZA.AI - VERSÃO ROBUSTA")
    print("="*60)
    
    try:
        # Verificar banco de dados
        conn = get_db_connection()
        if conn:
            count_questoes = conn.execute("SELECT COUNT(*) FROM questoes").fetchone()[0]
            count_temas = conn.execute("SELECT COUNT(*) FROM temas_redacao").fetchone()[0]
            print(f"📚 Questões no banco: {count_questoes}")
            print(f"📝 Temas de redação: {count_temas}")
            conn.close()
except Exception as e:
        print(f"⚠️  Aviso no banco: {e}")

    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🌐 Servidor: http://127.0.0.1:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"🤖 Gemini: {'✅ Configurado' if gemini_configured else '❌ Não configurado'}")
    print(f"📊 Logging: ✅ Ativo (logs/app.log)")
    print("="*60)
    
    # Configurar para produção
    if not debug:
        from waitress import serve
        print("🚀 Iniciando servidor Waitress para produção...")
        serve(app, host='0.0.0.0', port=port)
    else:
        app.run(debug=debug, host='0.0.0.0', port=port)







