import sqlalchemy as db
import csv
import os
from datetime import datetime
import logging
import shutil
import re

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configurações ---
DB_NAME = 'concurso.db'
CSV_FILENAME = 'questoes.csv'
TB_QUESTOES = 'questoes'
TB_ESTATISTICAS = 'estatisticas'
TB_SIMULADOS_FEITOS = 'simulados_feitos'
DELIMITER = ';'

# --- Pesos das Disciplinas (Mesmo do main.py) ---
PESOS_DISCIPLINAS = {
    "Língua Portuguesa": 1.5,
    "Matemática": 1.0,
    "Raciocínio Lógico": 1.0,
    "Direito Administrativo": 2.0,
    "Direito Constitucional": 2.0,
    "Psicologia": 1.0,
    "Atualidades": 1.0,
    "Conhecimentos Bancários": 1.5,
    "Informática": 1.0,
    "Matemática Financeira": 1.0,
    "Vendas e Negociação": 1.0,
    "Português e Redação Oficial": 1.5,
    "Legislação": 2.0,
    "Geral": 1.0
}

# --- FUNÇÕES AUXILIARES MELHORADAS ---
def sanitizar_texto(texto):
    """Remove caracteres problemáticos e normaliza texto"""
    if not texto:
        return ""
    # Remove caracteres de controle e normaliza espaços
    texto = re.sub(r'[\x00-\x1F\x7F]', '', str(texto))
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def validar_questao_completa(dados_questao):
    """Validação mais robusta da questão"""
    erros = []
    
    # Validar enunciado
    if len(dados_questao['enunciado'].strip()) < 10:
        erros.append("Enunciado muito curto")
    
    # Validar alternativas
    alternativas = ['alt_a', 'alt_b', 'alt_c', 'alt_d']
    for alt in alternativas:
        if len(dados_questao[alt].strip()) < 1:
            erros.append(f"Alternativa {alt} vazia")
    
    # Validar gabarito
    if dados_questao['gabarito'] not in ['A', 'B', 'C', 'D']:
        erros.append("Gabarito inválido")
    
    return erros

# --- SISTEMA DE BACKUP AUTOMÁTICO ---
def criar_backup_automatico():
    """Cria backup automático do banco se existir"""
    if os.path.exists(DB_NAME):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.db"
        try:
            shutil.copy2(DB_NAME, backup_name)
            logger.info(f"📦 Backup criado: {backup_name}")
            return backup_name
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return None
    return None

# --- Estrutura da Tabela de Questões ---
def get_questoes_table(metadata):
    """Define a estrutura premium da tabela de questões."""
    return db.Table(
        TB_QUESTOES, metadata,
        db.Column('id', db.Integer, primary_key=True),
        db.Column('disciplina', db.String, nullable=False, index=True),
        db.Column('assunto', db.String, nullable=False),
        db.Column('enunciado', db.Text, nullable=False),
        db.Column('alt_a', db.Text, nullable=False),
        db.Column('alt_b', db.Text, nullable=False),
        db.Column('alt_c', db.Text, nullable=False),
        db.Column('alt_d', db.Text, nullable=False),
        db.Column('gabarito', db.String(1), nullable=False),
        db.Column('just_a', db.Text),
        db.Column('just_b', db.Text),
        db.Column('just_c', db.Text),
        db.Column('just_d', db.Text),
        db.Column('dica_interpretacao', db.Text),
        db.Column('formula_aplicavel', db.Text),
        db.Column('nivel', db.String(20)),
        db.Column('data_criacao', db.String, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        db.Column('ativo', db.Boolean, default=True)
    )

# --- Estrutura da Tabela de Estatísticas ---
def get_estatisticas_table(metadata):
    """Define a estrutura premium da tabela de estatísticas."""
    return db.Table(
        TB_ESTATISTICAS, metadata,
        db.Column('disciplina', db.String, primary_key=True),
        db.Column('acertos', db.Integer, default=0),
        db.Column('erros', db.Integer, default=0),
        db.Column('score_total', db.Float, default=0.0),
        db.Column('ultima_atualizacao', db.String, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        db.Column('taxa_acerto', db.Float, default=0.0)
    )

# --- Estrutura da Tabela de Histórico de Simulados ---
def get_simulados_feitos_table(metadata):
    """Define a estrutura premium da tabela de histórico de simulados."""
    return db.Table(
        TB_SIMULADOS_FEITOS, metadata,
        db.Column('id', db.Integer, primary_key=True, autoincrement=True),
        db.Column('data_registro', db.String, nullable=False, index=True),
        db.Column('total_questoes', db.Integer, nullable=False),
        db.Column('acertos', db.Integer, nullable=False),
        db.Column('pontuacao_final', db.Float, nullable=False),
        db.Column('duracao_segundos', db.Integer, nullable=False),
        db.Column('nome_usuario', db.String, nullable=False),
        db.Column('modo', db.String(20), default='simulado'),
        db.Column('aproveitamento', db.Float),
        db.Column('tempo_medio_questao', db.Float)
    )

def criar_banco_e_tabelas():
    """Cria a engine, o metadata e define todas as tabelas de forma premium."""
    
    # Criar backup antes de prosseguir
    backup = criar_backup_automatico()
    if backup:
        logger.info(f"✅ Backup do banco anterior salvo como: {backup}")
    
    engine = db.create_engine(f'sqlite:///{DB_NAME}')
    metadata = db.MetaData()

    # Criar tabelas
    questoes_table = get_questoes_table(metadata)
    estatisticas_table = get_estatisticas_table(metadata)
    simulados_table = get_simulados_feitos_table(metadata)

    metadata.create_all(engine)
    logger.info(f"✅ Banco '{DB_NAME}' criado com 3 tabelas premium: (questoes, estatisticas, simulados_feitos)")
    
    return engine, questoes_table, estatisticas_table, simulados_table

def validar_linha_csv(linha, numero_linha):
    """Valida uma linha do CSV antes da inserção."""
    if len(linha) != 16:
        logger.error(f"❌ Linha {numero_linha}: Esperava 16 colunas, encontrou {len(linha)}")
        return False
    
    # Validar ID
    try:
        id_val = int(linha[0] or 0)
        if id_val <= 0:
            logger.error(f"❌ Linha {numero_linha}: ID inválido: {linha[0]}")
            return False
    except ValueError:
        logger.error(f"❌ Linha {numero_linha}: ID não numérico: {linha[0]}")
        return False
    
    # Validar gabarito
    gabarito = linha[8].strip().upper()
    if gabarito not in ['A', 'B', 'C', 'D']:
        logger.error(f"❌ Linha {numero_linha}: Gabarito inválido: {gabarito}")
        return False
    
    # Validar disciplina
    disciplina = linha[1].strip()
    if not disciplina:
        logger.error(f"❌ Linha {numero_linha}: Disciplina vazia")
        return False
    
    return True

def processar_dados_questao(row):
    """Processa e limpa os dados de uma questão do CSV."""
    dados = {
        'id': int(row[0]),
        'disciplina': sanitizar_texto(row[1]),
        'assunto': sanitizar_texto(row[2]),
        'enunciado': sanitizar_texto(row[3]),
        'alt_a': sanitizar_texto(row[4]),
        'alt_b': sanitizar_texto(row[5]),
        'alt_c': sanitizar_texto(row[6]),
        'alt_d': sanitizar_texto(row[7]),
        'gabarito': row[8].strip().upper(),
        'just_a': sanitizar_texto(row[9]),
        'just_b': sanitizar_texto(row[10]),
        'just_c': sanitizar_texto(row[11]),
        'just_d': sanitizar_texto(row[12]),
        'dica_interpretacao': sanitizar_texto(row[13]),
        'formula_aplicavel': sanitizar_texto(row[14]),
        'nivel': sanitizar_texto(row[15]) or 'Médio'
    }
    
    # Validação completa
    erros = validar_questao_completa(dados)
    if erros:
        logger.warning(f"⚠️ Questão ID {dados['id']} com avisos: {', '.join(erros)}")
    
    return dados

def inserir_dados_csv(engine, questoes_table, estatisticas_table):
    """Insere dados do CSV no banco com validação premium."""
    
    questoes_inseridas = 0
    disciplinas_encontradas = set()
    linhas_com_erro = 0

    try:
        if not os.path.exists(CSV_FILENAME):
            logger.error(f"❌ Arquivo '{CSV_FILENAME}' não encontrado")
            return 0

        with open(CSV_FILENAME, mode='r', encoding='utf-8') as file:
            # Ler e validar cabeçalho
            cabecalho = file.readline().strip().split(DELIMITER)
            if len(cabecalho) != 16:
                logger.error(f"❌ Cabeçalho do CSV inválido. Esperava 16 colunas, encontrou {len(cabecalho)}")
                return 0

            file.seek(0)
            reader = csv.reader(file, delimiter=DELIMITER, quoting=csv.QUOTE_NONE, skipinitialspace=True)
            next(reader)  # Pular cabeçalho

            with engine.connect() as conn:
                # Limpar tabela existente
                conn.execute(db.delete(questoes_table))
                logger.info("🧹 Tabela de questões limpa")

                # Inserir questões
                for numero_linha, row in enumerate(reader, start=2):
                    if not row or row[0].startswith('#'):
                        continue

                    # Validar linha
                    if not validar_linha_csv(row, numero_linha):
                        linhas_com_erro += 1
                        continue

                    # Processar dados
                    dados_questao = processar_dados_questao(row)
                    disciplinas_encontradas.add(dados_questao['disciplina'])

                    # Inserir questão
                    try:
                        conn.execute(db.insert(questoes_table).values(**dados_questao))
                        questoes_inseridas += 1

                        if questoes_inseridas % 50 == 0:
                            logger.info(f"📥 {questoes_inseridas} questões inseridas...")

                    except Exception as e:
                        logger.error(f"❌ Erro ao inserir questão ID {dados_questao['id']}: {e}")
                        linhas_com_erro += 1

                conn.commit()

                # Inicializar estatísticas
                logger.info("📊 Inicializando tabela de estatísticas...")
                for disc in sorted(disciplinas_encontradas):
                    # Verificar se disciplina já existe
                    select_estat = db.select(estatisticas_table).where(
                        estatisticas_table.columns.disciplina == disc
                    )
                    existing = conn.execute(select_estat).fetchone()

                    if not existing:
                        peso = PESOS_DISCIPLINAS.get(disc, 1.0)
                        conn.execute(db.insert(estatisticas_table).values(
                            disciplina=disc,
                            acertos=0,
                            erros=0,
                            score_total=0.0,
                            taxa_acerto=0.0
                        ))
                        logger.debug(f"  ✅ Estatística inicializada para: {disc}")

                conn.commit()

        # Relatório final
        logger.info(f"\n🎉 RELATÓRIO DE CARGA DE DADOS:")
        logger.info(f"✅ Questões inseridas com sucesso: {questoes_inseridas}")
        logger.info(f"❌ Linhas com erro: {linhas_com_erro}")
        logger.info(f"📚 Disciplinas encontradas: {len(disciplinas_encontradas)}")
        logger.info(f"📋 Disciplinas: {', '.join(sorted(disciplinas_encontradas))}")

        return questoes_inseridas

    except FileNotFoundError:
        logger.error(f"❌ Arquivo '{CSV_FILENAME}' não encontrado")
        return 0
    except Exception as e:
        logger.error(f"❌ Erro inesperado durante inserção: {e}")
        return 0

def criar_dados_exemplo_simulados(engine, simulados_table):
    """Cria alguns dados de exemplo para simulados (opcional)."""
    try:
        with engine.connect() as conn:
            # Verificar se já existem dados
            existing = conn.execute(db.select(simulados_table).limit(1)).fetchone()
            if existing:
                logger.info("📊 Dados de exemplo já existem")
                return

            # Criar alguns registros de exemplo
            exemplos = [
                {
                    'data_registro': '2024-01-15 14:30:00',
                    'total_questoes': 20,
                    'acertos': 16,
                    'pontuacao_final': 28.5,
                    'duracao_segundos': 3600,
                    'nome_usuario': 'Wanderson de Paula',
                    'aproveitamento': 80.0,
                    'tempo_medio_questao': 180.0
                },
                {
                    'data_registro': '2024-01-10 09:15:00',
                    'total_questoes': 30,
                    'acertos': 22,
                    'pontuacao_final': 38.0,
                    'duracao_segundos': 5400,
                    'nome_usuario': 'Wanderson de Paula',
                    'aproveitamento': 73.3,
                    'tempo_medio_questao': 180.0
                },
                {
                    'data_registro': '2024-01-05 16:45:00',
                    'total_questoes': 25,
                    'acertos': 20,
                    'pontuacao_final': 35.5,
                    'duracao_segundos': 4500,
                    'nome_usuario': 'Wanderson de Paula',
                    'aproveitamento': 80.0,
                    'tempo_medio_questao': 180.0
                }
            ]

            for exemplo in exemplos:
                conn.execute(db.insert(simulados_table).values(**exemplo))

            conn.commit()
            logger.info("✅ Dados de exemplo para simulados criados")

    except Exception as e:
        logger.error(f"❌ Erro ao criar dados exemplo: {e}")

def verificar_integridade_banco(engine, questoes_table):
    """Verifica a integridade do banco de dados após a criação."""
    try:
        with engine.connect() as conn:
            # Verificar total de questões
            total_questoes = conn.execute(db.select(db.func.count()).select_from(questoes_table)).scalar()
            
            # Verificar disciplinas únicas
            disciplinas = conn.execute(db.select(questoes_table.columns.disciplina).distinct()).fetchall()
            disciplinas = [d[0] for d in disciplinas]
            
            # Verificar questões sem alternativas
            questoes_sem_alternativas = conn.execute(
                db.select(questoes_table.columns.id).where(
                    db.or_(
                        db.and_(questoes_table.columns.alt_a == '', questoes_table.columns.alt_b == ''),
                        db.and_(questoes_table.columns.alt_c == '', questoes_table.columns.alt_d == '')
                    )
                )
            ).fetchall()
            
            logger.info(f"🔍 VERIFICAÇÃO DE INTEGRIDADE:")
            logger.info(f"✅ Total de questões no banco: {total_questoes}")
            logger.info(f"✅ Disciplinas carregadas: {len(disciplinas)}")
            logger.info(f"✅ Disciplinas: {', '.join(disciplinas)}")
            logger.info(f"⚠️  Questões com problemas: {len(questoes_sem_alternativas)}")
            
            return total_questoes > 0 and len(questoes_sem_alternativas) == 0
            
    except Exception as e:
        logger.error(f"❌ Erro na verificação de integridade: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 INICIANDO SETUP PREMIUM DO BANCO DE DADOS")
    
    # Remover banco antigo se existir
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            logger.info(f"🗑️ Banco antigo '{DB_NAME}' removido")
        except Exception as e:
            logger.error(f"❌ Erro ao remover banco antigo: {e}")

    try:
        # Criar banco e tabelas
        engine, questoes_table, estatisticas_table, simulados_table = criar_banco_e_tabelas()

        # Inserir dados do CSV
        total_inserido = inserir_dados_csv(engine, questoes_table, estatisticas_table)

        if total_inserido > 0:
            # Criar dados de exemplo
            criar_dados_exemplo_simulados(engine, simulados_table)
            
            # Verificar integridade
            integridade_ok = verificar_integridade_banco(engine, questoes_table)
            
            if integridade_ok:
                logger.info("\n🎊 SETUP CONCLUÍDO COM SUCESSO!")
                logger.info("💡 Próximo passo: Execute 'uvicorn main:app --reload'")
                logger.info("🌐 Acesse: http://127.0.0.1:8000")
            else:
                logger.error("\n⚠️  Setup concluído com avisos de integridade")
                
        else:
            logger.error("\n💥 SETUP FALHOU - Nenhuma questão foi inserida")

    except Exception as e:
        logger.error(f"💥 Falha crítica no setup: {e}")