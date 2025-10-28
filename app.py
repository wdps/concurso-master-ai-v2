import os
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

# Configuração para produção
PORT = int(os.environ.get('PORT', 5001))
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'chave_secreta_forte_123')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# --- Sistema de Sessão Leve para Simulados ---
simulados_ativos = {}

def get_simulado_atual():
    simulado_id = session.get('simulado_id')
    if simulado_id and simulado_id in simulados_ativos:
        return simulados_ativos[simulado_id]
    return None

def set_simulado_atual(simulado_data):
    simulado_id = simulado_data['simulado_id']
    simulados_ativos[simulado_id] = simulado_data
    session['simulado_id'] = simulado_id
    session.modified = True

def limpar_simulado_atual():
    simulado_id = session.pop('simulado_id', None)
    if simulado_id and simulado_id in simulados_ativos:
        del simulados_ativos[simulado_id]

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

# --- Conexão DB Corrigida (UTF-8) ---
def get_db_connection():
    try:
        conn = sqlite3.connect('concurso.db', check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.text_factory = lambda b: b.decode('utf-8', errors='ignore') 
        return conn
    except Exception as e:
        print(f"❌ ERRO DB: {e}")
        return None

# --- Mapeamento de Disciplinas (Consolidação de Psicologia) ---
def mapear_disciplina(disciplina_original):
    if disciplina_original is None:
        return 'Outras'
    
    disciplina_original = disciplina_original.strip()
    
    if 'Psicologia' in disciplina_original and ('Saúde' in disciplina_original or disciplina_original == 'Psicologia'):
        return 'Psicologia'

    if 'Psicologia' in disciplina_original and 'Gestão' in disciplina_original:
        return 'Gestão de Pessoas'
        
    return disciplina_original

# --- Função para limpar temas de redação ---
def limpar_tema_redacao(titulo):
    if titulo is None:
        return "Tema sem título"
    
    if isinstance(titulo, bytes):
        titulo = titulo.decode('utf-8', errors='ignore')
    
    titulo = titulo.split('(')[0].strip()
    
    return titulo

# --- Rotas Principais ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    limpar_simulado_atual()
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

# --- API: Simulado com Sistema de Sessão Leve ---
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
        
        disciplinas_data = {}
        for row in materias_db:
            
            disc_original = row['disciplina']
            disc_mapeada = mapear_disciplina(disc_original)
            
            if disc_mapeada not in disciplinas_data:
                disciplinas_data[disc_mapeada] = {
                    'total_questoes': 0,
                    'materias': []
                }
            
            disciplinas_data[disc_mapeada]['materias'].append({
                'nome': row['materia'],
                'questoes': row['total_questoes']
            })
            disciplinas_data[disc_mapeada]['total_questoes'] += row['total_questoes']
        
        materias_agrupadas = [{
            'disciplina': disc,
            'total_questoes': data['total_questoes'],
            'materias': data['materias']
        } for disc, data in disciplinas_data.items()]

        conn.close()
        
        return jsonify({'success': True, 'disciplinas': materias_agrupadas})
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO /api/materias (DB): {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    conn = None
    print("\n🎯 Iniciando simulado...")
    
    try:
        data = request.get_json()
        
        materias = data.get('materias', []) 
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
        
        questoes_db = conn.execute(query, params).fetchall()
        
        if not questoes_db:
            conn.close()
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada nas matérias selecionadas'}), 404

        simulado_id = f"sim_{int(time.time())}_{random.randint(1000, 9999)}"
        
        if 'user_id' not in session:
            session['user_id'] = f"user_{random.randint(10000, 99999)}"

        simulado_data = {
            'simulado_id': simulado_id,
            'questoes': [],
            'respostas': {},
            'indice_atual': 0,
            'data_inicio': datetime.now().isoformat(),
            'config': { 
                'materias': materias,
                'quantidade': quantidade
            }
        }

        for questao_db in questoes_db:
            questao_dict = dict(questao_db)
            questao_dict['disciplina'] = mapear_disciplina(questao_dict['disciplina'])
            questao_dict['alternativas'] = json.loads(questao_dict['alternativas'])
            simulado_data['questoes'].append(questao_dict)

        set_simulado_atual(simulado_data)

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
        simulado = get_simulado_atual()
        if not simulado:
            return jsonify({'success': False, 'error': 'Nenhum simulado ativo'}), 400

        questoes = simulado['questoes'] 
        
        if indice < 0 or indice >= len(questoes):
            return jsonify({'success': False, 'error': 'Índice inválido'}), 400

        simulado['indice_atual'] = indice
        set_simulado_atual(simulado)

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
        simulado = get_simulado_atual()
        if not simulado:
            return jsonify({'success': False, 'error': 'Nenhum simulado ativo'}), 400

        data = request.get_json()
        questao_id = data.get('questao_id')
        alternativa = data.get('alternativa', '').strip().upper()

        if not questao_id or not alternativa:
            return jsonify({'success': False, 'error': 'Dados incompletos'}), 400
        
        if str(questao_id) in simulado['respostas']:
             return jsonify({'success': False, 'error': 'Questão já foi respondida.'}), 400
        
        questao_atual = None
        for q in simulado['questoes']:
            if str(q['id']) == str(questao_id):
                questao_atual = q
                break

        if not questao_atual:
            return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404

        resposta_correta = questao_atual['resposta_correta'].strip().upper()
        acertou = (alternativa == resposta_correta)

        simulado['respostas'][str(questao_id)] = {
            'alternativa_escolhida': alternativa,
            'acertou': acertou,
            'timestamp': datetime.now().isoformat()
        }
        
        set_simulado_atual(simulado)

        # CORREÇÃO: Justificativa apenas quando erra
        resposta_data = {
            'success': True,
            'acertou': acertou,
            'resposta_correta': resposta_correta
        }
        
        if not acertou:
            resposta_data['justificativa'] = questao_atual.get('justificativa', 'Sem justificativa disponível.')

        return jsonify(resposta_data)

    except Exception as e:
        print(f"❌ ERRO CRÍTICO /simulado/responder: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/finalizar', methods=['POST'])
def finalizar_simulado():
    conn = None
    try:
        simulado = get_simulado_atual()
        if not simulado:
            return jsonify({'success': False, 'error': 'Nenhum simulado ativo para finalizar'}), 400
        
        total_questoes = len(simulado['questoes'])
        total_respondidas = len(simulado['respostas'])
        total_acertos = sum(1 for r in simulado['respostas'].values() if r['acertou'])
        
        percentual_acerto = (total_acertos / total_questoes) * 100 if total_questoes > 0 else 0
        
        total_peso = sum(q.get('peso', 1) for q in simulado['questoes'])
        peso_acumulado = 0
        
        for questao in simulado['questoes']:
            questao_id = str(questao['id'])
            if questao_id in simulado['respostas'] and simulado['respostas'][questao_id]['acertou']:
                peso_acumulado += questao.get('peso', 1)
        
        nota_final = (peso_acumulado / total_peso) * 100 if total_peso > 0 else 0

        relatorio = {
            'simulado_id': simulado['simulado_id'],
            'total_questoes': total_questoes,
            'total_respondidas': total_respondidas,
            'total_acertos': total_acertos,
            'percentual_acerto': round(percentual_acerto, 2),
            'nota_final': round(nota_final, 2),
            'data_fim': datetime.now().isoformat()
        }
        
        config_db = simulado.get('config', {'materias': [], 'quantidade': 0})
        
        try:
            conn = get_db_connection()
            if conn:
                conn.execute('''
                    INSERT INTO historico_simulados 
                    (user_id, simulado_id, respostas, relatorio, config, data_fim)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session.get('user_id', 'anon'),
                    simulado['simulado_id'],
                    json.dumps(simulado['respostas']),
                    json.dumps(relatorio),
                    json.dumps(config_db),
                    relatorio['data_fim']
                ))
                conn.commit()
                conn.close()
        except Exception as db_error:
            print(f"⚠️ Erro ao salvar histórico: {db_error}")

        limpar_simulado_atual()
        
        print(f"✅ Simulado finalizado: {total_acertos}/{total_questoes} acertos")
        
        return jsonify({
            'success': True,
            'relatorio': relatorio
        })

    except Exception as e:
        print(f"❌ ERRO /simulado/finalizar: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- API Redação Aprimorada ---
@app.route('/api/redacao/temas')
def get_temas_redacao():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Erro de conexão com o banco'}), 500

        temas_db = conn.execute("SELECT titulo FROM temas_redacao ORDER BY titulo").fetchall()
        temas = [{'titulo': row['titulo']} for row in temas_db]
        
        final_temas = []
        for tema in temas:
            titulo_limpo = limpar_tema_redacao(tema['titulo'])
            final_temas.append({'titulo': titulo_limpo})
        
        conn.close()
        return jsonify({'success': True, 'temas': final_temas})
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
        print(f"📄 Texto: {len(texto_redacao)} caracteres")

        model = genai.GenerativeModel(MODEL_NAME)

        prompt = f"""
        CORRIJA ESTA DISSERTAÇÃO PARA CONCURSOS PÚBLICOS COM BASE NO TEMA: "{tema_titulo}"

        TEXTO DO CANDIDATO:
        {texto_redacao}

        CRITÉRIOS DE CORREÇÃO PARA CONCURSOS:
        1. ESTRUTURA DISSERTATIVA (0-20 pontos)
           - Introdução com tese clara
           - Desenvolvimento com 2-3 argumentos sólidos
           - Conclusão com proposta de intervenção

        2. COERÊNCIA E COESÃO (0-20 pontos)
           - Progressão temática
           - Uso adequado de conectivos
           - Parágrafos bem construídos

        3. ARGUMENTAÇÃO (0-20 pontos)
           - Qualidade dos argumentos
           - Fundamentação consistente
           - Dados e exemplos relevantes

        4. NORMA CULTA (0-20 pontos)
           - Gramática correta
           - Pontuação adequada
           - Vocabulário apropriado

        5. PROPOSTA DE INTERVENÇÃO (0-20 pontos)
           - Viabilidade da proposta
           - Clareza e detalhamento
           - Respeito aos direitos humanos

        RETORNE APENAS JSON com esta estrutura:
        {{
            "nota_final": 0-100,
            "analise_competencias": [
                {{"competencia": "Estrutura dissertativa", "nota": 0-20, "comentario": "Análise detalhada..."}},
                {{"competencia": "Coerência e coesão", "nota": 0-20, "comentario": "Análise detalhada..."}},
                {{"competencia": "Argumentação", "nota": 0-20, "comentario": "Análise detalhada..."}},
                {{"competencia": "Norma culta", "nota": 0-20, "comentario": "Análise detalhada..."}},
                {{"competencia": "Proposta de intervenção", "nota": 0-20, "comentario": "Análise detalhada..."}}
            ],
            "pontos_fortes": ["lista", "de", "pontos", "fortes", "específicos"],
            "pontos_fracos": ["lista", "de", "pontos", "a", "melhorar", "específicos"],
            "sugestoes_melhoria": ["sugestões", "concretas", "e", "específicas"],
            "dicas_concursos": ["dicas", "práticas", "para", "concursos", "públicos"]
        }}

        Seja rigoroso na correção, como em um concurso público real.
        """

        print("🔄 Enviando para Gemini...")
        response = model.generate_content(prompt)
        print("✅ Resposta recebida")

        raw_text = response.text.strip()
        
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        correcao_data = json.loads(raw_text)
        
        nota_calculada = sum(comp['nota'] for comp in correcao_data['analise_competencias'])
        correcao_data['nota_final'] = nota_calculada

        print(f"✅ Correção concluída - Nota: {nota_calculada}")
        return jsonify({'success': True, 'correcao': correcao_data})

    except Exception as e:
        print(f"❌ ERRO na correção: {e}")
        return jsonify({'success': False, 'error': f'Erro: {str(e)}'}), 500

@app.route('/api/dashboard/estatisticas')
def get_estatisticas():
    conn = None
    try:
        user_id = session.get('user_id', 'anon')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Erro de conexão com o banco'}), 500

        # Buscar estatísticas completas
        historico_db = conn.execute(
            "SELECT relatorio, data_fim FROM historico_simulados WHERE user_id = ? ORDER BY data_fim DESC",
            (user_id,)
        ).fetchall()

        if not historico_db:
            return jsonify({
                'success': True,
                'total_simulados': 0,
                'total_questoes_respondidas': 0,
                'total_acertos': 0,
                'media_geral': 0,
                'evolucao': [],
                'melhor_materia': 'N/A',
                'pior_materia': 'N/A',
                'historico_recente': []
            })

        historico = [json.loads(row['relatorio']) for row in historico_db]
        
        total_simulados = len(historico)
        total_questoes_respondidas = sum(h.get('total_respondidas', 0) for h in historico)
        total_acertos = sum(h.get('total_acertos', 0) for h in historico)
        media_geral = sum(h.get('nota_final', 0) for h in historico) / total_simulados
        
        # Evolução (últimos 5 simulados)
        evolucao = historico[:5]
        
        # Melhor e pior desempenho (simplificado)
        melhor_simulado = max(historico, key=lambda x: x.get('nota_final', 0))
        pior_simulado = min(historico, key=lambda x: x.get('nota_final', 0))

        return jsonify({
            'success': True,
            'total_simulados': total_simulados,
            'total_questoes_respondidas': total_questoes_respondidas,
            'total_acertos': total_acertos,
            'media_geral': round(media_geral, 2),
            'melhor_desempenho': melhor_simulado.get('nota_final', 0),
            'pior_desempenho': pior_simulado.get('nota_final', 0),
            'evolucao': evolucao,
            'historico_recente': historico[:10]
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
    print("🎯 CONCURSOIA - SISTEMA INTELIGENTE DE ESTUDOS")
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
        print(f"⚠️ Erro no banco: {e}")

    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Servidor: http://localhost:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"🤖 Gemini: {'✅ Configurado' if gemini_configured else '❌ Não configurado'}")
    print("="*50)
    
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)




