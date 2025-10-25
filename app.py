from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_2024_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24  # 24 horas

# Configuração do Banco de Dados
DATABASE = 'concurso.db'

def get_db_connection():
    """Conexão com o banco de dados"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Inicializa o banco de dados e carrega questões"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar tabela de questões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT NOT NULL,
                materia TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT,
                dificuldade TEXT DEFAULT 'Média',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela de resultados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resultados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_questoes INTEGER,
                acertos INTEGER,
                porcentagem REAL,
                tempo_gasto REAL,
                data_simulado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Verificar se existem questões
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print('📥 Carregando questões do CSV...')
            load_questions_from_csv()
        else:
            print(f'✅ Banco inicializado com {count} questões')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Erro ao inicializar banco: {e}')
        return False

def load_questions_from_csv():
    """Carrega questões do arquivo CSV para o banco"""
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
                    # Extrair dados do CSV
                    enunciado = row.get('enunciado', '').strip()
                    materia = row.get('disciplina', 'Geral').strip()
                    
                    # Pular linhas vazias
                    if not enunciado or not materia:
                        continue
                    
                    # Construir alternativas
                    alternativas = {
                        'A': row.get('alt_a', '').strip(),
                        'B': row.get('alt_b', '').strip(),
                        'C': row.get('alt_c', '').strip(),
                        'D': row.get('alt_d', '').strip()
                    }
                    
                    resposta_correta = row.get('gabarito', 'A').strip().upper()
                    
                    # Construir explicação detalhada
                    explicacao_parts = []
                    if row.get('just_a'): explicacao_parts.append(f"A: {row['just_a']}")
                    if row.get('just_b'): explicacao_parts.append(f"B: {row['just_b']}")
                    if row.get('just_c'): explicacao_parts.append(f"C: {row['just_c']}")
                    if row.get('just_d'): explicacao_parts.append(f"D: {row['just_d']}")
                    if row.get('dica_interpretacao'): explicacao_parts.append(f"💡 {row['dica_interpretacao']}")
                    
                    explicacao = ' | '.join(explicacao_parts) if explicacao_parts else 'Explicação detalhada não disponível'
                    dificuldade = row.get('dificuldade', 'Média').strip()
                    
                    # Inserir no banco
                    cursor.execute('''
                        INSERT INTO questoes 
                        (enunciado, materia, alternativas, resposta_correta, explicacao, dificuldade)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        enunciado, 
                        materia, 
                        json.dumps(alternativas), 
                        resposta_correta,
                        explicacao,
                        dificuldade
                    ))
                    
                    questions_loaded += 1
                    
                except Exception as e:
                    print(f'⚠️  Erro ao processar linha: {e}')
                    continue
        
        conn.commit()
        conn.close()
        
        print(f'✅ {questions_loaded} questões carregadas no banco')
        return True
        
    except Exception as e:
        print(f'❌ Erro ao carregar CSV: {e}')
        return False

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    """Página de configuração do simulado"""
    try:
        init_database()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar matérias disponíveis
        cursor.execute('''
            SELECT DISTINCT materia, COUNT(*) as total 
            FROM questoes 
            WHERE materia IS NOT NULL 
            GROUP BY materia 
            ORDER BY total DESC
        ''')
        materias = [{'nome': row['materia'], 'total': row['total']} for row in cursor.fetchall()]
        
        conn.close()
        
        return render_template('simulado.html', materias=materias)
        
    except Exception as e:
        print(f'❌ Erro na página do simulado: {e}')
        return render_template('error.html', 
                             mensagem='Erro ao carregar configurações do simulado')

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    """API para iniciar um novo simulado"""
    try:
        data = request.get_json()
        quantidade = int(data.get('quantidade', 10))
        materias_selecionadas = data.get('materias', [])
        
        print(f'🚀 Iniciando simulado: {quantidade} questões, {len(materias_selecionadas)} matérias')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar questões baseado nas matérias selecionadas
        if not materias_selecionadas:
            # Todas as matérias
            cursor.execute('''
                SELECT id FROM questoes 
                ORDER BY RANDOM() 
                LIMIT ?
            ''', (quantidade,))
        else:
            # Matérias específicas
            placeholders = ','.join(['?'] * len(materias_selecionadas))
            query = f'''
                SELECT id FROM questoes 
                WHERE materia IN ({placeholders}) 
                ORDER BY RANDOM() 
                LIMIT ?
            '''
            cursor.execute(query, materias_selecionadas + [quantidade])
        
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        if not questao_ids:
            return jsonify({
                'success': False, 
                'error': 'Nenhuma questão encontrada com os critérios selecionados'
            }), 404
        
        # Configurar sessão do simulado
        session.clear()
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        session['inicio_simulado'] = datetime.now().isoformat()
        session['config'] = {
            'quantidade': quantidade,
            'materias': materias_selecionadas
        }
        
        print(f'✅ Simulado configurado com {len(questao_ids)} questões')
        
        return jsonify({
            'success': True,
            'total_questoes': len(questao_ids),
            'redirect_url': url_for('questao', numero=1)
        })
        
    except Exception as e:
        print(f'❌ Erro ao iniciar simulado: {e}')
        return jsonify({
            'success': False, 
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/questao/<int:numero>')
def questao(numero):
    """Página individual da questão"""
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    questao_ids = session.get('questoes_ids', [])
    total_questoes = len(questao_ids)
    
    if numero < 1 or numero > total_questoes:
        return render_template('error.html', 
                             mensagem='Questão não encontrada')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar questão atual
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_ids[numero-1],))
        questao_db = cursor.fetchone()
        
        if not questao_db:
            return render_template('error.html', 
                                 mensagem='Questão não encontrada no banco')
        
        # Processar questão
        try:
            alternativas = json.loads(questao_db['alternativas'])
        except:
            alternativas = {
                'A': 'Alternativa A',
                'B': 'Alternativa B', 
                'C': 'Alternativa C',
                'D': 'Alternativa D'
            }
        
        questao_data = {
            'id': questao_db['id'],
            'enunciado': questao_db['enunciado'],
            'materia': questao_db['materia'],
            'alternativas': alternativas,
            'resposta_correta': questao_db['resposta_correta'],
            'explicacao': questao_db['explicacao'],
            'dificuldade': questao_db['dificuldade']
        }
        
        # Verificar resposta anterior
        resposta_usuario = session.get('respostas', {}).get(str(numero))
        resposta_correta = questao_data['resposta_correta']
        
        conn.close()
        
        return render_template('questao.html',
                             numero=numero,
                             total_questoes=total_questoes,
                             questao=questao_data,
                             resposta_usuario=resposta_usuario,
                             resposta_correta=resposta_correta,
                             questao_respondida=resposta_usuario is not None)
        
    except Exception as e:
        print(f'❌ Erro ao carregar questão: {e}')
        return render_template('error.html', 
                             mensagem='Erro ao carregar questão')

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    """API para registrar resposta da questão"""
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'success': False, 'error': 'Simulado não iniciado'}), 400
        
        data = request.get_json()
        numero_questao = data.get('numero_questao')
        resposta = data.get('resposta')
        
        if not numero_questao or not resposta:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
        
        # Salvar resposta na sessão
        if 'respostas' not in session:
            session['respostas'] = {}
        
        session['respostas'][str(numero_questao)] = resposta
        session.modified = True
        
        print(f'📝 Questão {numero_questao}: resposta "{resposta}" registrada')
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f'❌ Erro ao registrar resposta: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/simulado/resultado')
def resultado_simulado():
    """Página de resultados do simulado"""
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    try:
        questao_ids = session.get('questoes_ids', [])
        respostas = session.get('respostas', {})
        inicio_simulado = datetime.fromisoformat(session.get('inicio_simulado'))
        
        # Calcular resultados
        acertos = 0
        detalhes_questoes = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for i, questao_id in enumerate(questao_ids, 1):
            cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
            questao_db = cursor.fetchone()
            
            if questao_db:
                resposta_usuario = respostas.get(str(i))
                resposta_correta = questao_db['resposta_correta']
                acertou = resposta_usuario == resposta_correta
                
                if acertou:
                    acertos += 1
                
                # Processar alternativas para exibição
                try:
                    alternativas = json.loads(questao_db['alternativas'])
                except:
                    alternativas = {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}
                
                detalhes_questoes.append({
                    'numero': i,
                    'enunciado': questao_db['enunciado'],
                    'materia': questao_db['materia'],
                    'resposta_usuario': resposta_usuario,
                    'resposta_correta': resposta_correta,
                    'acertou': acertou,
                    'explicacao': questao_db['explicacao'],
                    'alternativas': alternativas,
                    'dificuldade': questao_db['dificuldade']
                })
        
        conn.close()
        
        # Calcular métricas
        total_questoes = len(questao_ids)
        porcentagem_acertos = (acertos / total_questoes) * 100 if total_questoes > 0 else 0
        tempo_total = (datetime.now() - inicio_simulado).total_seconds()
        
        # Determinar desempenho
        if porcentagem_acertos >= 90:
            desempenho = 'Excelente 🎉'
            cor_desempenho = 'success'
        elif porcentagem_acertos >= 70:
            desempenho = 'Bom 👍'
            cor_desempenho = 'info'
        elif porcentagem_acertos >= 50:
            desempenho = 'Regular 💪'
            cor_desempenho = 'warning'
        else:
            desempenho = 'Precisa melhorar 📚'
            cor_desempenho = 'danger'
        
        # Salvar resultado no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO resultados (total_questoes, acertos, porcentagem, tempo_gasto)
            VALUES (?, ?, ?, ?)
        ''', (total_questoes, acertos, porcentagem_acertos, tempo_total))
        conn.commit()
        conn.close()
        
        # Limpar sessão do simulado
        session.pop('simulado_ativo', None)
        session.pop('questoes_ids', None)
        session.pop('respostas', None)
        session.pop('inicio_simulado', None)
        session.pop('config', None)
        
        return render_template('resultado.html',
                             total_questoes=total_questoes,
                             acertos=acertos,
                             erros=total_questoes - acertos,
                             porcentagem=porcentagem_acertos,
                             tempo_minutos=tempo_total / 60,
                             desempenho=desempenho,
                             cor_desempenho=cor_desempenho,
                             detalhes_questoes=detalhes_questoes)
        
    except Exception as e:
        print(f'❌ Erro ao calcular resultados: {e}')
        return render_template('error.html', 
                             mensagem='Erro ao processar resultados')

@app.route('/dashboard')
def dashboard():
    """Dashboard com estatísticas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Estatísticas gerais
        cursor.execute('SELECT COUNT(*) as total FROM questoes')
        total_questoes = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(DISTINCT materia) as total FROM questoes')
        total_materias = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT COUNT(*) as total, materia 
            FROM questoes 
            GROUP BY materia 
            ORDER BY total DESC 
            LIMIT 5
        ''')
        top_materias = cursor.fetchall()
        
        # Histórico de simulados
        cursor.execute('''
            SELECT * FROM resultados 
            ORDER BY data_simulado DESC 
            LIMIT 10
        ''')
        historico = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html',
                             total_questoes=total_questoes,
                             total_materias=total_materias,
                             top_materias=top_materias,
                             historico=historico)
        
    except Exception as e:
        print(f'❌ Erro no dashboard: {e}')
        return render_template('error.html', 
                             mensagem='Erro ao carregar dashboard')

@app.route('/redacao')
def redacao():
    """Página de redação (futura implementação)"""
    return render_template('redacao.html')

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('error.html', 
                         mensagem='Página não encontrada'), 404

@app.errorhandler(500)
def erro_interno(e):
    return render_template('error.html', 
                         mensagem='Erro interno do servidor'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
