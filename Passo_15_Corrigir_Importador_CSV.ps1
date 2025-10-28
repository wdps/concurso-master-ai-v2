# Passo 15 (Correção Final): Ajustando 'importar_dados.py' para as colunas do seu CSV

Write-Host "🚀 Iniciando Passo 15: Ajustando 'importar_dados.py' para ler 'assunto', 'alt_a'-'d', 'gabarito'..." -ForegroundColor Cyan

# Conteúdo CORRIGIDO FINAL do script Python 'importar_dados.py'
$pythonScriptContentFinal = @'
import sqlite3
import csv
import json
import os
import sys
import re

print("--- INICIANDO SCRIPT DE IMPORTAÇÃO E ATUALIZAÇÃO DO BANCO (V4 - Colunas Corrigidas) ---")

# Lista de 50 temas (mantida igual)
temas_redacao_lista = [
    ("A persistência da violência contra a mulher na sociedade brasileira", "Dissertação", "Difícil"), ("Desafios para a valorização de comunidades e povos tradicionais no Brasil", "Dissertação", "Difícil"),
    ("Invisibilidade e registro civil: garantia de acesso à cidadania no Brasil", "Dissertação", "Médio"), ("O estigma associado às doenças mentais na sociedade brasileira", "Dissertação", "Médio"),
    ("Democratização do acesso ao cinema no Brasil", "Dissertação", "Fácil"), ("Manipulação do comportamento do usuário pelo controle de dados na internet", "Dissertação", "Médio"),
    ("Os desafios da educação digital para jovens e crianças no século XXI", "Dissertação", "Médio"), ("O impacto da 'cultura do cancelamento' nas relações sociais", "Dissertação", "Difícil"),
    ("Caminhos para combater a intolerância religiosa no Brasil", "Dissertação", "Médio"), ("A importância da preservação do patrimônio histórico-cultural", "Dissertação", "Fácil"),
    ("Desafios para a implementação da mobilidade urbana sustentável no Brasil", "Dissertação", "Médio"), ("O papel da ciência e tecnologia no desenvolvimento social", "Dissertação", "Fácil"),
    ("A questão do desperdício de alimentos e a fome no Brasil", "Dissertação", "Médio"), ("Impactos da inteligência artificial no mercado de trabalho", "Dissertação", "Difícil"),
    ("A crise hídrica e a necessidade de uso consciente da água", "Dissertação", "Fácil"), ("Os efeitos da superexposição às redes sociais na saúde mental", "Dissertação", "Médio"),
    ("A inclusão de pessoas com deficiência (PCD) no mercado de trabalho", "Dissertação", "Médio"), ("A problemática do lixo eletrônico na sociedade contemporânea", "Dissertação", "Fácil"),
    ("Fake news: como combater a desinformação e seu impacto na democracia", "Dissertação", "Médio"), ("A valorização do esporte como ferramenta de inclusão social", "Dissertação", "Fácil"),
    ("Os desafios do sistema carcerário brasileiro", "Dissertação", "Difícil"), ("Evasão escolar em questão no Brasil", "Dissertação", "Médio"),
    ("A exploração do trabalho infantil e seus reflexos sociais", "Dissertação", "Médio"), ("O acesso à moradia digna como um direito fundamental", "Dissertação", "Médio"),
    ("A importância da vacinação para a saúde pública", "Dissertação", "Fácil"), ("Consumismo e seus impactos no meio ambiente", "Dissertação", "Médio"),
    ("A luta contra o etarismo (preconceito contra idosos) no Brasil", "Dissertação", "Médio"), ("O papel da leitura na formação crítica do indivíduo", "Dissertação", "Fácil"),
    ("Desafios para garantir a segurança alimentar da população", "Dissertação", "Médio"), ("A importância do Sistema Único de Saúde (SUS) para o Brasil", "Dissertação", "Fácil"),
    ("Impactos do desmatamento na Amazônia para o equilíbrio global", "Dissertação", "Difícil"), ("A gravidez na adolescência como um problema de saúde pública", "Dissertação", "Médio"),
    ("Adoção de crianças e adolescentes no Brasil: entraves e perspectivas", "Dissertação", "Médio"), ("A gentrificação e seus efeitos nos centros urbanos", "Dissertação", "Difícil"),
    ("O combate ao tráfico de animais silvestres", "Dissertação", "Médio"), ("A importância da representatividade na mídia e na política", "Dissertação", "Médio"),
    ("A crise dos refugiados e a xenofobia no século XXI", "Dissertação", "Difícil"), ("O analfabetismo funcional como um obstáculo ao desenvolvimento", "Dissertação", "Médio"),
    ("Adoecimento mental no ambiente de trabalho (Síndrome de Burnout)", "Dissertação", "Médio"), ("A cultura da meritocracia e a desigualdade de oportunidades", "Dissertação", "Difícil"),
    ("O papel da família na educação e formação dos jovens", "Dissertação", "Fácil"), ("A obsolescência programada e seus impactos na sociedade de consumo", "Dissertação", "Médio"),
    ("A importância da demarcação de terras indígenas", "Dissertação", "Difícil"), ("O desafio de combater o bullying e o cyberbullying nas escolas", "Dissertação", "Médio"),
    ("A precarização do trabalho plataformizado (motoristas de aplicativo, entregadores)", "Dissertação", "Difícil"), ("O uso de agrotóxicos e seus impactos na saúde e meio ambiente", "Dissertação", "Médio"),
    ("A importância da participação política para a democracia", "Dissertação", "Fácil"), ("Os desafios da inclusão digital da terceira idade", "Dissertação", "Fácil"),
    ("A questão da pirataria e a propriedade intelectual na era digital", "Dissertação", "Médio"), ("Voluntariado: um caminho para a transformação social", "Dissertação", "Fácil")
]

def conectar_banco():
    try: conn = sqlite3.connect('concurso.db'); conn.row_factory = sqlite3.Row; print("Conexão estabelecida."); return conn
    except Exception as e: print(f"ERRO FATAL ao conectar: {e}"); return None

def atualizar_estrutura_banco(conn):
    print("Verificando/Atualizando estrutura...");
    try:
        cursor = conn.cursor()
        # Cria tabelas (esquema completo)
        cursor.execute('''CREATE TABLE IF NOT EXISTS questoes (id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT NOT NULL, materia TEXT NOT NULL, enunciado TEXT NOT NULL, alternativas TEXT NOT NULL, resposta_correta TEXT NOT NULL, dificuldade TEXT DEFAULT 'Médio', justificativa TEXT, dica TEXT, formula TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, peso INTEGER DEFAULT 1 ) ''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS temas_redacao (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, descricao TEXT, tipo TEXT NOT NULL, dificuldade TEXT DEFAULT 'Médio', palavras_chave TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ) ''')
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
    print("\n--- Iniciando Importação 'questoes.csv' (V4 - Colunas Corrigidas) ---")
    csv_file = 'questoes.csv'
    if not os.path.exists(csv_file): print(f"ERRO FATAL: '{csv_file}' não encontrado!"); return 0, 0
    cursor = conn.cursor(); print("Limpando 'questoes'...");
    try: cursor.execute("DELETE FROM questoes"); cursor.execute("DELETE FROM sqlite_sequence WHERE name='questoes'"); conn.commit(); print("'questoes' limpa.")
    except Exception as e: print(f"ERRO ao limpar 'questoes': {e}"); return 0, 0
    sucesso_count = 0; falha_count = 0; linhas_total = 0
    try:
        # Detecção de Encoding
        encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1']; detected_encoding = None
        for enc in encodings_to_try:
             try:
                 with open(csv_file, mode='r', encoding=enc) as file: file.read(1024)
                 detected_encoding = enc; print(f"Encoding: {detected_encoding}"); break
             except UnicodeDecodeError: continue
             except Exception as e_enc: print(f"Erro teste {enc}: {e_enc}")
        if not detected_encoding: print("ERRO FATAL: Encoding não detectado."); return 0, 0
        
        with open(csv_file, mode='r', encoding=detected_encoding) as file:
            # Detecção de Delimitador
            try: sample = file.read(4096); dialect = csv.Sniffer().sniff(sample, delimiters=';,'); print(f"Delimitador: '{dialect.delimiter}'")
            except csv.Error:
                 print("AVISO: Sniffer falhou. Verificando ';' vs ','..."); file.seek(0); first_line = file.readline()
                 if first_line.count(';') >= first_line.count(','): dialect = csv.excel; dialect.delimiter = ';'; print("Assumindo: ';'")
                 else: dialect = csv.excel; dialect.delimiter = ','; print("Assumindo: ','")
            
            file.seek(0); reader = csv.DictReader(file, dialect=dialect)
            colunas = reader.fieldnames
            if not colunas: print("ERRO FATAL: CSV vazio/colunas não lidas."); return 0, 0
            print(f"Colunas CSV: {colunas}")

            # *** CORREÇÃO PRINCIPAL: AJUSTE DO MAPEAMENTO ***
            mapa_colunas = {
                'disciplina': next((c for c in colunas if 'disciplina' in c.lower()), None),
                'materia': next((c for c in colunas if 'assunto' in c.lower()), None), # Ajustado para 'assunto'
                'enunciado': next((c for c in colunas if 'enunciado' in c.lower()), None),
                # Alternativas serão tratadas separadamente abaixo
                'resposta_correta': next((c for c in colunas if 'gabarito' in c.lower()), None), # Ajustado para 'gabarito'
                'dificuldade': next((c for c in colunas if 'dificuldade' in c.lower()), None),
                # Mapeia justificativas individuais para um campo geral (pega a primeira não vazia)
                'justificativa': next((c for c in colunas if 'just_' in c.lower()), None),
                'dica': next((c for c in colunas if 'dica' in c.lower()), None),
                'formula': next((c for c in colunas if 'formula' in c.lower()), None),
                'peso': next((c for c in colunas if 'peso' in c.lower()), None),
                # Guarda os nomes das colunas de alternativas
                'alt_a': next((c for c in colunas if c.lower() == 'alt_a'), None),
                'alt_b': next((c for c in colunas if c.lower() == 'alt_b'), None),
                'alt_c': next((c for c in colunas if c.lower() == 'alt_c'), None),
                'alt_d': next((c for c in colunas if c.lower() == 'alt_d'), None),
                 # Adicione alt_e se necessário
                'alt_e': next((c for c in colunas if c.lower() == 'alt_e'), None),
            }

            # Verifica colunas essenciais *AJUSTADAS*
            essenciais_ajustadas = ['disciplina', 'materia', 'enunciado', 'resposta_correta', 'alt_a', 'alt_b'] # Precisa ter pelo menos A e B
            if any(mapa_colunas[key] is None for key in essenciais_ajustadas):
                print(f"ERRO FATAL: Colunas essenciais ajustadas ({', '.join(essenciais_ajustadas)}) não encontradas.")
                print(f"Mapeamento: {mapa_colunas}")
                return 0, 0
            print("Mapeamento ajustado OK.")

            questoes_para_inserir = []; print("\n--- Processando linhas ---")
            for i, row in enumerate(reader):
                linhas_total += 1; print(f"  Linha {i+2}: Processando...")
                try:
                    # ** Monta o dicionário de alternativas a partir das colunas alt_X **
                    alt_dict = {}
                    if mapa_colunas['alt_a'] and row.get(mapa_colunas['alt_a']): alt_dict['A'] = row[mapa_colunas['alt_a']].strip()
                    if mapa_colunas['alt_b'] and row.get(mapa_colunas['alt_b']): alt_dict['B'] = row[mapa_colunas['alt_b']].strip()
                    if mapa_colunas['alt_c'] and row.get(mapa_colunas['alt_c']): alt_dict['C'] = row[mapa_colunas['alt_c']].strip()
                    if mapa_colunas['alt_d'] and row.get(mapa_colunas['alt_d']): alt_dict['D'] = row[mapa_colunas['alt_d']].strip()
                    if mapa_colunas['alt_e'] and row.get(mapa_colunas['alt_e']): alt_dict['E'] = row[mapa_colunas['alt_e']].strip() # Adicionado E

                    if len(alt_dict) < 2: # Precisa ter pelo menos A e B
                        raise ValueError(f"Menos de duas alternativas encontradas nas colunas alt_a, alt_b...: {alt_dict}")
                    alternativas_json = json.dumps(alt_dict, ensure_ascii=False)

                    # Tenta pegar a primeira justificativa não vazia das colunas just_X
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
                          row.get(mapa_colunas.get('dificuldade'), 'Médio').strip().capitalize(),
                          justificativa_texto, # Justificativa encontrada
                          row.get(mapa_colunas.get('dica'), '').strip(),
                          row.get(mapa_colunas.get('formula'), '').strip(),
                          peso_valor )

                    # Validação final (primeiros 5 campos não podem ser vazios)
                    if not all(str(field).strip() for field in q[:5]):
                        raise ValueError(f"Dados essenciais ausentes ou vazios após processamento: {q[:5]}")

                    questoes_para_inserir.append(q); print(f"      OK: Linha {i+2} processada."); sucesso_count += 1
                except (ValueError, TypeError, json.JSONDecodeError, KeyError) as e_row: print(f"      ERRO DETALHADO linha {i+2}: {e_row}\n      Dados: {row}"); falha_count += 1
                except Exception as e_inesperado: print(f"      ERRO GRAVE linha {i+2}: {e_inesperado}"); falha_count += 1
            
            print("\n--- Fim do Processamento ---")
            if not questoes_para_inserir: print("\nERRO GRAVE: Nenhuma questão processada!"); return sucesso_count, falha_count
            print(f"\nInserindo {len(questoes_para_inserir)} questões...");
            cursor.executemany('INSERT INTO questoes (disciplina, materia, enunciado, alternativas, resposta_correta, dificuldade, justificativa, dica, formula, peso) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', questoes_para_inserir)
            conn.commit(); print("Inserção concluída.")
    except FileNotFoundError: print(f"ERRO FATAL: '{csv_file}' não encontrado.")
    except Exception as e: print(f"ERRO GERAL CSV: {e}"); sys.exit(1) # Sai se der erro geral
    finally:
        print("\n--- Resumo Importação Questões ---"); print(f"Linhas lidas: {linhas_total}"); print(f"SUCESSO: {sucesso_count}"); print(f"ERRO: {falha_count}"); return sucesso_count, falha_count

def importar_temas_redacao(conn):
    print("\n--- Iniciando Importação Temas ---")
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
        print("\n--- IMPORTAÇÃO FINALIZADA ---")
        if questoes_ok == 0: print("\n!!! ALERTA MÁXIMO: NENHUMA QUESTÃO IMPORTADA !!!")
        elif questoes_falha > 0: print(f"\nAVISO: {questoes_falha} linha(s) do CSV tiveram erro.")
        else: print("\nOK: Questões importadas.")
        if temas_ok == 50: print("OK: Temas importados.")
        else: print("AVISO: Problema nos temas.")
    else: print("Importação falhou: Sem conexão com DB.")

'@

# Salvar o script Python FINALMENTE CORRIGIDO no disco
try {
    Set-Content -Path "importar_dados.py" -Value $pythonScriptContentFinal -Encoding UTF8
    Write-Host "✅ Sucesso! Script 'importar_dados.py' foi CORRIGIDO para suas colunas." -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao salvar o 'importar_dados.py' corrigido." -ForegroundColor Red
    Write-Host $_
}

Write-Host "---------------------------------------------------------"
Write-Host "Próximo passo: Recriar o banco MAIS UMA VEZ usando este script corrigido." -ForegroundColor Cyan
Write-Host "Execute o script do Passo 9 (se ele existe e está correto):"
Write-Host "   .\\Passo_9_Refazer_Banco.ps1" -ForegroundColor White
Write-Host "(Se o Passo 9 estiver dando erro de sintaxe PowerShell, me avise para recriá-lo)"
Write-Host "OBSERVE a saída. Desta vez, ele DEVE importar as questões."