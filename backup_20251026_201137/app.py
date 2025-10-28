from flask import Flask, render_template, request, jsonify, session, send_from_directory
import sqlite3
import json
import random
import time
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import traceback

# --- Configuração Inicial ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'chave_secreta_forte_123')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

# --- Configuração da API Gemini ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "models/gemini-2.0-flash"

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY não encontrada")
    gemini_configured = False
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print(f"✅ Gemini configurado: {MODEL_NAME}")
        gemini_configured = True
    except Exception as e:
        print(f"❌ Erro no Gemini: {e}")
        gemini_configured = False

# --- Dicionário de Áreas (Simplificação do Simulado) ---
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
}

def get_area(materia):
    """Retorna a Área de Conhecimento para dada Matéria."""
    materia_lower = materia.lower()
    for mat, area in AREAS_CONHECIMENTO.items():
        if mat.lower() in materia_lower:
            return area
    return "Outras Matérias"

# --- Funções Auxiliares de Enconding ---
def corrigir_encoding(texto):
    """Corrige problemas comuns de encoding, garantindo estabilidade."""
    if not isinstance(texto, str):
        return texto
    
    correcoes = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã£': 'ã', 'Ãµ': 'õ', 'Ã¢': 'â', 'Ãª': 'ê', 'Ã§': 'ç',
        'Âº': 'º', 'Ã\xad': 'í', 'Ã‰': 'É', 'ÃŠ': 'Ê', 'Ã‘': 'Ñ'
    }
    
    for erro, correcao in correcoes.items():
        texto = texto.replace(erro, correcao)
        
    return texto

# --- Conexão DB ---
def get_db_connection():
    try:
        conn = sqlite3.connect('concurso.db', check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ ERRO DB: {e}")
        return None

# --- Rotas Principais ---
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

# --- API: Matérias (Simplificação) ---
@app.route('/api/materias')
def api_materias():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Erro de conexão com o banco'}), 500

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
            
        conn.close()
        
        areas_focadas = list(set(AREAS_CONHECIMENTO.values()))
        materias_finais = {
            area: dados for area, dados in materias_por_area.items() 
            if area in areas_focadas
        }

        return jsonify({'success': True, 'areas': materias_finais})
        
    except Exception as e:
        print(f"❌ ERRO /api/materias: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- API: Simulado ROBUSTA ---
@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    conn = None
    print("\n🎯 Iniciando simulado...")
    
    try:
        data = request.get_json()
        materias = data.get('materias', []) # Lista de matérias (chaves)
        quantidade = int(data.get('quantidade', 10))

        if not materias:
            return jsonify({'success': False, 'error': 'Selecione pelo menos uma matéria'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Erro de conexão com o banco'}), 500

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
        print(f"🔍 Buscando {quantidade} questões nas matérias: {materias}")
        
        questoes_db = conn.execute(query, params).fetchall()
        
        if not questoes_db:
            conn.close()
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 404

        # Preparar simulado
        simulado_id = f"sim_{int(time.time())}_{random.randint(1000, 9999)}"
        
        if 'user_id' not in session:
            session['user_id'] = f"user_{random.randint(10000, 99999)}"

        simulado_data = {
            'simulado_id': simulado_id,
            'questoes': [],
            'respostas': {},
            'indice_atual': 0,
            'data_inicio': datetime.now().isoformat()
        }

        # Processar questões
        for questao_db in questoes_db:
            questao_dict = dict(questao_db)
            for key in ['disciplina', 'materia', 'enunciado', 'justificativa', 'dica', 'formula', 'resposta_correta']:
                if questao_dict.get(key) is not None:
                    questao_dict[key] = corrigir_encoding(questao_dict[key])
            
            if isinstance(questao_dict.get('alternativas'), str):
                questao_dict['alternativas'] = json.loads(questao_dict['alternativas'])
            
            if questao_dict.get('peso') is None:
                dificuldade = questao_dict.get('dificuldade', 'Baixa').lower()
                peso = 1
                if 'média' in dificuldade: peso = 2
                elif 'alta' in dificuldade: peso = 3
                questao_dict['peso'] = peso
            
            simulado_data['questoes'].append(questao_dict)

        session['simulado_atual'] = simulado_data
        session.modified = True

        # Primeira questão (Versão estável com .get())
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

        conn.close()
        
        print(f"✅ Simulado {simulado_id} iniciado com {len(questoes_db)} questões")
        return jsonify({
            'success': True, 
            'total_questoes': len(questoes_db),
            'questao': questao_frontend,
            'indice_atual': 0
        })

    except Exception as e:
        print(f"❌ ERRO CRÍTICO /simulado/iniciar: {e}")
        print(traceback.format_exc())
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': f'Erro interno do servidor: {str(e)}'}), 500

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
        questao_id = str(questao['id'])
        
        resposta_anterior = simulado['respostas'].get(questao_id)
        
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
        print(f"❌ ERRO /simulado/questao: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    try:
        if 'simulado_atual' not in session:
            return jsonify({'success': False, 'error': 'Nenhum simulado ativo'}), 400

        data = request.get_json()
        questao_id = data.get('questao_id')
        alternativa = data.get('alternativa', '').strip().upper()

        if not questao_id:
            print("❌ BAD REQUEST: ID da questão não fornecido.")
            return jsonify({'success': False, 'error': 'ID da questão não fornecido (possível bug de carregamento).'}), 400
        if not alternativa:
            print("❌ BAD REQUEST: Alternativa não selecionada.")
            return jsonify({'success': False, 'error': 'Alternativa não selecionada.'}), 400

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
            'dicas_interpretacao': dicas_interpretacao # Envia a dica de interpretação
        })

    except Exception as e:
        print(f"❌ ERRO /simulado/responder: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
            'data_fim': datetime.now().isoformat()
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
                conn.close()
        except Exception as db_error:
            print(f"⚠️  Erro ao salvar histórico: {db_error}")

        # Limpar simulado
        session.pop('simulado_atual', None)
        
        print(f"✅ Simulado finalizado. Nota: {nota_final:.2f}%")
        
        return jsonify({
            'success': True,
            'relatorio': relatorio
        })

    except Exception as e:
        print(f"❌ ERRO /simulado/finalizar: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- API: Redação para Concursos (Correção de Encoding) ---
@app.route('/api/redacao/temas')
def get_temas_redacao():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Erro de conexão com o banco'}), 500

        temas_db = conn.execute("SELECT * FROM temas_redacao ORDER BY titulo").fetchall()
        temas = []
        for row in temas_db:
            tema_dict = dict(row)
            tema_dict['titulo'] = corrigir_encoding(tema_dict['titulo'])
            tema_dict['descricao'] = corrigir_encoding(tema_dict.get('descricao', ''))
            # Remove a dificuldade, conforme solicitado
            temas.append(tema_dict)

        conn.close()
        return jsonify({'success': True, 'temas': temas})
    except Exception as e:
        print(f"❌ ERRO /api/redacao/temas: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/redacao/corrigir-gemini', methods=['POST'])
def corrigir_redacao_gemini():
    print("\n📝 Iniciando correção de redação...")

    if not gemini_configured:
        return jsonify({'success': False, 'error': 'API Gemini não configurada'}), 500

    try:
        data = request.get_json()
        texto_redacao = data.get('texto', '').strip()
        tema_titulo = data.get('tema', '').strip()

        if not texto_redacao:
            return jsonify({'success': False, 'error': 'Texto da redação não fornecido'}), 400
        if not tema_titulo:
            return jsonify({'success': False, 'error': 'Tema não fornecido'}), 400

        print(f"📋 Tema: {tema_titulo}")

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

        print("🔄 Enviando para Gemini...")
        response = model.generate_content(prompt)
        print("✅ Resposta recebida")

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
        correcao_data['nota_final'] = nota_calculada

        print(f"✅ Correção concluída - Nota: {nota_calculada}")
        return jsonify({'success': True, 'correcao': correcao_data})

    except Exception as e:
        print(f"❌ ERRO na correção: {e}")
        return jsonify({'success': False, 'error': f'Erro: {str(e)}'}), 500

# --- API: Dashboard ---
@app.route('/api/dashboard/estatisticas')
def get_estatisticas():
    conn = None
    try:
        user_id = session.get('user_id', 'anon')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Erro de conexão com o banco'}), 500

        historico_db = conn.execute(
            "SELECT relatorio FROM historico_simulados WHERE user_id = ? ORDER BY data_fim DESC",
            (user_id,)
        ).fetchall()

        if not historico_db:
            return jsonify({
                'success': True,
                'total_simulados': 0,
                'total_questoes_respondidas': 0,
                'media_geral': 0,
                'media_acertos': 0,
                'historico_recente': []
            })

        historico = [json.loads(row['relatorio']) for row in historico_db]
        
        total_simulados = len(historico)
        total_questoes_respondidas = sum(h.get('total_respondidas', 0) for h in historico)
        media_geral = sum(h.get('nota_final', 0) for h in historico) / total_simulados
        media_acertos = sum(h.get('percentual_acerto_simples', 0) for h in historico) / total_simulados

        return jsonify({
            'success': True,
            'total_simulados': total_simulados,
            'total_questoes_respondidas': total_questoes_respondidas,
            'media_geral': round(media_geral, 2), # Média por peso
            'media_acertos': round(media_acertos, 2), # Média simples
            'historico_recente': historico[:5]
        })

    except Exception as e:
        print(f"❌ ERRO /api/dashboard/estatisticas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# --- Inicialização ---
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🎯 SISTEMA ESQUEMATIZA.AI")
    print("="*50)
    
    try:
        conn = get_db_connection()
        if conn:
            count_questoes = conn.execute("SELECT COUNT(*) FROM questoes").fetchone()[0]
            count_temas = conn.execute("SELECT COUNT(*) FROM temas_redacao").fetchone()[0]
            print(f"📚 Questões no banco: {count_questoes}")
            print(f"📝 Temas de redação: {count_temas}")
            conn.close()
    except Exception as e:
        print(f"⚠️  Erro no banco: {e}")

    port = int(os.environ.get('PORT', 5001)) # Definido para 5001 por segurança
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Servidor: http://127.0.0.1:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"🤖 Gemini: {'✅ Configurado' if gemini_configured else '❌ Não configurado'}")
    print("="*50)
    
    app.run(debug=debug, host='0.0.0.0', port=port)
