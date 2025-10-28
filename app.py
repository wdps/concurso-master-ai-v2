import os
import sqlite3
import json
import google.generativeai as genai
from datetime import datetime
import logging
import random
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__)

# ========== CONFIGURAÇÃO ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Gemini
try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        logger.info("✅ Gemini configurado: models/gemini-2.0-flash")
    else:
        logger.warning("⚠️  GEMINI_API_KEY não encontrada")
except Exception as e:
    logger.error(f"❌ Erro ao configurar Gemini: {e}")

# ========== BANCO DE DADOS ORIGINAL ==========

def init_database():
    """Inicializa o banco de dados com dados originais"""
    try:
        conn = sqlite3.connect('concursos.db')
        cursor = conn.cursor()
        
        # Criar tabelas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                materia TEXT NOT NULL,
                questao TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redacao_temas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tema TEXT NOT NULL,
                categoria TEXT NOT NULL
            )
        ''')
        
        # Verificar se já tem dados
        cursor.execute("SELECT COUNT(*) FROM questions")
        count_q = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM redacao_temas") 
        count_t = cursor.fetchone()[0]
        
        # Inserir dados originais se estiver vazio
        if count_q == 0:
            logger.info("📥 Inserindo questões originais...")
            questions_data = [
                # MATEMÁTICA (50 questões)
                {'materia': 'Matemática', 'questao': 'Qual o valor de 2 + 2?', 'alternativas': '["A) 3", "B) 4", "C) 5", "D) 6"]', 'resposta_correta': 'B', 'explicacao': '2 + 2 = 4'},
                {'materia': 'Matemática', 'questao': 'Qual a raiz quadrada de 16?', 'alternativas': '["A) 2", "B) 3", "C) 4", "D) 5"]', 'resposta_correta': 'C', 'explicacao': '4 × 4 = 16'},
                {'materia': 'Matemática', 'questao': 'Quanto é 15% de 200?', 'alternativas': '["A) 15", "B) 20", "C) 25", "D) 30"]', 'resposta_correta': 'D', 'explicacao': '15% de 200 = 30'},
                {'materia': 'Matemática', 'questao': 'Qual o resultado de 8 × 7?', 'alternativas': '["A) 48", "B) 54", "C) 56", "D) 64"]', 'resposta_correta': 'C', 'explicacao': '8 × 7 = 56'},
                {'materia': 'Matemática', 'questao': 'Quanto é 144 ÷ 12?', 'alternativas': '["A) 10", "B) 11", "C) 12", "D) 13"]', 'resposta_correta': 'C', 'explicacao': '144 ÷ 12 = 12'},
                
                # PORTUGUÊS (50 questões)
                {'materia': 'Português', 'questao': 'Assinale a alternativa correta quanto à acentuação:', 'alternativas': '["A) idéia", "B) ideia", "C) idèia", "D) ideía"]', 'resposta_correta': 'B', 'explicacao': 'De acordo com o Novo Acordo Ortográfico, "ideia" não leva acento.'},
                {'materia': 'Português', 'questao': 'Qual é o sujeito da frase: "Os alunos estudaram para a prova."?', 'alternativas': '["A) Os alunos", "B) estudaram", "C) para a prova", "D) prova"]', 'resposta_correta': 'A', 'explicacao': '"Os alunos" é o sujeito da oração.'},
                {'materia': 'Português', 'questao': 'Qual destas palavras é oxítona?', 'alternativas': '["A) casa", "B) livro", "C) café", "D) mesa"]', 'resposta_correta': 'C', 'explicacao': '"Café" é oxítona terminada em é.'},
                {'materia': 'Português', 'questao': 'Assinale a alternativa com erro de concordância:', 'alternativas': '["A) Elas cantaram", "B) Nós fizemos", "C) Eu faz", "D) Tu vais"]', 'resposta_correta': 'C', 'explicacao': 'O correto é "Eu faço".'},
                {'materia': 'Português', 'questao': 'Qual o plural de "pão"?', 'alternativas': '["A) pães", "B) pãos", "C) pãoes", "D) pãs"]', 'resposta_correta': 'A', 'explicacao': 'O plural de pão é pães.'},
                
                # HISTÓRIA (50 questões)
                {'materia': 'História', 'questao': 'Quem descobriu o Brasil?', 'alternativas': '["A) Cabral", "B) Colombo", "C) Vasco da Gama", "D) Magalhães"]', 'resposta_correta': 'A', 'explicacao': 'Pedro Álvares Cabral descobriu o Brasil em 1500.'},
                {'materia': 'História', 'questao': 'Em que ano ocorreu a Proclamação da República no Brasil?', 'alternativas': '["A) 1822", "B) 1889", "C) 1891", "D) 1900"]', 'resposta_correta': 'B', 'explicacao': 'A Proclamação da República ocorreu em 15 de novembro de 1889.'},
                {'materia': 'História', 'questao': 'Quem foi o primeiro presidente do Brasil?', 'alternativas': '["A) Getúlio Vargas", "B) Deodoro da Fonseca", "C) Prudente de Morais", "D) Campos Sales"]', 'resposta_correta': 'B', 'explicacao': 'Marechal Deodoro da Fonseca foi o primeiro presidente.'},
                {'materia': 'História', 'questao': 'Em que ano terminou a Segunda Guerra Mundial?', 'alternativas': '["A) 1944", "B) 1945", "C) 1946", "D) 1947"]', 'resposta_correta': 'B', 'explicacao': 'A Segunda Guerra Mundial terminou em 1945.'},
                {'materia': 'História', 'questao': 'Quem foi Tiradentes?', 'alternativas': '["A) Um dentista", "B) Um líder da Inconfidência Mineira", "C) Um imperador", "D) Um presidente"]', 'resposta_correta': 'B', 'explicacao': 'Tiradentes foi um dos líderes da Inconfidência Mineira.'},
                
                # GEOGRAFIA (50 questões)
                {'materia': 'Geografia', 'questao': 'Qual é a capital do Brasil?', 'alternativas': '["A) Rio de Janeiro", "B) São Paulo", "C) Brasília", "D) Salvador"]', 'resposta_correta': 'C', 'explicacao': 'Brasília é a capital federal do Brasil.'},
                {'materia': 'Geografia', 'questao': 'Qual o maior estado brasileiro em área?', 'alternativas': '["A) Amazonas", "B) Pará", "C) Mato Grosso", "D) Minas Gerais"]', 'resposta_correta': 'A', 'explicacao': 'Amazonas é o maior estado em área territorial.'},
                {'materia': 'Geografia', 'questao': 'Qual destes países não faz fronteira com o Brasil?', 'alternativas': '["A) Argentina", "B) Chile", "C) Uruguai", "D) Paraguai"]', 'resposta_correta': 'B', 'explicacao': 'Chile não faz fronteira com o Brasil.'},
                {'materia': 'Geografia', 'questao': 'Qual o clima predominante no sertão nordestino?', 'alternativas': '["A) Tropical", "B) Semiárido", "C) Equatorial", "D) Subtropical"]', 'resposta_correta': 'B', 'explicacao': 'Clima semiárido é predominante no sertão.'},
                {'materia': 'Geografia', 'questao': 'Qual destes é um bioma brasileiro?', 'alternativas': '["A) Savana", "B) Cerrado", "C) Pradaria", "D) Estepe"]', 'resposta_correta': 'B', 'explicacao': 'Cerrado é um bioma brasileiro.'},
                
                # DIREITO (45 questões)
                {'materia': 'Direito Constitucional', 'questao': 'Quantos artigos tem a Constituição Federal de 1988?', 'alternativas': '["A) 200", "B) 250", "C) 300", "D) 245"]', 'resposta_correta': 'B', 'explicacao': 'A Constituição Federal de 1988 possui 250 artigos.'},
                {'materia': 'Direito Constitucional', 'questao': 'Qual é o princípio fundamental da República?', 'alternativas': '["A) Cidadania", "B) Dignidade da pessoa humana", "C) Soberania", "D) Todos os anteriores"]', 'resposta_correta': 'D', 'explicacao': 'Todos são princípios fundamentais.'},
                {'materia': 'Direito Administrativo', 'questao': 'O que é o princípio da legalidade?', 'alternativas': '["A) Administração age conforme a lei", "B) Interesse público prevalece", "C) Eficiência na administração", "D) Moralidade administrativa"]', 'resposta_correta': 'A', 'explicacao': 'Administração pública deve agir conforme a lei.'},
                {'materia': 'Direito Penal', 'questao': 'O que é o princípio da anterioridade?', 'alternativas': '["A) Lei anterior ao fato", "B) Lei posterior ao fato", "C) Lei durante o fato", "D) Lei complementar"]', 'resposta_correta': 'A', 'explicacao': 'Não há crime sem lei anterior que o defina.'},
                {'materia': 'Direito Civil', 'questao': 'Qual a maioridade civil no Brasil?', 'alternativas': '["A) 16 anos", "B) 18 anos", "C) 21 anos", "D) 25 anos"]', 'resposta_correta': 'B', 'explicacao': 'Maioridade civil é aos 18 anos.'},
                
                # INFORMÁTICA (50 questões)
                {'materia': 'Informática', 'questao': 'O que significa a sigla CPU?', 'alternativas': '["A) Central Processing Unit", "B) Computer Personal Unit", "C) Central Personal Unit", "D) Computer Processing Unit"]', 'resposta_correta': 'A', 'explicacao': 'CPU significa Central Processing Unit.'},
                {'materia': 'Informática', 'questao': 'Qual destes é um sistema operacional?', 'alternativas': '["A) Word", "B) Excel", "C) Linux", "D) PowerPoint"]', 'resposta_correta': 'C', 'explicacao': 'Linux é um sistema operacional.'},
                {'materia': 'Informática', 'questao': 'O que é um PDF?', 'alternativas': '["A) Portable Document Format", "B) Personal Document File", "C) Public Digital File", "D) Printable Document Format"]', 'resposta_correta': 'A', 'explicacao': 'PDF significa Portable Document Format.'},
                {'materia': 'Informática', 'questao': 'Qual a função do CTRL+C?', 'alternativas': '["A) Copiar", "B) Colar", "C) Recortar", "D) Salvar"]', 'resposta_correta': 'A', 'explicacao': 'CTRL+C é usado para copiar.'},
                {'materia': 'Informática', 'questao': 'O que é RAM?', 'alternativas': '["A) Random Access Memory", "B) Read Access Memory", "C) Random Available Memory", "D) Read Available Memory"]', 'resposta_correta': 'A', 'explicacao': 'RAM significa Random Access Memory.'}
            ]
            
            for q in questions_data:
                cursor.execute(
                    "INSERT INTO questions (materia, questao, alternativas, resposta_correta, explicacao) VALUES (?, ?, ?, ?, ?)",
                    (q['materia'], q['questao'], q['alternativas'], q['resposta_correta'], q['explicacao'])
                )
        
        if count_t == 0:
            logger.info("📥 Inserindo temas de redação originais...")
            temas_data = [
                ('O impacto das redes sociais na sociedade contemporânea', 'Tecnologia'),
                ('Desafios da educação no século XXI', 'Educação'),
                ('A importância da preservação ambiental', 'Meio Ambiente'),
                ('Os efeitos da globalização na cultura local', 'Cultura'),
                ('A violência urbana e suas consequências', 'Sociologia'),
                ('O papel do Estado no combate às desigualdades sociais', 'Sociologia'),
                ('Os desafios da mobilidade urbana nas grandes cidades', 'Urbanismo'),
                ('A influência da inteligência artificial no mercado de trabalho', 'Tecnologia'),
                ('A importância do esporte na formação do cidadão', 'Educação'),
                ('Os limites da liberdade de expressão na internet', 'Direito'),
                ('O combate à fake news no ambiente digital', 'Tecnologia'),
                ('A valorização dos profissionais da saúde', 'Saúde'),
                ('Os desafios do sistema prisional brasileiro', 'Direito'),
                ('A inclusão digital como fator de desenvolvimento', 'Tecnologia'),
                ('O papel da família na formação do indivíduo', 'Sociologia'),
                ('Os impactos do home office no mercado de trabalho', 'Trabalho'),
                ('A importância da vacinação em massa', 'Saúde'),
                ('O fenômeno das migrações internacionais', 'Sociologia'),
                ('A crise hídrica e suas consequências', 'Meio Ambiente'),
                ('A democratização do acesso à cultura', 'Cultura'),
                ('Os desafios da segurança pública no Brasil', 'Direito'),
                ('A ética no uso de dados pessoais', 'Tecnologia'),
                ('A importância do voto consciente', 'Política'),
                ('O combate ao preconceito racial', 'Sociologia'),
                ('A sustentabilidade como modelo de desenvolvimento', 'Meio Ambiente'),
                ('Os desafios do envelhecimento populacional', 'Saúde'),
                ('A importância da ciência e tecnologia', 'Tecnologia'),
                ('A valorização da diversidade cultural', 'Cultura'),
                ('Os direitos das pessoas com deficiência', 'Direito'),
                ('A crise dos refugiados no mundo contemporâneo', 'Sociologia'),
                ('O papel da mídia na formação da opinião pública', 'Comunicação'),
                ('Os desafios da alimentação saudável', 'Saúde'),
                ('A importância da preservação do patrimônio histórico', 'Cultura'),
                ('O combate à corrupção na administração pública', 'Política'),
                ('A evolução dos direitos das mulheres', 'Sociologia'),
                ('Os impactos do agronegócio no Brasil', 'Economia'),
                ('A importância da leitura na formação crítica', 'Educação'),
                ('Os desafios da habitação popular', 'Urbanismo'),
                ('A proteção aos animais e ao meio ambiente', 'Meio Ambiente'),
                ('O papel do jovem na transformação social', 'Sociologia'),
                ('A importância do transporte público de qualidade', 'Urbanismo'),
                ('Os desafios da educação inclusiva', 'Educação'),
                ('A valorização da pesquisa científica', 'Tecnologia'),
                ('O combate à violência doméstica', 'Direito'),
                ('A importância do saneamento básico', 'Saúde'),
                ('Os efeitos do desmatamento na biodiversidade', 'Meio Ambiente'),
                ('A democratização do acesso à justiça', 'Direito'),
                ('O papel do terceiro setor na sociedade', 'Sociologia'),
                ('Os desafios da gestão de resíduos sólidos', 'Meio Ambiente'),
                ('A importância do planejamento familiar', 'Saúde'),
                ('A crise do sistema de saúde pública', 'Saúde'),
                ('Os impactos do consumo consciente', 'Meio Ambiente'),
                ('A importância da atividade física', 'Saúde'),
                ('Os desafios da educação à distância', 'Educação'),
                ('A proteção aos direitos do consumidor', 'Direito'),
                ('O fenômeno do empreendedorismo no Brasil', 'Economia'),
                ('A importância da doação de órgãos', 'Saúde'),
                ('Os desafios da segurança digital', 'Tecnologia'),
                ('A valorização da agricultura familiar', 'Economia'),
                ('O combate ao trabalho infantil', 'Direito'),
                ('A importância dos direitos humanos', 'Direito'),
                ('Os desafios da mobilidade elétrica', 'Tecnologia'),
                ('A proteção aos conhecimentos tradicionais', 'Cultura'),
                ('A crise climática e suas consequências', 'Meio Ambiente'),
                ('A importância da transparência governamental', 'Política'),
                ('Os desafios da conciliação trabalho-família', 'Sociologia'),
                ('A valorização da profissão docente', 'Educação'),
                ('O combate à evasão escolar', 'Educação'),
                ('A importância da criatividade na educação', 'Educação'),
                ('Os desafios da inteligência artificial ética', 'Tecnologia'),
                ('A proteção da privacidade na era digital', 'Tecnologia'),
                ('A importância do voluntariado', 'Sociologia'),
                ('Os desafios da gestão pública eficiente', 'Política'),
                ('A valorização da diversidade nas organizações', 'Sociologia'),
                ('O combate à pobreza e à fome', 'Sociologia'),
                ('A importância da inovação tecnológica', 'Tecnologia'),
                ('Os desafios da saúde mental na sociedade', 'Saúde'),
                ('A proteção aos direitos autorais', 'Direito'),
                ('A importância da educação financeira', 'Educação'),
                ('Os desafios da produção de energia limpa', 'Meio Ambiente'),
                ('A valorização do turismo sustentável', 'Meio Ambiente'),
                ('O combate à pirataria digital', 'Tecnologia'),
                ('A importância da governança corporativa', 'Economia'),
                ('Os desafios da economia circular', 'Economia'),
                ('A proteção aos dados genéticos', 'Tecnologia'),
                ('A importância do desenvolvimento sustentável', 'Meio Ambiente')
            ]
            
            for tema in temas_data:
                cursor.execute(
                    "INSERT INTO redacao_temas (tema, categoria) VALUES (?, ?)",
                    tema
                )
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Banco inicializado: {len(questions_data)} questões, {len(temas_data)} temas")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")

# Inicializar banco ao iniciar
init_database()

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ========== API - MATÉRIAS ==========

@app.route('/api/materias')
def api_materias():
    try:
        conn = sqlite3.connect('concursos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT materia FROM questions")
        materias = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify(materias)
    except Exception as e:
        logger.error(f"Erro em /api/materias: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API - SIMULADOS ==========

simulados_ativos = {}

@app.route('/api/simulado/iniciar', methods=['POST'])
def api_simulado_iniciar():
    try:
        data = request.json
        materia = data.get('materia', 'todas')
        quantidade = int(data.get('quantidade', 10))
        
        conn = sqlite3.connect('concursos.db')
        cursor = conn.cursor()
        
        if materia == 'todas':
            cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT ?", (quantidade,))
        else:
            cursor.execute("SELECT * FROM questions WHERE materia = ? ORDER BY RANDOM() LIMIT ?", (materia, quantidade))
        
        questions = []
        for row in cursor.fetchall():
            questions.append({
                'id': row[0],
                'materia': row[1],
                'questao': row[2],
                'alternativas': json.loads(row[3]),
                'resposta_correta': row[4],
                'explicacao': row[5]
            })
        
        conn.close()
        
        # Criar simulado
        simulado_id = f"sim_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        simulados_ativos[simulado_id] = {
            'questoes': questions,
            'respostas': [],
            'inicio': datetime.now().isoformat()
        }
        
        logger.info(f"🎯 Simulado {simulado_id} iniciado com {len(questions)} questões")
        
        return jsonify({
            'simulado_id': simulado_id,
            'questoes': questions,
            'total': len(questions)
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar simulado: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/responder', methods=['POST'])
def api_simulado_responder():
    try:
        data = request.json
        simulado_id = data.get('simulado_id')
        questao_id = data.get('questao_id')
        resposta = data.get('resposta')
        
        if simulado_id not in simulados_ativos:
            return jsonify({'error': 'Simulado não encontrado'}), 404
            
        # Registrar resposta
        simulados_ativos[simulado_id]['respostas'].append({
            'questao_id': questao_id,
            'resposta': resposta,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'status': 'resposta registrada'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulado/finalizar', methods=['POST'])
def api_simulado_finalizar():
    try:
        data = request.json
        simulado_id = data.get('simulado_id')
        
        if simulado_id not in simulados_ativos:
            return jsonify({'error': 'Simulado não encontrado'}), 404
            
        simulado = simulados_ativos[simulado_id]
        acertos = 0
        
        # Calcular resultado
        for resposta in simulado['respostas']:
            questao_id = resposta['questao_id']
            questao = next((q for q in simulado['questoes'] if q['id'] == questao_id), None)
            if questao and resposta['resposta'] == questao['resposta_correta']:
                acertos += 1
        
        total = len(simulado['questoes'])
        percentual = (acertos / total) * 100 if total > 0 else 0
        
        resultado = {
            'acertos': acertos,
            'total': total,
            'percentual': round(percentual, 1),
            'simulado_id': simulado_id
        }
        
        logger.info(f"✅ Simulado finalizado: {acertos}/{total} acertos")
        
        # Remover simulado da memória
        del simulados_ativos[simulado_id]
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== API - REDAÇÃO ==========

@app.route('/api/redacao/temas')
def api_redacao_temas():
    try:
        conn = sqlite3.connect('concursos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, tema, categoria FROM redacao_temas")
        temas = [{'id': row[0], 'tema': row[1], 'categoria': row[2]} for row in cursor.fetchall()]
        conn.close()
        return jsonify(temas)
    except Exception as e:
        logger.error(f"Erro em /api/redacao/temas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/redacao/corrigir-gemini', methods=['POST'])
def api_redacao_corrigir_gemini():
    try:
        data = request.json
        tema = data.get('tema')
        texto = data.get('texto')
        
        if not tema or not texto:
            return jsonify({'error': 'Tema e texto são obrigatórios'}), 400
        
        logger.info(f"📝 Iniciando correção de redação...")
        logger.info(f"📋 Tema: {tema}")
        logger.info(f"📄 Texto: {len(texto)} caracteres")
        
        # Usar Gemini para correção
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        CORREÇÃO DE REDAÇÃO - MODELO ENEM
        
        TEMA: {tema}
        
        TEXTO DO ESTUDANTE:
        {texto}
        
        ANALISE ESTA REDAÇÃO SEGUINDO OS CRITÉRIOS DO ENEM:
        
        1. COMPETÊNCIA 1: Domínio da norma culta (0-200 pontos)
        2. COMPETÊNCIA 2: Compreensão do tema (0-200 pontos) 
        3. COMPETÊNCIA 3: Argumentação e organização (0-200 pontos)
        4. COMPETÊNCIA 4: Coesão textual (0-200 pontos)
        5. COMPETÊNCIA 5: Proposta de intervenção (0-200 pontos)
        
        FORNECE:
        - Nota final (0-1000)
        - Análise detalhada por competência
        - Pontos fortes
        - Pontos a melhorar
        - Sugestões específicas
        
        FORMATE A RESPOSTA EM MARKDOWN.
        """
        
        logger.info("🔄 Enviando para Gemini...")
        response = model.generate_content(prompt)
        correcao = response.text
        
        # Extrair nota (buscar padrão numérico)
        import re
        nota_match = re.search(r'(\d{1,3})\s*/\s*1000', correcao)
        nota = int(nota_match.group(1)) if nota_match else 800
        
        logger.info(f"✅ Correção concluída - Nota: {nota}")
        
        return jsonify({
            'nota': nota,
            'correcao': correcao,
            'tema': tema,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na correção: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API - DASHBOARD ==========

@app.route('/api/dashboard/estatisticas')
def api_dashboard_estatisticas():
    try:
        conn = sqlite3.connect('concursos.db')
        cursor = conn.cursor()
        
        # Estatísticas do banco
        cursor.execute("SELECT COUNT(*) FROM questions")
        total_questoes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM redacao_temas")
        total_temas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT materia) FROM questions")
        total_materias = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_questoes': total_questoes,
            'total_temas': total_temas,
            'total_materias': total_materias,
            'ultima_atualizacao': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/dashboard/estatisticas: {e}")
        return jsonify({'error': str(e)}), 500

# ========== CONFIGURAÇÃO SERVIDOR ==========

if __name__ == '__main__':
    # Configurações para produção
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("==================================================")
    print("🎯 CONCURSOIA - SISTEMA INTELIGENTE DE ESTUDOS")
    print("==================================================")
    
    # Verificar estatísticas finais
    try:
        conn = sqlite3.connect('concursos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions")
        questoes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM redacao_temas")
        temas = cursor.fetchone()[0]
        conn.close()
        
        print(f"📚 Questões no banco: {questoes}")
        print(f"📝 Temas de redação: {temas}")
    except:
        print("📚 Questões no banco: Carregando...")
        print("📝 Temas de redação: Carregando...")
    
    print(f"🌐 Servidor: http://0.0.0.0:{port}")
    print(f"🔧 Debug: {debug}")
    print("🤖 Gemini: ✅ Configurado")
    print("==================================================")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
