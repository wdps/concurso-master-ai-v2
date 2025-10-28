import sqlite3
import csv
import json
import os
import sys
import re

print("--- INICIANDO SCRIPT DE IMPORTAÃ‡ÃƒO E ATUALIZAÃ‡ÃƒO DO BANCO (V4 - Colunas Corrigidas) ---")

# Lista de 50 temas (mantida igual)
temas_redacao_lista = [
    ("A persistÃªncia da violÃªncia contra a mulher na sociedade brasileira", "DissertaÃ§Ã£o", "DifÃ­cil"), ("Desafios para a valorizaÃ§Ã£o de comunidades e povos tradicionais no Brasil", "DissertaÃ§Ã£o", "DifÃ­cil"),
    ("Invisibilidade e registro civil: garantia de acesso Ã  cidadania no Brasil", "DissertaÃ§Ã£o", "MÃ©dio"), ("O estigma associado Ã s doenÃ§as mentais na sociedade brasileira", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("DemocratizaÃ§Ã£o do acesso ao cinema no Brasil", "DissertaÃ§Ã£o", "FÃ¡cil"), ("ManipulaÃ§Ã£o do comportamento do usuÃ¡rio pelo controle de dados na internet", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("Os desafios da educaÃ§Ã£o digital para jovens e crianÃ§as no sÃ©culo XXI", "DissertaÃ§Ã£o", "MÃ©dio"), ("O impacto da 'cultura do cancelamento' nas relaÃ§Ãµes sociais", "DissertaÃ§Ã£o", "DifÃ­cil"),
    ("Caminhos para combater a intolerÃ¢ncia religiosa no Brasil", "DissertaÃ§Ã£o", "MÃ©dio"), ("A importÃ¢ncia da preservaÃ§Ã£o do patrimÃ´nio histÃ³rico-cultural", "DissertaÃ§Ã£o", "FÃ¡cil"),
    ("Desafios para a implementaÃ§Ã£o da mobilidade urbana sustentÃ¡vel no Brasil", "DissertaÃ§Ã£o", "MÃ©dio"), ("O papel da ciÃªncia e tecnologia no desenvolvimento social", "DissertaÃ§Ã£o", "FÃ¡cil"),
    ("A questÃ£o do desperdÃ­cio de alimentos e a fome no Brasil", "DissertaÃ§Ã£o", "MÃ©dio"), ("Impactos da inteligÃªncia artificial no mercado de trabalho", "DissertaÃ§Ã£o", "DifÃ­cil"),
    ("A crise hÃ­drica e a necessidade de uso consciente da Ã¡gua", "DissertaÃ§Ã£o", "FÃ¡cil"), ("Os efeitos da superexposiÃ§Ã£o Ã s redes sociais na saÃºde mental", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("A inclusÃ£o de pessoas com deficiÃªncia (PCD) no mercado de trabalho", "DissertaÃ§Ã£o", "MÃ©dio"), ("A problemÃ¡tica do lixo eletrÃ´nico na sociedade contemporÃ¢nea", "DissertaÃ§Ã£o", "FÃ¡cil"),
    ("Fake news: como combater a desinformaÃ§Ã£o e seu impacto na democracia", "DissertaÃ§Ã£o", "MÃ©dio"), ("A valorizaÃ§Ã£o do esporte como ferramenta de inclusÃ£o social", "DissertaÃ§Ã£o", "FÃ¡cil"),
    ("Os desafios do sistema carcerÃ¡rio brasileiro", "DissertaÃ§Ã£o", "DifÃ­cil"), ("EvasÃ£o escolar em questÃ£o no Brasil", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("A exploraÃ§Ã£o do trabalho infantil e seus reflexos sociais", "DissertaÃ§Ã£o", "MÃ©dio"), ("O acesso Ã  moradia digna como um direito fundamental", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("A importÃ¢ncia da vacinaÃ§Ã£o para a saÃºde pÃºblica", "DissertaÃ§Ã£o", "FÃ¡cil"), ("Consumismo e seus impactos no meio ambiente", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("A luta contra o etarismo (preconceito contra idosos) no Brasil", "DissertaÃ§Ã£o", "MÃ©dio"), ("O papel da leitura na formaÃ§Ã£o crÃ­tica do indivÃ­duo", "DissertaÃ§Ã£o", "FÃ¡cil"),
    ("Desafios para garantir a seguranÃ§a alimentar da populaÃ§Ã£o", "DissertaÃ§Ã£o", "MÃ©dio"), ("A importÃ¢ncia do Sistema Ãšnico de SaÃºde (SUS) para o Brasil", "DissertaÃ§Ã£o", "FÃ¡cil"),
    ("Impactos do desmatamento na AmazÃ´nia para o equilÃ­brio global", "DissertaÃ§Ã£o", "DifÃ­cil"), ("A gravidez na adolescÃªncia como um problema de saÃºde pÃºblica", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("AdoÃ§Ã£o de crianÃ§as e adolescentes no Brasil: entraves e perspectivas", "DissertaÃ§Ã£o", "MÃ©dio"), ("A gentrificaÃ§Ã£o e seus efeitos nos centros urbanos", "DissertaÃ§Ã£o", "DifÃ­cil"),
    ("O combate ao trÃ¡fico de animais silvestres", "DissertaÃ§Ã£o", "MÃ©dio"), ("A importÃ¢ncia da representatividade na mÃ­dia e na polÃ­tica", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("A crise dos refugiados e a xenofobia no sÃ©culo XXI", "DissertaÃ§Ã£o", "DifÃ­cil"), ("O analfabetismo funcional como um obstÃ¡culo ao desenvolvimento", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("Adoecimento mental no ambiente de trabalho (SÃ­ndrome de Burnout)", "DissertaÃ§Ã£o", "MÃ©dio"), ("A cultura da meritocracia e a desigualdade de oportunidades", "DissertaÃ§Ã£o", "DifÃ­cil"),
    ("O papel da famÃ­lia na educaÃ§Ã£o e formaÃ§Ã£o dos jovens", "DissertaÃ§Ã£o", "FÃ¡cil"), ("A obsolescÃªncia programada e seus impactos na sociedade de consumo", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("A importÃ¢ncia da demarcaÃ§Ã£o de terras indÃ­genas", "DissertaÃ§Ã£o", "DifÃ­cil"), ("O desafio de combater o bullying e o cyberbullying nas escolas", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("A precarizaÃ§Ã£o do trabalho plataformizado (motoristas de aplicativo, entregadores)", "DissertaÃ§Ã£o", "DifÃ­cil"), ("O uso de agrotÃ³xicos e seus impactos na saÃºde e meio ambiente", "DissertaÃ§Ã£o", "MÃ©dio"),
    ("A importÃ¢ncia da participaÃ§Ã£o polÃ­tica para a democracia", "DissertaÃ§Ã£o", "FÃ¡cil"), ("Os desafios da inclusÃ£o digital da terceira idade", "DissertaÃ§Ã£o", "FÃ¡cil"),
    ("A questÃ£o da pirataria e a propriedade intelectual na era digital", "DissertaÃ§Ã£o", "MÃ©dio"), ("Voluntariado: um caminho para a transformaÃ§Ã£o social", "DissertaÃ§Ã£o", "FÃ¡cil")
]

def conectar_banco():
    try: conn = sqlite3.connect('concurso.db'); conn.row_factory = sqlite3.Row; print("ConexÃ£o estabelecida."); return conn
    except Exception as e: print(f"ERRO FATAL ao conectar: {e}"); return None

def atualizar_estrutura_banco(conn):
    print("Verificando/Atualizando estrutura...");
    try:
        cursor = conn.cursor()
        # Cria tabelas (esquema completo)
        cursor.execute('''CREATE TABLE IF NOT EXISTS questoes (id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT NOT NULL, materia TEXT NOT NULL, enunciado TEXT NOT NULL, alternativas TEXT NOT NULL, resposta_correta TEXT NOT NULL, dificuldade TEXT DEFAULT 'MÃ©dio', justificativa TEXT, dica TEXT, formula TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, peso INTEGER DEFAULT 1 ) ''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS temas_redacao (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, descricao TEXT, tipo TEXT NOT NULL, dificuldade TEXT DEFAULT 'MÃ©dio', palavras_chave TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ) ''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS historico_simulados (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, simulado_id TEXT NOT NULL UNIQUE, config TEXT NOT NULL, respostas TEXT NOT NULL, relatorio TEXT NOT NULL, data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP, data_fim TIMESTAMP, tempo_total_minutos REAL DEFAULT 0 ) ''')
        # Adiciona colunas faltantes a 'questoes'
        cursor.execute("PRAGMA table_info(questoes)"); cols_q = [c[1] for c in cursor.fetchall()]
        if 'peso' not in cols_q: cursor.execute("ALTER TABLE questoes ADD COLUMN peso INTEGER DEFAULT 1"); print("   Coluna 'peso' adicionada.")
        if 'justificativa' not in cols_q: cursor.execute("ALTER TABLE questoes ADD COLUMN justificativa TEXT"); print("   Coluna 'justificativa' adicionada.")
        if 'dica' not in cols_q: cursor.execute("ALTER TABLE questoes ADD COLUMN dica TEXT"); print("   Coluna 'dica' adicionada.")
        if 'formula' not in cols_q: cursor.execute("ALTER TABLE questoes ADD COLUMN formula TEXT"); print("   Coluna 'formula' adicionada.")
        conn.commit(); print("Estrutura OK.")
    except Exception as e: print(f"ERRO ao atualizar estrutura: {e}")

def importar_questoes_csv(conn):
    print("\n--- Iniciando ImportaÃ§Ã£o 'questoes.csv' (V4 - Colunas Corrigidas) ---")
    csv_file = 'questoes.csv'
    if not os.path.exists(csv_file): print(f"ERRO FATAL: '{csv_file}' nÃ£o encontrado!"); return 0, 0
    cursor = conn.cursor(); print("Limpando 'questoes'...");
    try: cursor.execute("DELETE FROM questoes"); cursor.execute("DELETE FROM sqlite_sequence WHERE name='questoes'"); conn.commit(); print("'questoes' limpa.")
    except Exception as e: print(f"ERRO ao limpar 'questoes': {e}"); return 0, 0
    sucesso_count = 0; falha_count = 0; linhas_total = 0
    try:
        # DetecÃ§Ã£o de Encoding
        encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1']; detected_encoding = None
        for enc in encodings_to_try:
             try:
                 with open(csv_file, mode='r', encoding=enc) as file: file.read(1024)
                 detected_encoding = enc; print(f"Encoding: {detected_encoding}"); break
             except UnicodeDecodeError: continue
             except Exception as e_enc: print(f"Erro teste {enc}: {e_enc}")
        if not detected_encoding: print("ERRO FATAL: Encoding nÃ£o detectado."); return 0, 0
        
        with open(csv_file, mode='r', encoding=detected_encoding) as file:
            # DetecÃ§Ã£o de Delimitador
            try: sample = file.read(4096); dialect = csv.Sniffer().sniff(sample, delimiters=';,'); print(f"Delimitador: '{dialect.delimiter}'")
            except csv.Error:
                 print("AVISO: Sniffer falhou. Verificando ';' vs ','..."); file.seek(0); first_line = file.readline()
                 if first_line.count(';') >= first_line.count(','): dialect = csv.excel; dialect.delimiter = ';'; print("Assumindo: ';'")
                 else: dialect = csv.excel; dialect.delimiter = ','; print("Assumindo: ','")
            
            file.seek(0); reader = csv.DictReader(file, dialect=dialect)
            colunas = reader.fieldnames
            if not colunas: print("ERRO FATAL: CSV vazio/colunas nÃ£o lidas."); return 0, 0
            print(f"Colunas CSV: {colunas}")

            # *** CORREÃ‡ÃƒO PRINCIPAL: AJUSTE DO MAPEAMENTO ***
            mapa_colunas = {
                'disciplina': next((c for c in colunas if 'disciplina' in c.lower()), None),
                'materia': next((c for c in colunas if 'assunto' in c.lower()), None), # Ajustado para 'assunto'
                'enunciado': next((c for c in colunas if 'enunciado' in c.lower()), None),
                # Alternativas serÃ£o tratadas separadamente abaixo
                'resposta_correta': next((c for c in colunas if 'gabarito' in c.lower()), None), # Ajustado para 'gabarito'
                'dificuldade': next((c for c in colunas if 'dificuldade' in c.lower()), None),
                # Mapeia justificativas individuais para um campo geral (pega a primeira nÃ£o vazia)
                'justificativa': next((c for c in colunas if 'just_' in c.lower()), None),
                'dica': next((c for c in colunas if 'dica' in c.lower()), None),
                'formula': next((c for c in colunas if 'formula' in c.lower()), None),
                'peso': next((c for c in colunas if 'peso' in c.lower()), None),
                # Guarda os nomes das colunas de alternativas
                'alt_a': next((c for c in colunas if c.lower() == 'alt_a'), None),
                'alt_b': next((c for c in colunas if c.lower() == 'alt_b'), None),
                'alt_c': next((c for c in colunas if c.lower() == 'alt_c'), None),
                'alt_d': next((c for c in colunas if c.lower() == 'alt_d'), None),
                 # Adicione alt_e se necessÃ¡rio
                'alt_e': next((c for c in colunas if c.lower() == 'alt_e'), None),
            }

            # Verifica colunas essenciais *AJUSTADAS*
            essenciais_ajustadas = ['disciplina', 'materia', 'enunciado', 'resposta_correta', 'alt_a', 'alt_b'] # Precisa ter pelo menos A e B
            if any(mapa_colunas[key] is None for key in essenciais_ajustadas):
                print(f"ERRO FATAL: Colunas essenciais ajustadas ({', '.join(essenciais_ajustadas)}) nÃ£o encontradas.")
                print(f"Mapeamento: {mapa_colunas}")
                return 0, 0
            print("Mapeamento ajustado OK.")

            questoes_para_inserir = []; print("\n--- Processando linhas ---")
            for i, row in enumerate(reader):
                linhas_total += 1; print(f"  Linha {i+2}: Processando...")
                try:
                    # ** Monta o dicionÃ¡rio de alternativas a partir das colunas alt_X **
                    alt_dict = {}
                    if mapa_colunas['alt_a'] and row.get(mapa_colunas['alt_a']): alt_dict['A'] = row[mapa_colunas['alt_a']].strip()
                    if mapa_colunas['alt_b'] and row.get(mapa_colunas['alt_b']): alt_dict['B'] = row[mapa_colunas['alt_b']].strip()
                    if mapa_colunas['alt_c'] and row.get(mapa_colunas['alt_c']): alt_dict['C'] = row[mapa_colunas['alt_c']].strip()
                    if mapa_colunas['alt_d'] and row.get(mapa_colunas['alt_d']): alt_dict['D'] = row[mapa_colunas['alt_d']].strip()
                    if mapa_colunas['alt_e'] and row.get(mapa_colunas['alt_e']): alt_dict['E'] = row[mapa_colunas['alt_e']].strip() # Adicionado E

                    if len(alt_dict) < 2: # Precisa ter pelo menos A e B
                        raise ValueError(f"Menos de duas alternativas encontradas nas colunas alt_a, alt_b...: {alt_dict}")
                    alternativas_json = json.dumps(alt_dict, ensure_ascii=False)

                    # Tenta pegar a primeira justificativa nÃ£o vazia das colunas just_X
                    justificativa_texto = ""
                    for col_just in [c for c in colunas if 'just_' in c.lower()]:
                         if row.get(col_just):
                             justificativa_texto = row[col_just].strip()
                             break # Pega a primeira que encontrar

                    try: peso_valor = int(row.get(mapa_colunas.get('peso'), 1) or 1)
                    except (ValueError, TypeError): peso_valor = 1

                    q = ( row.get(mapa_colunas['disciplina'], '').strip(),
                          row.get(mapa_colunas['materia'], '').strip(), # Usa 'materia' (que mapeou para 'assunto')
                          row.get(mapa_colunas['enunciado'], '').strip(),
                          alternativas_json, # JSON montado acima
                          row.get(mapa_colunas['resposta_correta'], '').strip().upper(), # Usa 'resposta_correta' (que mapeou para 'gabarito')
                          row.get(mapa_colunas.get('dificuldade'), 'MÃ©dio').strip().capitalize(),
                          justificativa_texto, # Justificativa encontrada
                          row.get(mapa_colunas.get('dica'), '').strip(),
                          row.get(mapa_colunas.get('formula'), '').strip(),
                          peso_valor )

                    # ValidaÃ§Ã£o final (primeiros 5 campos nÃ£o podem ser vazios)
                    if not all(str(field).strip() for field in q[:5]):
                        raise ValueError(f"Dados essenciais ausentes ou vazios apÃ³s processamento: {q[:5]}")

                    questoes_para_inserir.append(q); print(f"      OK: Linha {i+2} processada."); sucesso_count += 1
                except (ValueError, TypeError, json.JSONDecodeError, KeyError) as e_row: print(f"      ERRO DETALHADO linha {i+2}: {e_row}\n      Dados: {row}"); falha_count += 1
                except Exception as e_inesperado: print(f"      ERRO GRAVE linha {i+2}: {e_inesperado}"); falha_count += 1
            
            print("\n--- Fim do Processamento ---")
            if not questoes_para_inserir: print("\nERRO GRAVE: Nenhuma questÃ£o processada!"); return sucesso_count, falha_count
            print(f"\nInserindo {len(questoes_para_inserir)} questÃµes...");
            cursor.executemany('INSERT INTO questoes (disciplina, materia, enunciado, alternativas, resposta_correta, dificuldade, justificativa, dica, formula, peso) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', questoes_para_inserir)
            conn.commit(); print("InserÃ§Ã£o concluÃ­da.")
    except FileNotFoundError: print(f"ERRO FATAL: '{csv_file}' nÃ£o encontrado.")
    except Exception as e: print(f"ERRO GERAL CSV: {e}"); sys.exit(1) # Sai se der erro geral
    finally:
        print("\n--- Resumo ImportaÃ§Ã£o QuestÃµes ---"); print(f"Linhas lidas: {linhas_total}"); print(f"SUCESSO: {sucesso_count}"); print(f"ERRO: {falha_count}"); return sucesso_count, falha_count

def importar_temas_redacao(conn):
    print("\n--- Iniciando ImportaÃ§Ã£o Temas ---")
    try:
        cursor = conn.cursor(); cursor.execute("DELETE FROM temas_redacao"); cursor.execute("DELETE FROM sqlite_sequence WHERE name='temas_redacao'"); conn.commit();
        temas_para_inserir = []
        for titulo, tipo, dificuldade in temas_redacao_lista:
            descricao = f"Desenvolva um texto dissertativo-argumentativo sobre o tema: '{titulo}'."; palavras_chave = ', '.join(titulo.lower().split(' ')[1:4])
            temas_para_inserir.append((titulo, descricao, tipo, dificuldade, palavras_chave))
        cursor.executemany('INSERT INTO temas_redacao (titulo, descricao, tipo, dificuldade, palavras_chave) VALUES (?, ?, ?, ?, ?)', temas_para_inserir)
        conn.commit(); print(f"Sucesso! {len(temas_para_inserir)} temas importados."); return len(temas_para_inserir)
    except Exception as e: print(f"Erro ao importar temas: {e}"); return 0

if __name__ == "__main__":
    conn = conectar_banco()
    if conn:
        atualizar_estrutura_banco(conn)
        questoes_ok, questoes_falha = importar_questoes_csv(conn)
        temas_ok = importar_temas_redacao(conn)
        conn.close()
        print("\n--- IMPORTAÃ‡ÃƒO FINALIZADA ---")
        if questoes_ok == 0: print("\n!!! ALERTA MÃXIMO: NENHUMA QUESTÃƒO IMPORTADA !!!")
        elif questoes_falha > 0: print(f"\nAVISO: {questoes_falha} linha(s) do CSV tiveram erro.")
        else: print("\nOK: QuestÃµes importadas.")
        if temas_ok == 50: print("OK: Temas importados.")
        else: print("AVISO: Problema nos temas.")
    else: print("ImportaÃ§Ã£o falhou: Sem conexÃ£o com DB.")

