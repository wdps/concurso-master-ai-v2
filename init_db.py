import sqlite3
import json
import os
from datetime import datetime

# --- Configuração ---
DATABASE = 'concurso.db'

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Cria as tabelas necessárias se elas não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Criando tabela 'questoes'...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        materia TEXT NOT NULL,
        assunto TEXT,
        enunciado TEXT NOT NULL,
        alternativas TEXT NOT NULL, -- JSON string: {"A": "...", "B": "..."}
        resposta_correta TEXT NOT NULL, -- "A", "B", etc.
        dificuldade TEXT DEFAULT 'Média',
        justificativa TEXT,
        dica TEXT,
        formula TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    print("Criando tabela 'temas_redacao'...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS temas_redacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        eixo_tematico TEXT,
        texto_motivador TEXT,
        dicas TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    print("Criando tabela 'historico_simulados'...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico_simulados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        simulado_id TEXT UNIQUE NOT NULL,
        data_inicio DATETIME,
        data_fim DATETIME,
        config TEXT,        -- JSON com matérias, total_questoes, tempo_limite
        respostas TEXT,     -- JSON com as respostas { 'index': { 'alternativa': 'A', 'tempo': 10 } }
        relatorio TEXT,     -- JSON com o resultado final
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    print("Criando tabela 'historico_redacoes'...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico_redacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        tema_id INTEGER,
        titulo_tema TEXT,
        texto_enviado TEXT,
        correcao_gerada TEXT, -- JSON da correção
        nota REAL,
        data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tema_id) REFERENCES temas_redacao (id) ON DELETE SET NULL
    )
    ''')

    # Índices para otimizar consultas
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questoes_disciplina ON questoes(disciplina)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_simulados_data ON historico_simulados(data_fim)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_redacoes_user ON historico_redacoes(user_id)")
    
    conn.commit()
    conn.close()
    print("Tabelas verificadas/criadas com sucesso.")

def insert_sample_data():
    """Insere dados de exemplo se a tabela 'questoes' estiver vazia."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(id) FROM questoes")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Inserindo dados de exemplo em 'questoes'...")
        questoes = [
            ('Português', 'Uso da Crase', 'Assinale a alternativa em que o uso do acento grave indicativo da crase é FACULTATIVO:', 
             json.dumps({'A': 'Vou à Bahia no verão.', 'B': 'Refiro-me àquele aluno.', 'C': 'Disse tudo à sua mãe.', 'D': 'O evento começa às 19h.'}), 
             'C', 'Média', 
             'Correto. O uso da crase é facultativo antes de pronomes possessivos femininos (minha, sua, nossa) quando eles acompanham um substantivo.', 
             'Lembre-se da regra: "Diante de possessivo, crase é opcional".', 
             None),
             
            ('Matemática', 'Porcentagem', 'Um produto que custava R$ 120,00 teve um desconto de 15%. Qual o novo preço?', 
             json.dumps({'A': 'R$ 102,00', 'B': 'R$ 105,00', 'C': 'R$ 96,00', 'D': 'R$ 108,00'}), 
             'A', 'Fácil', 
             'Correto. 15% de 120 é (15/100) * 120 = 18. O novo preço é 120 - 18 = 102.', 
             'Para calcular 15%, você pode calcular 10% (12) e somar com 5% (metade de 10%, ou 6). 12 + 6 = 18.', 
             'Valor Final = Valor Inicial * (1 - (Percentual / 100))'),
             
            ('Direito Constitucional', 'Direitos Fundamentais', 'Qual dos seguintes NÃO é um direito social previsto no Art. 6º da Constituição?', 
             json.dumps({'A': 'Educação', 'B': 'Saúde', 'C': 'Lazer', 'D': 'Propriedade'}), 
             'D', 'Média', 
             'Correto. A propriedade é um direito fundamental (Art. 5º, caput), mas não está listada no Art. 6º como um direito social.', 
             'O Art. 6º lista: educação, saúde, alimentação, trabalho, moradia, transporte, lazer, segurança, previdência social, proteção à maternidade e à infância, e assistência aos desamparados.', 
             'Art. 6º, CF/88'),
             
            ('Informática', 'Hardware', 'Qual componente é considerado o "cérebro" do computador?', 
             json.dumps({'A': 'HD (Disco Rígido)', 'B': 'Memória RAM', 'C': 'CPU (Unidade Central de Processamento)', 'D': 'Placa-mãe'}), 
             'C', 'Fácil', 
             'Correto. A CPU (Central Processing Unit) é responsável por executar a maioria das instruções e cálculos do computador.', 
             'Pense na CPU como o maestro de uma orquestra, coordenando todas as outras partes.', 
             None),

            ('Atualidades', 'Meio Ambiente', 'Qual o nome do acordo global assinado em 2015 com o objetivo de limitar o aquecimento global?',
             json.dumps({'A': 'Protocolo de Kyoto', 'B': 'Acordo de Paris', 'C': 'Tratado de Tordesilhas', 'D': 'Pacto Global pela Água'}),
             'B', 'Fácil',
             'Correto. O Acordo de Paris, estabelecido na COP21, tem como meta principal limitar o aumento da temperatura média global a bem menos de 2°C acima dos níveis pré-industriais, esforçando-se para limitá-lo a 1,5°C.',
             'O Protocolo de Kyoto foi um acordo anterior, de 1997. O Acordo de Paris é o principal pacto climático atual.',
             None),

            ('Direito Administrativo', 'Atos Administrativos', 'Qual atributo do ato administrativo permite que a Administração o execute imediatamente, sem precisar de ordem judicial?',
             json.dumps({'A': 'Presunção de Legitimidade', 'B': 'Imperatividade', 'C': 'Autoexecutoriedade', 'D': 'Tipicidade'}),
             'C', 'Média',
             'Correto. A autoexecutoriedade é o atributo que permite à Administração executar suas próprias decisões, como a demolição de uma obra irregular, sem precisar de autorização prévia do Judiciário.',
             'Enquanto a imperatividade *obriga* o particular a aceitar o ato, a autoexecutoriedade *executa* o ato à força.',
             None),

            ('Psicologia (Gestão)', 'Liderança', 'Qual estilo de liderança foca em inspirar e motivar a equipe para alcançar objetivos extraordinários, geralmente através do carisma e da visão do líder?',
             json.dumps({'A': 'Liderança Autocrática', 'B': 'Liderança Democrática', 'C': 'Liderança Laissez-faire', 'D': 'Liderança Transformacional'}),
             'D', 'Média',
             'Correto. A Liderança Transformacional inspira e motiva os seguidores a transcender seus próprios interesses pelo bem da organização.',
             'Pense em líderes que mudam a forma como as pessoas pensam, em vez de apenas dar ordens (Autocrático) ou deixar fazer (Laissez-faire).',
             None)
        ]
        
        cursor.executemany('''
            INSERT INTO questoes (disciplina, assunto, enunciado, alternativas, resposta_correta, dificuldade, justificativa, dica, formula)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', questoes)
        conn.commit()
        print(f"Adicionadas {len(questoes)} questões de exemplo.")
    else:
        print("Tabela 'questoes' já contém dados. Nenhum dado de exemplo foi inserido.")

    # Inserir Temas de Redação de Exemplo
    cursor.execute("SELECT COUNT(id) FROM temas_redacao")
    count_redacao = cursor.fetchone()[0]
    
    if count_redacao == 0:
        print("Inserindo dados de exemplo em 'temas_redacao'...")
        temas = [
            ('A persistência da violência contra a mulher na sociedade brasileira', 'Sociedade', 'Texto motivador sobre dados de feminicídio...', 'Aborde a Lei Maria da Penha e a cultura do machismo.'),
            ('Desafios da educação a distância no Brasil', 'Educação', 'Texto sobre a transição para o EAD na pandemia...', 'Discuta a exclusão digital e a qualidade do ensino.'),
            ('O impacto das "fake news" na democracia contemporânea', 'Tecnologia/Sociedade', 'Artigo sobre desinformação em eleições...', 'Analise o papel das redes sociais e possíveis soluções.'),
            ('Caminhos para combater a insegurança alimentar no Brasil', 'Direitos Humanos', 'Dados sobre o mapa da fome...', 'Relacione com desigualdade social e políticas públicas.'),
            ('A importância da preservação da Amazônia para o equilíbrio climático global', 'Meio Ambiente', 'Relatório sobre desmatamento e aquecimento global...', 'Destaque o papel do Brasil e a pressão internacional.'),
        ]
        
        cursor.executemany('''
            INSERT INTO temas_redacao (titulo, eixo_tematico, texto_motivador, dicas)
            VALUES (?, ?, ?, ?)
        ''', temas)
        conn.commit()
        print(f"Adicionados {len(temas)} temas de redação de exemplo.")
    else:
        print("Tabela 'temas_redacao' já contém dados.")

    conn.close()

if __name__ == '__main__':
    if os.path.exists(DATABASE):
        print(f"Banco de dados '{DATABASE}' já existe. Verificando tabelas...")
    else:
        print(f"Criando novo banco de dados: '{DATABASE}'")
    
    create_tables()
    insert_sample_data()
    print("Inicialização do banco de dados concluída.")
