import sqlite3
import json
import os
import csv
import sys

DATABASE = 'concurso.db'
CSV_FILENAME = 'questoes.csv' # O nome do seu arquivo

def get_db_connection():
    """Conexão com o banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return None

def criar_tabelas(cursor):
    """Cria as tabelas no padrão V3.0, garantindo a estrutura correta."""
    try:
        # Forçar a exclusão da tabela 'questoes' antiga para garantir o novo schema
        print("Garantindo o schema V3.0: Removendo tabela 'questoes' antiga (se existir)...")
        cursor.execute("DROP TABLE IF EXISTS questoes")
        print("Tabela 'questoes' antiga removida.")

        # Tabela de questões (padronizada V3.0)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disciplina TEXT NOT NULL,
                enunciado TEXT NOT NULL,
                alternativas TEXT NOT NULL, -- ARMAZENAR COMO JSON TEXT
                resposta_correta TEXT NOT NULL, -- Ex: "A", "B"
                dificuldade TEXT DEFAULT 'Médio',
                justificativa TEXT,
                dica TEXT,
                formula TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Outras tabelas do sistema V3.0
        cursor.execute("CREATE TABLE IF NOT EXISTS redacoes (id INTEGER PRIMARY KEY, titulo TEXT, tema TEXT, texto_base TEXT, dicas TEXT, criterios_avaliacao TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS historico_simulados (id INTEGER PRIMARY KEY, simulado_id TEXT UNIQUE, config TEXT, relatorio TEXT, data_inicio TIMESTAMP, data_fim TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS historico_redacoes (id INTEGER PRIMARY KEY, redacao_id INTEGER, texto_redacao TEXT, correcao TEXT, nota INTEGER, feedback TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (redacao_id) REFERENCES redacoes (id))")
        
        print("Tabelas V3.0 criadas/verificadas com sucesso.")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        raise # Propaga o erro para parar o script

def limpar_tabelas_antigas(cursor):
    """Limpa dados antigos para evitar duplicatas."""
    try:
        print("Limpando dados antigos das tabelas de histórico e redação...")
        cursor.execute("DELETE FROM redacoes")
        cursor.execute("DELETE FROM historico_simulados")
        cursor.execute("DELETE FROM historico_redacoes")
        print("Tabelas de histórico e redação limpas.")
    except Exception as e:
        print(f"Aviso: Erro ao limpar tabelas (podem não existir ainda): {e}")

def popular_questoes_do_csv(cursor):
    """Popula a tabela 'questoes' lendo o arquivo questoes.csv."""
    
    if not os.path.exists(CSV_FILENAME):
        print(f"--- ERRO ---")
        print(f"Arquivo '{CSV_FILENAME}' NÃO ENCONTRADO.")
        print("Por favor, certifique-se que o arquivo está na mesma pasta.")
        return 0

    questoes_inseridas = 0
    try:
        print(f"Abrindo '{CSV_FILENAME}' (codificação 'utf-8', delimitador ';')...")
        with open(CSV_FILENAME, mode='r', encoding='utf-8', newline='') as f:
            # Usar DictReader para ler usando os nomes das colunas
            reader = csv.DictReader(f, delimiter=';')
            
            print("Lendo CSV e inserindo questões no banco...")
            
            for row in reader:
                try:
                    # 1. Montar o JSON de alternativas
                    alternativas_dict = {
                        'A': row.get('alt_a'),
                        'B': row.get('alt_b'),
                        'C': row.get('alt_c'),
                        'D': row.get('alt_d')
                    }
                    # Remover alternativas vazias (se houver, ex: alt_e)
                    alternativas_dict = {k: v for k, v in alternativas_dict.items() if v}
                    
                    # 2. Encontrar a justificativa correta
                    gabarito = row.get('gabarito', '').upper()
                    justificativa = ""
                    if gabarito == 'A':
                        justificativa = row.get('just_a')
                    elif gabarito == 'B':
                        justificativa = row.get('just_b')
                    elif gabarito == 'C':
                        justificativa = row.get('just_c')
                    elif gabarito == 'D':
                        justificativa = row.get('just_d')
                    
                    # 3. Inserir no banco
                    cursor.execute('''
                        INSERT INTO questoes 
                        (disciplina, enunciado, alternativas, resposta_correta, dificuldade, justificativa, dica, formula)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('disciplina'),
                        row.get('enunciado'),
                        json.dumps(alternativas_dict), # Serializa o dict para JSON
                        gabarito,
                        row.get('dificuldade', 'Médio'),
                        justificativa,
                        row.get('dica_interpretacao'),
                        row.get('formula_aplicavel')
                    ))
                    questoes_inseridas += 1
                except Exception as e_row:
                    print(f"Erro ao processar linha {reader.line_num}: {e_row}")
                    print(f"Dados da linha com erro: {row}")

        print(f"Total de {questoes_inseridas} questões lidas e inseridas no banco.")
        return questoes_inseridas

    except UnicodeDecodeError:
        print("\n--- ERRO DE CODIFICAÇÃO ---")
        print("Falha ao ler o CSV com 'utf-8'.")
        print("Se seu arquivo foi salvo pelo Excel, tente salvá-lo como 'CSV UTF-8 (delimitado por vírgulas)'")
        return 0
    except Exception as e:
        print(f"\n--- ERRO AO LER O CSV ---")
        print(f"Ocorreu um erro: {e}")
        return 0

def popular_redacoes(cursor):
    """Popula a tabela de redações com temas de exemplo (opcional)."""
    try:
        temas_redacao = [
            {'titulo': 'Desafios da Saúde Mental', 'tema': 'Os desafios para a garantia da saúde mental na sociedade brasileira.', 'dicas': 'Aborde o estigma e o acesso a tratamento.'},
            {'titulo': 'Inteligência Artificial', 'tema': 'O impacto da Inteligência Artificial no mercado de trabalho.', 'dicas': 'Discuta a requalificação profissional.'},
            {'titulo': 'Sustentabilidade Urbana', 'tema': 'Caminhos para a construção de cidades mais sustentáveis.', 'dicas': 'Explore soluções como transporte e reciclagem.'}
        ]
        
        print(f"Inserindo {len(temas_redacao)} temas de redação de exemplo...")
        for t in temas_redacao:
            cursor.execute('''
                INSERT INTO redacoes (titulo, tema, texto_base, dicas)
                VALUES (?, ?, ?, ?)
            ''', (t['titulo'], t['tema'], t.get('texto_base', ''), t['dicas']))
        print("Temas de redação inseridos com sucesso.")
        return len(temas_redacao)
    except Exception as e:
        print(f"Erro ao inserir temas de redação: {e}")
        return 0

# --- EXECUÇÃO PRINCIPAL ---
def main():
    print(f"--- Iniciando o script de 'seed' para o banco '{DATABASE}' ---")
    
    conn = get_db_connection()
    if not conn:
        sys.exit(1) # Sai se não conseguir conectar

    cursor = conn.cursor()
    
    try:
        # 1. Recria as tabelas (DROP + CREATE)
        criar_tabelas(cursor)
        
        # 2. Limpa tabelas de histórico
        limpar_tabelas_antigas(cursor)
        
        # 3. Popula com seu CSV
        total_q = popular_questoes_do_csv(cursor)
        
        # 4. Popula com redações de exemplo
        total_r = popular_redacoes(cursor)
        
        # 5. Salvar (Commit)
        conn.commit()
        print("\n" + "="*40)
        print("--- SUCESSO! ---")
        print("O banco de dados foi populado com seus dados.")
        print(f"Total de questões inseridas: {total_q}")
        print(f"Total de temas de redação: {total_r}")
        print("="*40)

    except Exception as e:
        print(f"\n--- ERRO GERAL ---")
        print(f"Ocorreu um erro na transação: {e}")
        conn.rollback() # Desfaz qualquer mudança se houver erro
    finally:
        conn.close()
        print(f"Conexão com '{DATABASE}' fechada.")

if __name__ == "__main__":
    main()
