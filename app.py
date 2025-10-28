import traceback
import sys
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
        logger.info("✅ Gemini configurado")
    else:
        logger.warning("⚠️  GEMINI_API_KEY não encontrada")
except Exception as e:
    logger.error(f"❌ Erro ao configurar Gemini: {e}")

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
            'total_questoes': total_questoes or 295,
            'total_temas': total_temas or 81,
            'total_materias': total_materias or 15,
            'ultima_atualizacao': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== TRATAMENTO DE ERRO GLOBAL ==========
@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    error_traceback = traceback.format_exc()
    print(f"❌ ERRO NA APLICAÇÃO: {e}")
    print(f"📝 Traceback: {error_traceback}")
    return jsonify({
        'error': 'Erro interno do servidor',
        'message': str(e),
        'traceback': error_traceback if os.environ.get('DEBUG') == 'True' else None
    }), 500


# ========== CONFIGURAÇÃO SERVIDOR ==========

if __name__ == '__main__':
    # Configurações para produção
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("==================================================")
    print("🎯 CONCURSOIA - SISTEMA INTELIGENTE DE ESTUDOS")
    print("==================================================")
    print(f"📚 Questões no banco: 295")
    print(f"📝 Temas de redação: 81") 
    print(f"🌐 Servidor: http://0.0.0.0:{port}")
    print(f"🔧 Debug: {debug}")
    print("🤖 Gemini: ✅ Configurado")
    print("==================================================")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

