import os
import sqlite3
import json
import google.generativeai as genai
from datetime import datetime
import logging
import random # Adicionado para simulado_id
import glob   # Adicionado para debug route (se ainda existir)
from whitenoise import WhiteNoise # Adicionado para arquivos estáticos
from flask import Flask, render_template, jsonify, request, session, send_from_directory # Imports corretos

# ========== CONFIGURAÇÃO INICIAL ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definir o caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'concursos.db')
logger.info(f'--- CAMINHO DO BANCO DE DADOS DEFINIDO: {DB_PATH} ---')

# --- VERIFICAÇÃO DO BANCO DE DADOS (Início) ---
# (Removido o bloco de verificação que causava erros, confiamos no tamanho agora)
try:
    if os.path.exists(DB_PATH):
        db_size = os.path.getsize(DB_PATH)
        logger.info(f'--- DB Check: {DB_PATH} encontrado (Tamanho: {db_size} bytes) ---')
    else:
        logger.error(f'--- DB Check: {DB_PATH} NÃO ENCONTRADO! ---')
except Exception as e:
    logger.error(f'--- DB Check: Erro ao verificar {DB_PATH}: {e} ---')
# --- FIM DA VERIFICAÇÃO ---

app = Flask(__name__)
# Configurar Whitenoise para servir arquivos estáticos da pasta 'static/'
# O prefixo '/static' é adicionado automaticamente por Whitenoise
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')
logger.info("✅ Whitenoise configurado para servir arquivos estáticos.")


# Configuração do Gemini (agora tenta configurar, mas não impede o boot se falhar)
try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        logger.info("✅ Gemini configurado: models/gemini-2.0-flash") # Ajuste o modelo se necessário
    else:
        logger.warning("⚠️ GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
except Exception as e:
    logger.error(f"❌ Erro inicial ao configurar Gemini: {e} - Aplicação continuará, mas correção de redação falhará.")


# ========== ROTAS PRINCIPAIS (HTML) ==========

@app.route('/')
def index():
    return render_template('index.html')

# Adicione outras rotas HTML se necessário (ex: /simulado, /redacao, /dashboard)
# @app.route('/simulado')
# def simulado_page():
#    return render_template('simulado.html')

# @app.route('/redacao')
# def redacao_page():
#    return render_template('redacao.html')

# @app.route('/dashboard')
# def dashboard_page():
#    return render_template('dashboard.html')


# ========== API - MATÉRIAS ==========

@app.route('/api/materias')
def api_materias():
    logger.info(f'API /api/materias: Iniciando...')
    try:
        logger.info(f'API /api/materias: Conectando ao DB em {DB_PATH}')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        logger.info('API /api/materias: Executando query...')
        cursor.execute("SELECT DISTINCT materia FROM questions")
        materias = [row[0] for row in cursor.fetchall()]
        conn.close()
        logger.info(f'API /api/materias: ENCONTRADO {len(materias)} matérias distintas. Conexão fechada.')
        return jsonify(materias)
    except Exception as e:
        logger.error(f'API /api/materias: ERRO CRÍTICO - {e}')
        return jsonify({'error': 'Erro interno ao buscar matérias'}), 500


# ========== API - SIMULADOS ==========

simulados_ativos = {} # Atenção: Isso é perdido a cada reinício do servidor!

@app.route('/api/simulado/iniciar', methods=['POST'])
def api_simulado_iniciar():
    logger.info(f'API /api/simulado/iniciar: Iniciando...')
    try:
        data = request.json
        materia = data.get('materia', 'todas')
        quantidade = int(data.get('quantidade', 10))
        logger.info(f'API /simulado/iniciar: Buscando {quantidade} questões de {materia}')

        logger.info(f'API /simulado/iniciar: Conectando ao DB em {DB_PATH}')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if materia == 'todas' or not materia:
            cursor.execute("SELECT id, materia, enunciado, alternativas, resposta_correta, explicacao FROM questions ORDER BY RANDOM() LIMIT ?", (quantidade,))
        else:
            cursor.execute("SELECT id, materia, enunciado, alternativas, resposta_correta, explicacao FROM questions WHERE materia = ? ORDER BY RANDOM() LIMIT ?", (materia, quantidade))

        questions_raw = cursor.fetchall()
        logger.info(f'API /simulado/iniciar: Query retornou {len(questions_raw)} linhas.')

        questions = []
        for row in questions_raw:
            try:
                alternativas_dict = json.loads(row[3]) # Índice 3 é 'alternativas'
            except json.JSONDecodeError:
                logger.warning(f"API /simulado/iniciar: JSON inválido para alternativas na questão ID {row[0]}. Pulando questão.")
                continue # Pula esta questão se o JSON estiver ruim

            questions.append({
                'id': row[0],
                'materia': row[1],
                'questao': row[2],
                'alternativas': alternativas_dict,
                'resposta_correta': row[4],
                'explicacao': row[5]
            })

        conn.close()
        logger.info(f'API /simulado/iniciar: ENCONTRADO {len(questions)} questões válidas. Conexão fechada.')

        if not questions:
             logger.error(f'API /simulado/iniciar: Nenhuma questão encontrada para os critérios!')
             return jsonify({'error': 'Nenhuma questão encontrada para esta matéria/quantidade'}), 404


        # Criar simulado (simples, em memória)
        simulado_id = f"sim_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        simulados_ativos[simulado_id] = {
            'questoes': questions,
            'respostas': {}, # Usar dict para fácil acesso por ID
            'inicio': datetime.now().isoformat()
        }

        logger.info(f"🎯 Simulado {simulado_id} iniciado com {len(questions)} questões.")

        # Retornar apenas os dados necessários para o frontend iniciar
        questoes_frontend = [{
            'id': q['id'],
            'materia': q['materia'],
            'questao': q['questao'],
            'alternativas': q['alternativas'] # Frontend precisa das alternativas
            # NÃO ENVIAR resposta_correta ou explicacao agora
         } for q in questions]


        return jsonify({
            'simulado_id': simulado_id,
            'questoes': questoes_frontend, # Envia versão limpa
            'total': len(questoes_frontend)
        })

    except Exception as e:
        logger.error(f"API /api/simulado/iniciar: ERRO CRÍTICO - {e}", exc_info=True) # Log completo do erro
        return jsonify({'error': 'Erro interno ao iniciar simulado'}), 500

@app.route('/api/simulado/responder', methods=['POST'])
def api_simulado_responder():
    # Simplesmente registra a resposta, sem validação imediata
    try:
        data = request.json
        simulado_id = data.get('simulado_id')
        questao_id = data.get('questao_id')
        resposta_usuario = data.get('resposta')

        if not simulado_id or questao_id is None or resposta_usuario is None:
             return jsonify({'error': 'Dados incompletos'}), 400

        if simulado_id not in simulados_ativos:
            return jsonify({'error': 'Simulado não encontrado ou expirado'}), 404

        simulados_ativos[simulado_id]['respostas'][questao_id] = resposta_usuario
        #logger.info(f"Simulado {simulado_id}: Resposta registrada para questão {questao_id}")
        return jsonify({'status': 'resposta registrada'})

    except Exception as e:
        logger.error(f"API /api/simulado/responder: ERRO CRÍTICO - {e}", exc_info=True)
        return jsonify({'error': 'Erro interno ao registrar resposta'}), 500


@app.route('/api/simulado/finalizar', methods=['POST'])
def api_simulado_finalizar():
    logger.info(f'API /api/simulado/finalizar: Iniciando...')
    try:
        data = request.json
        simulado_id = data.get('simulado_id')

        if simulado_id not in simulados_ativos:
            logger.warning(f"API /finalizar: Tentativa de finalizar simulado inexistente: {simulado_id}")
            return jsonify({'error': 'Simulado não encontrado ou já finalizado'}), 404

        simulado = simulados_ativos[simulado_id]
        questoes_simulado = simulado['questoes']
        respostas_usuario = simulado['respostas']
        resultados_detalhados = []
        acertos = 0

        logger.info(f"API /finalizar: Corrigindo simulado {simulado_id}...")
        for questao in questoes_simulado:
            q_id = questao['id']
            resposta_correta = questao['resposta_correta']
            resposta_dada = respostas_usuario.get(q_id) # Pega a resposta do usuário para essa questão
            acertou = (resposta_dada == resposta_correta)

            if acertou:
                acertos += 1

            resultados_detalhados.append({
                'id': q_id,
                'materia': questao['materia'],
                'questao': questao['questao'],
                'alternativas': questao['alternativas'],
                'resposta_correta': resposta_correta,
                'resposta_dada': resposta_dada,
                'acertou': acertou,
                'explicacao': questao.get('explicacao', 'Explicação não disponível.') # Usa .get() por segurança
            })

        total_questoes = len(questoes_simulado)
        percentual = round((acertos / total_questoes) * 100, 1) if total_questoes > 0 else 0

        resultado_final = {
            'simulado_id': simulado_id,
            'acertos': acertos,
            'total': total_questoes,
            'percentual': percentual,
            'resultados': resultados_detalhados # Envia detalhes para o frontend exibir
        }

        logger.info(f"✅ Simulado {simulado_id} finalizado: {acertos}/{total_questoes} acertos ({percentual}%)")

        # Limpar da memória
        del simulados_ativos[simulado_id]

        return jsonify(resultado_final)

    except Exception as e:
        logger.error(f"API /api/simulado/finalizar: ERRO CRÍTICO - {e}", exc_info=True)
        return jsonify({'error': 'Erro interno ao finalizar simulado'}), 500


# ========== API - REDAÇÃO ==========

@app.route('/api/redacao/temas')
def api_redacao_temas():
    logger.info(f'API /api/redacao/temas: Iniciando...')
    try:
        logger.info(f'API /redacao/temas: Conectando ao DB em {DB_PATH}')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Ajuste: Selecionar colunas que existem na tabela 'temas_redacao'
        # (Baseado no script importar_dados.py, a tabela tem: id, titulo, descricao, tipo, dificuldade, palavras_chave)
        logger.info('API /redacao/temas: Executando query...')
        cursor.execute("SELECT id, titulo, tipo, dificuldade FROM temas_redacao ORDER BY titulo") # Removido 'categoria' se não existir
        temas = [{'id': row[0], 'tema': row[1], 'tipo': row[2], 'dificuldade': row[3]} for row in cursor.fetchall()]
        conn.close()
        logger.info(f'API /redacao/temas: ENCONTRADO {len(temas)} temas. Conexão fechada.')
        return jsonify(temas)
    except Exception as e:
        logger.error(f'API /api/redacao/temas: ERRO CRÍTICO - {e}')
        # Log específico para erro de coluna
        if isinstance(e, sqlite3.OperationalError) and 'no such column' in str(e):
             logger.error(f"VERIFIQUE A ESTRUTURA DA TABELA 'temas_redacao'! Coluna faltando.")
        return jsonify({'error': 'Erro interno ao buscar temas de redação'}), 500


@app.route('/api/redacao/corrigir-gemini', methods=['POST'])
def api_redacao_corrigir_gemini():
    logger.info(f"API /api/redacao/corrigir-gemini: Iniciando...")
    try:
        data = request.json
        tema = data.get('tema')
        texto = data.get('texto')

        if not tema or not texto:
            logger.warning("API /corrigir-gemini: Requisição inválida - tema ou texto faltando.")
            return jsonify({'error': 'Tema e texto são obrigatórios'}), 400

        logger.info(f"API /corrigir-gemini: Recebido - Tema: {tema}, Texto: {len(texto)} chars")

        # Tenta configurar/usar Gemini AQUI
        try:
            current_api_key = os.environ.get('GEMINI_API_KEY')
            if not current_api_key:
                 raise ValueError("Chave da API Gemini não configurada no ambiente.")
            genai.configure(api_key=current_api_key) # Reconfigura a cada chamada para garantir
            model = genai.GenerativeModel('gemini-pro') # Use o modelo desejado (gemini-pro, gemini-flash, etc.)
            logger.info("API /corrigir-gemini: Modelo Gemini carregado.")
        except Exception as e_gemini_config:
            logger.error(f'API /corrigir-gemini: ERRO CRÍTICO ao configurar Gemini - {e_gemini_config}')
            return jsonify({'error': f'Falha ao configurar API do Gemini: {e_gemini_config}'}), 503 # Service Unavailable


        prompt = f"""
        CORREÇÃO DE REDAÇÃO - MODELO ENEM

        TEMA: {tema}

        TEXTO DO ESTUDANTE:
        {texto}

        ANALISE ESTA REDAÇÃO SEGUINDO OS 5 CRITÉRIOS DO ENEM (0-200 pontos cada):
        1. Domínio da norma culta.
        2. Compreensão do tema e estrutura dissertativo-argumentativa.
        3. Seleção, relação, organização e interpretação de informações, fatos, opiniões e argumentos em defesa de um ponto de vista.
        4. Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação (coesão).
        5. Elaboração de proposta de intervenção para o problema abordado, respeitando os direitos humanos.

        FORNEÇA O FEEDBACK EM MARKDOWN, INCLUINDO:
        - Nota Final (SOMA DAS COMPETÊNCIAS, 0-1000) - Coloque no formato: **Nota Final:** XXXX/1000
        - Análise detalhada por Competência (C1 a C5), com a pontuação de cada uma.
        - Pontos Fortes gerais.
        - Pontos a Melhorar gerais.
        - Sugestões Específicas para aprimoramento.
        """

        logger.info("API /corrigir-gemini: Enviando prompt para Gemini...")
        response = model.generate_content(prompt)
        correcao_md = response.text
        logger.info("API /corrigir-gemini: Resposta recebida do Gemini.")

        # Extrair nota (Regex mais robusto)
        nota = 0 # Default
        try:
            # Procura por "Nota Final:", seguido de espaços, seguido de 3 ou 4 dígitos
            nota_match = re.search(r"Nota Final:\s*(\d{3,4})", correcao_md, re.IGNORECASE)
            if nota_match:
                nota = int(nota_match.group(1))
                logger.info(f"API /corrigir-gemini: Nota extraída da resposta: {nota}")
            else:
                logger.warning("API /corrigir-gemini: Não foi possível extrair a nota do texto. Usando 0.")
        except Exception as e_nota:
             logger.error(f"API /corrigir-gemini: Erro ao extrair nota: {e_nota}")


        logger.info(f"✅ Correção concluída - Nota: {nota}")

        return jsonify({
            'nota': nota,
            'correcao': correcao_md, # Envia o markdown completo
            'tema': tema,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"API /api/redacao/corrigir-gemini: ERRO CRÍTICO - {e}", exc_info=True)
        # Verifica se o erro foi da API do Google especificamente
        if "API key not valid" in str(e):
             return jsonify({'error': 'Chave da API Gemini inválida. Verifique as variáveis de ambiente.'}), 401 # Unauthorized
        return jsonify({'error': 'Erro interno ao processar correção'}), 500


# ========== API - DASHBOARD ==========

@app.route('/api/dashboard/estatisticas')
def api_dashboard_estatisticas():
    logger.info(f'API /api/dashboard/estatisticas: Iniciando...')
    try:
        logger.info(f'API /dashboard/estatisticas: Conectando ao DB em {DB_PATH}')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Estatísticas do banco
        logger.info('API /dashboard: Executando queries de contagem...')
        cursor.execute("SELECT COUNT(*) FROM questions")
        total_questoes = cursor.fetchone()[0]
        logger.info(f'API /dashboard: Contagem Questoes = {total_questoes}')

        cursor.execute("SELECT COUNT(*) FROM temas_redacao")
        total_temas = cursor.fetchone()[0]
        logger.info(f'API /dashboard: Contagem Temas = {total_temas}')

        cursor.execute("SELECT COUNT(DISTINCT materia) FROM questions")
        total_materias = cursor.fetchone()[0]
        logger.info(f'API /dashboard: Contagem Materias = {total_materias}')

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
        logger.error(f'API /dashboard/estatisticas: ERRO CRÍTICO - {e}', exc_info=True)
        # Verifica se o erro foi de tabela/coluna inexistente
        if isinstance(e, sqlite3.OperationalError) and ('no such table' in str(e) or 'no such column' in str(e)):
             logger.error("VERIFIQUE A ESTRUTURA DO BANCO DE DADOS! Tabela ou coluna faltando.")
             return jsonify({'error': f'Erro no banco de dados: {e}'}), 500
        return jsonify({'error': 'Erro interno ao buscar estatísticas'}), 500


# ========== ROTA DE DEBUG (Opcional, manter se útil) ==========
@app.route('/debug/list-files')
def list_files():
    # ...(código da função list_files)...
    # Vamos mantê-la por enquanto para verificar o DB
    logger.info("--- DEBUG: Listando arquivos no servidor ---")
    path = '/app'
    files_list = []
    try:
        for f in glob.glob(f'{path}/**', recursive=True):
            try:
                 if os.path.isfile(f):
                     file_size = os.path.getsize(f)
                     files_list.append(f'ARQUIVO: {f} (Tamanho: {file_size} bytes)')
                 #elif os.path.isdir(f): # Evitar listar todas as subpastas do venv se houver
                 #    files_list.append(f'PASTA: {f}')
            except OSError:
                 files_list.append(f'ARQUIVO/PASTA: {f} (Erro ao acessar)')
        logger.info(f"DEBUG /list-files: {files_list}")
        return jsonify(sorted(files_list)) # Ordena para facilitar a leitura
    except Exception as e:
        logger.error(f'DEBUG /list-files: Erro - {e}')
        return jsonify({'error': str(e)}), 500


# ========== NÃO ADICIONAR app.run() AQUI ==========
# O Gunicorn vai importar e rodar o objeto 'app' diretamente.
# O if __name__ == '__main__': é útil apenas para rodar localmente com 'python app.py'

# logger.info("Script app.py carregado pelo Gunicorn.") # Log final para confirmar

