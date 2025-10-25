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
app.secret_key = 'concurso_master_secret_key_2024'

class SistemaSimulado:
    def __init__(self):
        self.simulados_ativos = {}
    
    def iniciar_simulado(self, user_id, config):
        """Inicia um novo simulado"""
        simulado_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        simulado_data = {
            'id': simulado_id,
            'config': config,
            'questoes': [],
            'respostas': [],
            'inicio': datetime.now(),
            'tempo_restante': config.get('tempo_minutos', 180) * 60,
            'status': 'ativo'
        }
        
        # Carregar questões
        questoes = self._carregar_questoes_simulado(config)
        simulado_data['questoes'] = questoes
        simulado_data['questao_atual'] = 0
        
        self.simulados_ativos[simulado_id] = simulado_data
        return simulado_id
    
    def _carregar_questoes_simulado(self, config):
        """Carrega questões baseado na configuração"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            materias = config.get('materias', [])
            quantidade = config.get('quantidade_total', 50)
            aleatorio = config.get('aleatorio', True)
            
            query = "SELECT * FROM questões WHERE 1=1"
            params = []
            
            if materias:
                placeholders = ','.join(['?'] * len(materias))
                query += f" AND disciplina IN ({placeholders})"
                params.extend(materias)
            
            if aleatorio:
                query += " ORDER BY RANDOM()"
            else:
                query += " ORDER BY id"
            
            query += " LIMIT ?"
            params.append(quantidade)
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            questoes = []
            for row in resultados:
                questao = {
                    'id': row['id'],
                    'enunciado': row['enunciado'],
                    'materia': row['disciplina'],
                    'alternativas': {
                        'A': row['alt_a'],
                        'B': row['alt_b'],
                        'C': row['alt_c'],
                        'D': row['alt_d']
                    },
                    'resposta_correta': row['gabarito'],
                    'dificuldade': row.get('dificuldade', 'Médio'),
                    'justificativa': row.get('justificativa'),
                    'dica': row.get('dica'),
                    'formula': row.get('formula')
                }
                questoes.append(questao)
            
            return questoes
            
        except Exception as e:
            logger.error(f"Erro ao carregar questões: {e}")
            return []
        finally:
            conn.close()
    
    def registrar_resposta(self, simulado_id, questao_index, alternativa, tempo_gasto):
        """Registra uma resposta do usuário"""
        if simulado_id not in self.simulados_ativos:
            return False
        
        simulado = self.simulados_ativos[simulado_id]
        
        if questao_index >= len(simulado['questoes']):
            return False
        
        questao = simulado['questoes'][questao_index]
        acertou = alternativa.upper() == questao['resposta_correta'].upper()
        
        resposta = {
            'questao_id': questao['id'],
            'questao_index': questao_index,
            'alternativa_escolhida': alternativa,
            'acertou': acertou,
            'tempo_gasto': tempo_gasto,
            'timestamp': datetime.now()
        }
        
        simulado['respostas'].append(resposta)
        return True
    
    def finalizar_simulado(self, simulado_id):
        """Finaliza simulado e gera relatório"""
        if simulado_id not in self.simulados_ativos:
            return None
        
        simulado = self.simulados_ativos[simulado_id]
        simulado['fim'] = datetime.now()
        simulado['status'] = 'finalizado'
        
        relatorio = self._gerar_relatorio(simulado)
        simulado['relatorio'] = relatorio
        
        # Salvar no histórico
        self._salvar_historico(simulado)
        
        return relatorio
    
    def _gerar_relatorio(self, simulado):
        """Gera relatório detalhado do simulado"""
        respostas = simulado['respostas']
        total_questoes = len(simulado['questoes'])
        questoes_respondidas = len(respostas)
        
        # Estatísticas gerais
        acertos = sum(1 for r in respostas if r['acertou'])
        percentual_acerto = (acertos / questoes_respondidas * 100) if questoes_respondidas > 0 else 0
        
        # Tempo total
        tempo_total = sum(r['tempo_gasto'] for r in respostas)
        
        # Estatísticas por matéria
        estatisticas_materia = {}
        for resposta in respostas:
            questao = simulado['questoes'][resposta['questao_index']]
            materia = questao['materia']
            
            if materia not in estatisticas_materia:
                estatisticas_materia[materia] = {'total': 0, 'acertos': 0, 'tempo': 0}
            
            estatisticas_materia[materia]['total'] += 1
            estatisticas_materia[materia]['tempo'] += resposta['tempo_gasto']
            if resposta['acertou']:
                estatisticas_materia[materia]['acertos'] += 1
        
        # Calcular percentuais
        for materia, stats in estatisticas_materia.items():
            stats['percentual'] = (stats['acertos'] / stats['total'] * 100) if stats['total'] > 0 else 0
            stats['tempo_medio'] = stats['tempo'] / stats['total'] if stats['total'] > 0 else 0
        
        # Recomendações
        recomendacoes = self._gerar_recomendacoes(estatisticas_materia)
        
        return {
            'geral': {
                'total_questoes': total_questoes,
                'questoes_respondidas': questoes_respondidas,
                'acertos': acertos,
                'erros': questoes_respondidas - acertos,
                'percentual_acerto': round(percentual_acerto, 2),
                'tempo_total_minutos': round(tempo_total / 60, 2),
                'tempo_medio_questao': round(tempo_total / questoes_respondidas, 2) if questoes_respondidas > 0 else 0
            },
            'por_materia': estatisticas_materia,
            'recomendacoes': recomendacoes,
            'questoes_com_detalhes': self._preparar_questoes_detalhadas(simulado)
        }
    
    def _gerar_recomendacoes(self, estatisticas_materia):
        """Gera recomendações personalizadas"""
        recomendacoes = []
        
        for materia, stats in estatisticas_materia.items():
            if stats['percentual'] < 50:
                recomendacoes.append(f"🚨 Foco urgente em {materia} - Apenas {stats['percentual']:.1f}% de acerto")
            elif stats['percentual'] < 70:
                recomendacoes.append(f"📚 Continue estudando {materia} - {stats['percentual']:.1f}% de acerto")
            elif stats['percentual'] < 90:
                recomendacoes.append(f"✅ Bom desempenho em {materia} - {stats['percentual']:.1f}% de acerto")
            else:
                recomendacoes.append(f"🎉 Excelente em {materia} - {stats['percentual']:.1f}% de acerto")
        
        if not recomendacoes:
            recomendacoes.append("📈 Continue com estudos equilibrados em todas as matérias")
        
        return recomendacoes
    
    def _preparar_questoes_detalhadas(self, simulado):
        """Prepara questões com detalhes para revisão"""
        detalhes = []
        
        for i, questao in enumerate(simulado['questoes']):
            resposta_usuario = None
            if i < len(simulado['respostas']):
                resposta_usuario = simulado['respostas'][i]
            
            detalhe_questao = {
                'numero': i + 1,
                'enunciado': questao['enunciado'],
                'materia': questao['materia'],
                'alternativas': questao['alternativas'],
                'resposta_correta': questao['resposta_correta'],
                'justificativa': questao.get('justificativa'),
                'dica': questao.get('dica'),
                'formula': questao.get('formula'),
                'resposta_usuario': resposta_usuario['alternativa_escolhida'] if resposta_usuario else None,
                'acertou': resposta_usuario['acertou'] if resposta_usuario else None,
                'tempo_gasto': resposta_usuario['tempo_gasto'] if resposta_usuario else None
            }
            
            detalhes.append(detalhe_questao)
        
        return detalhes
    
    def _salvar_historico(self, simulado):
        """Salva simulado no histórico"""
        conn = get_db_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # Criar tabela de histórico se não existir
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
            
            # Salvar simulado
            cursor.execute('''
                INSERT OR REPLACE INTO historico_simulados 
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
            logger.error(f"Erro ao salvar histórico: {e}")
        finally:
            conn.close()

# Instância global do sistema
sistema_simulado = SistemaSimulado()

def get_db_connection():
    """Conexão segura com o banco"""
    try:
        conn = sqlite3.connect('concurso.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"❌ Erro na conexão: {e}")
        return None

def criar_tabelas_se_necessario():
    """Cria tabelas necessárias se não existirem"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabela de questões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questões (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disciplina TEXT NOT NULL,
                enunciado TEXT NOT NULL,
                alt_a TEXT NOT NULL,
                alt_b TEXT NOT NULL,
                alt_c TEXT NOT NULL,
                alt_d TEXT NOT NULL,
                gabarito TEXT NOT NULL,
                dificuldade TEXT DEFAULT 'Médio',
                justificativa TEXT,
                dica TEXT,
                formula TEXT,
                tempo_estimado INTEGER DEFAULT 60,
                ano_prova TEXT,
                banca_organizadora TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de redações
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
        
        # Tabela de histórico de redações
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
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        conn.close()
        return False

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def home():
    """Página inicial com dashboard"""
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    """Página do simulado"""
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    """Página de redação"""
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard_page():
    """Página de dashboard detalhado"""
    return render_template('dashboard.html')

# ========== API ENDPOINTS ==========

@app.route('/api/health')
def health():
    return jsonify({
        "status": "online", 
        "message": "ConcursoMaster AI 3.0",
        "version": "3.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/materias')
def materias():
    """API de matérias"""
    criar_tabelas_se_necessario()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"materias": [], "estatisticas": {}, "total_geral": 0})
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT disciplina FROM questões ORDER BY disciplina")
        rows = cursor.fetchall()
        materias = [row['disciplina'] for row in rows] if rows else []
        
        estatisticas = {}
        total_geral = 0
        
        for materia in materias:
            cursor.execute("SELECT COUNT(*) as total FROM questões WHERE disciplina = ?", (materia,))
            result = cursor.fetchone()
            total_materia = result['total'] if result else 0
            
            estatisticas[materia] = {
                'total': total_materia,
                'faceis': 0,  # Simplificado para demo
                'medias': total_materia,
                'dificeis': 0
            }
            
            total_geral += total_materia
        
        conn.close()
        
        return jsonify({
            "materias": materias,
            "estatisticas": estatisticas,
            "total_geral": total_geral
        })
        
    except Exception as e:
        logger.error(f"Erro em /api/materias: {e}")
        return jsonify({"materias": [], "estatisticas": {}, "total_geral": 0})

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    """Inicia um novo simulado"""
    try:
        data = request.get_json()
        
        config = {
            'materias': data.get('materias', []),
            'quantidade_total': data.get('quantidade_total', 50),
            'tempo_minutos': data.get('tempo_minutos', 180),
            'aleatorio': data.get('aleatorio', True)
        }
        
        user_id = 'user_' + datetime.now().strftime('%Y%m%d%H%M%S')
        simulado_id = sistema_simulado.iniciar_simulado(user_id, config)
        
        return jsonify({
            "success": True,
            "simulado_id": simulado_id,
            "quantidade_questoes": len(sistema_simulado.simulados_ativos[simulado_id]['questoes'])
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar simulado: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/simulado/<simulado_id>/questao/<int:questao_index>')
def get_questao_simulado(simulado_id, questao_index):
    """Obtém questão específica do simulado"""
    if simulado_id not in sistema_simulado.simulados_ativos:
        return jsonify({"error": "Simulado não encontrado"}), 404
    
    simulado = sistema_simulado.simulados_ativos[simulado_id]
    
    if questao_index >= len(simulado['questoes']):
        return jsonify({"error": "Questão não encontrada"}), 404
    
    questao = simulado['questoes'][questao_index]
    
    return jsonify({
        "questao": questao,
        "numero_questao": questao_index + 1,
        "total_questoes": len(simulado['questoes']),
        "tempo_restante": simulado['tempo_restante']
    })

@app.route('/api/simulado/<simulado_id>/responder', methods=['POST'])
def responder_questao(simulado_id):
    """Registra resposta da questão"""
    try:
        data = request.get_json()
        
        questao_index = data.get('questao_index')
        alternativa = data.get('alternativa')
        tempo_gasto = data.get('tempo_gasto', 0)
        
        success = sistema_simulado.registrar_resposta(
            simulado_id, questao_index, alternativa, tempo_gasto
        )
        
        return jsonify({"success": success})
        
    except Exception as e:
        logger.error(f"Erro ao registrar resposta: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/simulado/<simulado_id>/finalizar', methods=['POST'])
def finalizar_simulado(simulado_id):
    """Finaliza simulado e retorna relatório"""
    try:
        relatorio = sistema_simulado.finalizar_simulado(simulado_id)
        
        if relatorio:
            return jsonify({
                "success": True,
                "relatorio": relatorio
            })
        else:
            return jsonify({"success": False, "error": "Simulado não encontrado"})
            
    except Exception as e:
        logger.error(f"Erro ao finalizar simulado: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/redacoes/temas')
def get_temas_redacao():
    """Obtém temas de redação disponíveis"""
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
        logger.error(f"Erro ao obter temas: {e}")
        return jsonify({"temas": []})

@app.route('/api/redacoes/corrigir', methods=['POST'])
def corrigir_redacao():
    """Corrige uma redação"""
    try:
        data = request.get_json()
        
        redacao_id = data.get('redacao_id')
        texto_redacao = data.get('texto_redacao')
        
        # Simulação de correção (em produção, integrar com IA)
        correcao = {
            'nota': random.randint(600, 1000),
            'competencia_1': {'nota': random.randint(120, 200), 'comentario': 'Bom domínio da norma culta'},
            'competencia_2': {'nota': random.randint(120, 200), 'comentario': 'Tema bem desenvolvido'},
            'competencia_3': {'nota': random.randint(120, 200), 'comentario': 'Argumentação consistente'},
            'competencia_4': {'nota': random.randint(120, 200), 'comentario': 'Boa organização textual'},
            'competencia_5': {'nota': random.randint(120, 200), 'comentario': 'Proposta de intervenção adequada'},
            'feedback_geral': 'Redação bem estruturada, com argumentos consistentes e proposta de intervenção adequada ao tema.',
            'sugestoes_melhoria': [
                'Ampliar o repertório sociocultural',
                'Cuidado com repetição de conectivos',
                'Desenvolver mais os argumentos no segundo parágrafo'
            ]
        }
        
        # Salvar correção
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
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/dashboard/estatisticas')
def get_estatisticas_dashboard():
    """Estatísticas para o dashboard"""
    criar_tabelas_se_necessario()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"estatisticas": {}})
    
    try:
        cursor = conn.cursor()
        
        # Total de questões
        cursor.execute("SELECT COUNT(*) as total FROM questões")
        total_questoes = cursor.fetchone()['total']
        
        # Questões por matéria
        cursor.execute('''
            SELECT disciplina, COUNT(*) as quantidade 
            FROM questões 
            GROUP BY disciplina 
            ORDER BY quantidade DESC
        ''')
        questoes_materia = {row['disciplina']: row['quantidade'] for row in cursor.fetchall()}
        
        # Histórico de simulados
        cursor.execute('''
            SELECT relatorio FROM historico_simulados 
            ORDER BY data_fim DESC LIMIT 10
        ''')
        historico_simulados = []
        for row in cursor.fetchall():
            try:
                relatorio = json.loads(row['relatorio'])
                historico_simulados.append(relatorio['geral'])
            except:
                pass
        
        conn.close()
        
        return jsonify({
            "estatisticas": {
                "total_questoes": total_questoes,
                "questoes_por_materia": questoes_materia,
                "historico_simulados": historico_simulados
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({"estatisticas": {}})

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 ConcursoMaster AI 3.0 iniciando na porta {port}")
    criar_tabelas_se_necessario()
    app.run(host='0.0.0.0', port=port, debug=False)
