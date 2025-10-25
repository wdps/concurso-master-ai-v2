from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import os
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'concurso_master_funcional_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Configuração do banco
DATABASE = 'concurso.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    '''Inicializa o banco de dados de forma SIMPLES'''
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar tabela de questões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT,
                materia TEXT,
                alternativas TEXT,
                resposta_correta TEXT,
                explicacao TEXT
            )
        ''')
        
        # Verificar se já existem questões
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print('📥 Carregando questões do CSV...')
            load_questions()
        else:
            print(f'✅ {count} questões no banco')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Erro no banco: {e}')
        return False

def load_questions():
    '''Carrega questões do CSV - VERSÃO SIMPLES E FUNCIONAL'''
    if not os.path.exists('questoes.csv'):
        print('❌ Arquivo questoes.csv não encontrado')
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            questions_loaded = 0
            
            for row in csv_reader:
                try:
                    enunciado = row.get('enunciado', '').strip()
                    materia = row.get('disciplina', 'Geral').strip()
                    
                    if not enunciado:
                        continue
                    
                    # Alternativas básicas
                    alternativas = {
                        'A': row.get('alt_a', 'Alternativa A').strip(),
                        'B': row.get('alt_b', 'Alternativa B').strip(),
                        'C': row.get('alt_c', 'Alternativa C').strip(),
                        'D': row.get('alt_d', 'Alternativa D').strip()
                    }
                    
                    resposta_correta = row.get('gabarito', 'A').strip().upper()
                    explicacao = f"Resposta correta: {resposta_correta}"
                    
                    # Inserir questão
                    cursor.execute('''
                        INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (enunciado, materia, json.dumps(alternativas), resposta_correta, explicacao))
                    
                    questions_loaded += 1
                    
                except Exception as e:
                    continue
        
        conn.commit()
        conn.close()
        print(f'✅ {questions_loaded} questões carregadas')
        return True
        
    except Exception as e:
        print(f'❌ Erro ao carregar CSV: {e}')
        return False

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def index():
    '''Página inicial SIMPLES'''
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ConcursoMaster</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                color: white;
            }
            .container {
                text-align: center;
                background: rgba(255,255,255,0.1);
                padding: 50px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 20px;
            }
            .btn {
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 15px 30px;
                margin: 10px;
                border-radius: 10px;
                text-decoration: none;
                font-size: 1.2rem;
                font-weight: bold;
                transition: all 0.3s;
            }
            .btn:hover {
                background: #2980b9;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 ConcursoMaster</h1>
            <p style="font-size: 1.3rem; margin-bottom: 30px;">Sistema de Simulados para Concursos</p>
            <a href="/simulado" class="btn">🚀 Iniciar Simulado</a>
        </div>
    </body>
    </html>
    '''

@app.route('/simulado')
def simulado():
    '''Página de configuração do simulado - SIMPLES'''
    try:
        init_database()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT materia FROM questoes WHERE materia IS NOT NULL')
        materias_db = cursor.fetchall()
        conn.close()
        
        materias = [row['materia'] for row in materias_db]
        
        # Gerar HTML das matérias
        materias_html = ''
        for materia in materias:
            materias_html += f'''
            <div class="materia-item">
                <label>
                    <input type="checkbox" name="materias" value="{materia}" checked>
                    {materia}
                </label>
            </div>
            '''
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Simulado - ConcursoMaster</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    max-width: 500px;
                    width: 100%;
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .form-group {{
                    margin-bottom: 25px;
                }}
                label {{
                    display: block;
                    margin-bottom: 8px;
                    font-weight: bold;
                    color: #34495e;
                }}
                input[type="number"] {{
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    font-size: 16px;
                }}
                .materias {{
                    max-height: 200px;
                    overflow-y: auto;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    padding: 15px;
                }}
                .materia-item {{
                    margin-bottom: 10px;
                }}
                .materia-item label {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-weight: normal;
                    cursor: pointer;
                }}
                .buttons {{
                    display: flex;
                    gap: 15px;
                    margin-top: 30px;
                }}
                .btn {{
                    flex: 1;
                    padding: 15px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s;
                }}
                .btn-primary {{
                    background: #3498db;
                    color: white;
                }}
                .btn-primary:hover {{
                    background: #2980b9;
                }}
                .btn-secondary {{
                    background: #95a5a6;
                    color: white;
                }}
                .btn-secondary:hover {{
                    background: #7f8c8d;
                }}
                .alert {{
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                    display: none;
                }}
                .alert-error {{
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                .alert-success {{
                    background: #d1ecf1;
                    color: #0c5460;
                    border: 1px solid #bee5eb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Configurar Simulado</h1>
                
                <div id="alert" class="alert"></div>
                
                <form id="simuladoForm">
                    <div class="form-group">
                        <label for="quantidade">Quantidade de Questões:</label>
                        <input type="number" id="quantidade" min="1" max="50" value="10" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Matérias:</label>
                        <div class="materias">
                            {materias_html}
                        </div>
                    </div>
                    
                    <div class="buttons">
                        <button type="button" class="btn btn-secondary" onclick="window.location.href='/'">
                            ↩️ Voltar
                        </button>
                        <button type="submit" class="btn btn-primary" id="btnIniciar">
                            🚀 Iniciar Simulado
                        </button>
                    </div>
                </form>
            </div>

            <script>
                document.getElementById('simuladoForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const quantidade = parseInt(document.getElementById('quantidade').value);
                    const materiasCheckboxes = document.querySelectorAll('input[name="materias"]:checked');
                    const materias = Array.from(materiasCheckboxes).map(cb => cb.value);
                    
                    // Validações
                    if (materias.length === 0) {{
                        mostrarAlerta('❌ Selecione pelo menos uma matéria', 'error');
                        return;
                    }}
                    
                    if (!quantidade || quantidade < 1 || quantidade > 50) {{
                        mostrarAlerta('❌ Quantidade deve ser entre 1 e 50', 'error');
                        return;
                    }}
                    
                    const btnIniciar = document.getElementById('btnIniciar');
                    btnIniciar.disabled = true;
                    btnIniciar.textContent = '🔄 Iniciando...';
                    
                    try {{
                        const response = await fetch('/api/simulado/iniciar', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                quantidade: quantidade,
                                materias: materias
                            }})
                        }});
                        
                        const data = await response.json();
                        
                        if (data.success) {{
                            mostrarAlerta('✅ Simulado iniciado! Redirecionando...', 'success');
                            setTimeout(() => {{
                                window.location.href = '/questao/1';
                            }}, 1000);
                        }} else {{
                            throw new Error(data.error || 'Erro desconhecido');
                        }}
                        
                    }} catch (error) {{
                        mostrarAlerta('❌ Erro: ' + error.message, 'error');
                    }} finally {{
                        btnIniciar.disabled = false;
                        btnIniciar.textContent = '🚀 Iniciar Simulado';
                    }}
                }});
                
                function mostrarAlerta(mensagem, tipo) {{
                    const alert = document.getElementById('alert');
                    alert.textContent = mensagem;
                    alert.className = 'alert alert-' + tipo;
                    alert.style.display = 'block';
                    
                    setTimeout(() => {{
                        alert.style.display = 'none';
                    }}, 5000);
                }}
            </script>
        </body>
        </html>
        '''
        
    except Exception as e:
        print(f'❌ Erro no simulado: {e}')
        return '<h1>Erro ao carregar simulado</h1><a href="/">Voltar</a>'

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    '''API para iniciar simulado - SIMPLES E FUNCIONAL'''
    try:
        data = request.get_json()
        quantidade = int(data.get('quantidade', 10))
        materias = data.get('materias', [])
        
        print(f'🚀 Iniciando simulado: {quantidade} questões, {len(materias)} matérias')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar questões
        if not materias:
            cursor.execute('SELECT id FROM questoes ORDER BY RANDOM() LIMIT ?', (quantidade,))
        else:
            placeholders = ','.join(['?'] * len(materias))
            query = f'SELECT id FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
            cursor.execute(query, materias + [quantidade])
        
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        if not questao_ids:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 404
        
        # Configurar sessão
        session.clear()
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        
        print(f'✅ Simulado com {len(questao_ids)} questões iniciado!')
        
        return jsonify({
            'success': True,
            'total': len(questao_ids)
        })
        
    except Exception as e:
        print(f'❌ Erro ao iniciar simulado: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/questao/<int:numero>')
def questao(numero):
    '''Página da questão - SIMPLES E FUNCIONAL'''
    if not session.get('simulado_ativo'):
        return '<h2>Simulado não iniciado</h2><a href="/simulado">Iniciar simulado</a>'
    
    questao_ids = session.get('questoes_ids', [])
    total_questoes = len(questao_ids)
    
    if numero < 1 or numero > total_questoes:
        return '<h2>Questão não encontrada</h2><a href="/simulado">Voltar</a>'
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_ids[numero-1],))
        questao_db = cursor.fetchone()
        conn.close()
        
        if not questao_db:
            return '<h2>Questão não encontrada</h2><a href="/simulado">Voltar</a>'
        
        # Processar questão
        alternativas = json.loads(questao_db['alternativas'])
        resposta_usuario = session.get('respostas', {}).get(str(numero))
        
        # Gerar HTML das alternativas
        alternativas_html = ''
        for letra, texto in alternativas.items():
            alternativas_html += f'''
            <div class="alternativa" onclick="selecionarAlternativa('{letra}')" id="alt{letra}">
                <strong>{letra}.</strong> {texto}
            </div>
            '''
        
        # Gerar feedback se respondida
        feedback_html = ''
        if resposta_usuario:
            correta = resposta_usuario == questao_db['resposta_correta']
            classe_feedback = 'correct' if correta else 'incorrect'
            mensagem_feedback = '✅ Resposta Correta!' if correta else '❌ Resposta Incorreta'
            resposta_correta_html = f'<p><strong>Resposta correta:</strong> {questao_db["resposta_correta"]}</p>' if not correta else ''
            
            feedback_html = f'''
            <div class="feedback {classe_feedback}">
                <h3>{mensagem_feedback}</h3>
                <p><strong>Sua resposta:</strong> {resposta_usuario}</p>
                {resposta_correta_html}
                <p><strong>Explicação:</strong> {questao_db['explicacao']}</p>
            </div>
            '''
        
        # Gerar botões de navegação
        botao_anterior = '<a href="/simulado" class="btn btn-secondary">↩️ Voltar</a>'
        if numero > 1:
            botao_anterior = f'<a href="/questao/{numero-1}" class="btn btn-secondary">⬅️ Anterior</a>'
        
        botao_proximo = ''
        if not resposta_usuario:
            botao_proximo = f'<button class="btn btn-primary" onclick="verificarResposta()" id="btnVerificar">✅ Verificar Resposta</button>'
        else:
            if numero < total_questoes:
                botao_proximo = f'<a href="/questao/{numero+1}" class="btn btn-primary">Próxima ➡️</a>'
            else:
                botao_proximo = '<a href="/resultado" class="btn btn-primary">🏁 Finalizar</a>'
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Questão {numero} - ConcursoMaster</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f6fa;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .alternativa {{
                    padding: 15px;
                    margin: 10px 0;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s;
                }}
                .alternativa:hover {{
                    border-color: #3498db;
                }}
                .selected {{
                    border-color: #3498db;
                    background: #e3f2fd;
                }}
                .btn {{
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 16px;
                    margin: 5px;
                }}
                .btn-primary {{
                    background: #3498db;
                    color: white;
                }}
                .btn-secondary {{
                    background: #95a5a6;
                    color: white;
                }}
                .feedback {{
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 8px;
                }}
                .correct {{
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                }}
                .incorrect {{
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Questão {numero} de {total_questoes}</h1>
                    <p><strong>Matéria:</strong> {questao_db['materia']}</p>
                </div>
                
                <div class="enunciado">
                    <p style="font-size: 1.1rem; line-height: 1.6;">{questao_db['enunciado']}</p>
                </div>
                
                <div id="alternativas">
                    {alternativas_html}
                </div>
                
                {feedback_html}
                
                <div style="display: flex; justify-content: space-between; margin-top: 30px;">
                    <div>
                        {botao_anterior}
                    </div>
                    
                    <div>
                        {botao_proximo}
                    </div>
                </div>
            </div>

            <script>
                let respostaSelecionada = null;
                
                function selecionarAlternativa(letra) {{
                    // Remover seleção anterior
                    document.querySelectorAll('.alternativa').forEach(alt => {{
                        alt.classList.remove('selected');
                    }});
                    
                    // Selecionar nova
                    document.getElementById('alt' + letra).classList.add('selected');
                    respostaSelecionada = letra;
                }}
                
                function verificarResposta() {{
                    if (!respostaSelecionada) {{
                        alert('Por favor, selecione uma alternativa');
                        return;
                    }}
                    
                    fetch('/api/questao/responder', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            questao_numero: {numero},
                            resposta: respostaSelecionada
                        }})
                    }}).then(() => {{
                        window.location.reload();
                    }});
                }}
                
                // Carregar resposta anterior se existir
                {"selecionarAlternativa('" + resposta_usuario + "');" if resposta_usuario else ""}
            </script>
        </body>
        </html>
        '''
        
    except Exception as e:
        print(f'❌ Erro na questão: {e}')
        return '<h2>Erro ao carregar questão</h2><a href="/simulado">Voltar</a>'

@app.route('/api/questao/responder', methods=['POST'])
def responder_questao():
    '''API para responder questão - SIMPLES'''
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'success': False}), 400
        
        data = request.get_json()
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        if not questao_numero or not resposta:
            return jsonify({'success': False}), 400
        
        # Salvar resposta
        if 'respostas' not in session:
            session['respostas'] = {}
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f'❌ Erro ao responder: {e}')
        return jsonify({'success': False}), 500

@app.route('/resultado')
def resultado():
    '''Página de resultado - SIMPLES'''
    if not session.get('simulado_ativo'):
        return '<h2>Nenhum simulado em andamento</h2><a href="/simulado">Iniciar simulado</a>'
    
    try:
        questao_ids = session.get('questoes_ids', [])
        respostas = session.get('respostas', {})
        
        acertos = 0
        for i, questao_id in enumerate(questao_ids, 1):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT resposta_correta FROM questoes WHERE id = ?', (questao_id,))
            questao = cursor.fetchone()
            conn.close()
            
            if questao and respostas.get(str(i)) == questao['resposta_correta']:
                acertos += 1
        
        total_questoes = len(questao_ids)
        porcentagem = (acertos / total_questoes) * 100
        
        # Limpar sessão
        session.clear()
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Resultado - ConcursoMaster</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f6fa;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .resultado {{
                    background: #2c3e50;
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .btn {{
                    display: inline-block;
                    background: #3498db;
                    color: white;
                    padding: 12px 24px;
                    margin: 10px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="resultado">
                    <h1>📊 Resultado do Simulado</h1>
                    <h2>{porcentagem:.1f}% de acertos</h2>
                    <p>Você acertou {acertos} de {total_questoes} questões</p>
                </div>
                
                <div>
                    <a href="/simulado" class="btn">🔄 Fazer Novo Simulado</a>
                    <a href="/" class="btn">🏠 Página Inicial</a>
                </div>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        print(f'❌ Erro no resultado: {e}')
        return '<h2>Erro ao calcular resultado</h2><a href="/">Voltar</a>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Servidor iniciado na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
