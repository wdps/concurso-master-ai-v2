from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
from datetime import datetime, timedelta
import os
import csv

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

def get_db_connection():
    conn = sqlite3.connect('concurso.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_questoes_csv():
    '''Carrega questões do SEU arquivo CSV com a estrutura real'''
    if not os.path.exists('questoes.csv'):
        print('❌ Arquivo questoes.csv não encontrado')
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT,
                materia TEXT,
                alternativas TEXT,
                resposta_correta TEXT,
                explicacao TEXT,
                dificuldade TEXT
            )
        ''')
        
        # Limpar tabela existente para evitar duplicatas
        cursor.execute('DELETE FROM questoes')
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            questoes_carregadas = 0
            
            for row in csv_reader:
                try:
                    # Mapear colunas do SEU CSV
                    enunciado = row.get('enunciado', '').strip()
                    materia = row.get('disciplina', 'Geral').strip()  # SEU CSV usa 'disciplina'
                    
                    # Construir dicionário de alternativas do SEU CSV
                    alternativas_dict = {
                        'A': row.get('alt_a', '').strip(),
                        'B': row.get('alt_b', '').strip(), 
                        'C': row.get('alt_c', '').strip(),
                        'D': row.get('alt_d', '').strip()
                    }
                    
                    resposta_correta = row.get('gabarito', 'A').strip()
                    
                    # Criar explicação com as justificativas do SEU CSV
                    explicacao_parts = []
                    if row.get('just_a'): explicacao_parts.append(f"A: {row['just_a']}")
                    if row.get('just_b'): explicacao_parts.append(f"B: {row['just_b']}")
                    if row.get('just_c'): explicacao_parts.append(f"C: {row['just_c']}")
                    if row.get('just_d'): explicacao_parts.append(f"D: {row['just_d']}")
                    if row.get('dica_interpretacao'): explicacao_parts.append(f"Dica: {row['dica_interpretacao']}")
                    
                    explicacao = ' | '.join(explicacao_parts) if explicacao_parts else 'Explicação não disponível'
                    dificuldade = row.get('dificuldade', 'Média').strip()
                    
                    # Inserir no banco
                    cursor.execute('''
                        INSERT INTO questoes 
                        (enunciado, materia, alternativas, resposta_correta, explicacao, dificuldade)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        enunciado,
                        materia,
                        json.dumps(alternativas_dict, ensure_ascii=False),
                        resposta_correta,
                        explicacao,
                        dificuldade
                    ))
                    
                    questoes_carregadas += 1
                    
                except Exception as e:
                    print(f'⚠️ Erro ao processar linha: {e}')
                    continue
        
        conn.commit()
        conn.close()
        print(f'✅ {questoes_carregadas} questões carregadas do CSV!')
        return True
        
    except Exception as e:
        print(f'❌ Erro ao carregar CSV: {e}')
        return False

def init_database():
    '''Inicialização do banco com SEU CSV'''
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT,
                materia TEXT,
                alternativas TEXT,
                resposta_correta TEXT,
                explicacao TEXT,
                dificuldade TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        # Carregar questões do SEU CSV
        return carregar_questoes_csv()
        
    except Exception as e:
        print(f'❌ Erro na inicialização: {e}')
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    init_database()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT materia FROM questoes WHERE materia IS NOT NULL')
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        
        print(f'📚 Matérias disponíveis: {materias}')
        return render_template('simulado.html', materias=materias)
        
    except Exception as e:
        print(f'❌ Erro no /simulado: {e}')
        return render_template('simulado.html', materias=['Direito Administrativo', 'Língua Portuguesa', 'Raciocínio Lógico', 'Direito Constitucional'])

@app.route('/redacao')
def redacao():
    return render_template('redacao.html', tema={'tema': 'Tema Exemplo', 'dicas': 'Escreva sobre este tema...'})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ========== API PARA SIMULADO ==========

@app.route('/api/questoes/random')
def get_questoes_random():
    '''API para buscar questões aleatórias do SEU CSV'''
    try:
        init_database()
        quantidade = int(request.args.get('quantidade', 5))
        materias = request.args.getlist('materias')
        
        print(f'🎯 Buscando {quantidade} questões para matérias: {materias}')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Se não selecionou matérias, busca de todas
        if not materias:
            cursor.execute('SELECT * FROM questoes ORDER BY RANDOM() LIMIT ?', (quantidade,))
        else:
            placeholders = ','.join(['?'] * len(materias))
            query = f'SELECT * FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
            cursor.execute(query, materias + [quantidade])
        
        questoes_db = cursor.fetchall()
        conn.close()
        
        # Formatar questões
        questoes = []
        for q in questoes_db:
            try:
                alternativas = json.loads(q['alternativas'])
            except:
                alternativas = {'A': 'Alternativa A', 'B': 'Alternativa B', 'C': 'Alternativa C', 'D': 'Alternativa D'}
            
            questoes.append({
                'id': q['id'],
                'enunciado': q['enunciado'],
                'materia': q['materia'],
                'alternativas': alternativas,
                'resposta_correta': q['resposta_correta'],
                'explicacao': q['explicacao'],
                'dificuldade': q.get('dificuldade', 'Média')
            })
        
        print(f'✅ Retornando {len(questoes)} questões')
        return jsonify({'success': True, 'questoes': questoes})
        
    except Exception as e:
        print(f'❌ Erro na API: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    '''Inicia um novo simulado com questões do SEU CSV'''
    try:
        data = request.get_json()
        quantidade = data.get('quantidade', 5)
        materias = data.get('materias', [])
        
        print(f'🚀 Iniciando simulado: {quantidade} questões, matérias: {materias}')
        
        # Buscar questões
        response = get_questoes_random()
        if response.status_code != 200:
            return jsonify({'success': False, 'error': 'Erro ao buscar questões'}), 500
            
        resultado = response.get_json()
        if not resultado.get('success'):
            return jsonify({'success': False, 'error': resultado.get('error', 'Erro desconhecido')}), 500
        
        questoes = resultado['questoes']
        
        if not questoes:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 404
        
        # Configurar sessão
        session['simulado_ativo'] = True
        session['questoes'] = questoes
        session['respostas'] = {}
        session['inicio'] = datetime.now().isoformat()
        session['config'] = {
            'quantidade': quantidade,
            'materias': materias
        }
        
        return jsonify({
            'success': True,
            'total': len(questoes),
            'questoes_ids': [q['id'] for q in questoes]
        })
        
    except Exception as e:
        print(f'❌ Erro ao iniciar simulado: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
