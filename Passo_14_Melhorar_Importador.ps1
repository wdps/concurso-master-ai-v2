# Passo 14 (Diagnóstico Avançado): Melhorando o script 'importar_dados.py'

Write-Host "🚀 Iniciando Passo 14: Tornando 'importar_dados.py' mais robusto e informativo..." -ForegroundColor Cyan

# Conteúdo MELHORADO do script Python 'importar_dados.py'
$pythonScriptContentMelhorado = @'
import sqlite3
import csv
import json
import os
import sys
import re # Importa regex para alternativas

print("--- INICIANDO SCRIPT DE IMPORTAÇÃO E ATUALIZAÇÃO DO BANCO (V3 Diagnóstico) ---")

# Lista de 50 temas de redação (Estilo ENEM/Concursos) - Mantida igual
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
    try:
        conn = sqlite3.connect('concurso.db')
        conn.row_factory = sqlite3.Row
        print("Conexão com banco 'concurso.db' estabelecida.")
        return conn
    except Exception as e:
        print(f"ERRO FATAL ao conectar ao banco: {e}")
        return None

def atualizar_estrutura_banco(conn):
    print("Verificando/Atualizando estrutura das tabelas...")
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT NOT NULL, materia TEXT NOT NULL,
                enunciado TEXT NOT NULL, alternativas TEXT NOT NULL, resposta_correta TEXT NOT NULL,
                dificuldade TEXT CHECK(dificuldade IN ('Fácil', 'Médio', 'Difícil')) DEFAULT 'Médio',
                justificativa TEXT, dica TEXT, formula TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                peso INTEGER DEFAULT 1 ) ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temas_redacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, descricao TEXT, tipo TEXT NOT NULL,
                dificuldade TEXT CHECK(dificuldade IN ('Fácil', 'Médio', 'Difícil')) DEFAULT 'Médio',
                palavras_chave TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ) ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_simulados (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, simulado_id TEXT NOT NULL UNIQUE,
                config TEXT NOT NULL, respostas TEXT NOT NULL, relatorio TEXT NOT NULL,
                data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP, data_fim TIMESTAMP, tempo_total_minutos REAL DEFAULT 0 ) ''')
        cursor.execute("PRAGMA table_info(questoes)")
        cols_q = [c[1] for c in cursor.fetchall()]
        if 'peso' not in cols_q: cursor.execute("ALTER TABLE questoes ADD COLUMN peso INTEGER DEFAULT 1")
        if 'justificativa' not in cols_q: cursor.execute("ALTER TABLE questoes ADD COLUMN justificativa TEXT")
        if 'dica' not in cols_q: cursor.execute("ALTER TABLE questoes ADD COLUMN dica TEXT")
        if 'formula' not in cols_q: cursor.execute("ALTER TABLE questoes ADD COLUMN formula TEXT")
        conn.commit()
        print("Estrutura do banco verificada/atualizada.")
    except Exception as e:
        print(f"ERRO ao atualizar estrutura do banco: {e}")

def parse_alternativas(texto_alternativas):
    texto_alternativas = texto_alternativas.strip()
    try:
        data = json.loads(texto_alternativas)
        if isinstance(data, dict): return {k.strip().upper(): v for k, v in data.items()}
    except json.JSONDecodeError: pass
    try:
        alt_dict = {}; partes = texto_alternativas.split('|')
        if len(partes) < 2 and '|' not in texto_alternativas:
             partes_re = re.split(r'\s+([B-Z])\)', texto_alternativas); novas_partes = [partes_re[0]]
             for i in range(1, len(partes_re), 2):
                 if i+1 < len(partes_re): novas_partes.append(partes_re[i] + ')' + partes_re[i+1])
             partes = novas_partes
        processed_keys = set()
        for parte in partes:
            parte = parte.strip();
            if not parte: continue
            match = re.match(r'^([A-Z])\s*\)', parte, re.IGNORECASE)
            if match:
                letra = match.group(1).upper(); texto = parte[match.end():].strip()
                if letra not in processed_keys: alt_dict[letra] = texto; processed_keys.add(letra)
            else: print(f"      AVISO: Parte da alternativa não reconhecida: '{parte[:50]}...'")
        if len(alt_dict) >= 2: return {k: alt_dict[k] for k in sorted(alt_dict.keys())}
        else: print(f"      ERRO: Não extraiu alternativas válidas de: '{texto_alternativas[:100]}...'"); return None
    except Exception as e_parse: print(f"      ERRO inesperado ao analisar alt '{texto_alternativas[:50]}...': {e_parse}"); return None

def importar_questoes_csv(conn):
    print("\n--- Iniciando Importação do 'questoes.csv' (Modo Diagnóstico) ---")
    csv_file = 'questoes.csv'
    if not os.path.exists(csv_file): print(f"ERRO FATAL: '{csv_file}' não encontrado!"); return 0, 0
    cursor = conn.cursor()
    print("Limpando tabela 'questoes'...");
    try: cursor.execute("DELETE FROM questoes"); cursor.execute("DELETE FROM sqlite_sequence WHERE name='questoes'"); conn.commit(); print("Tabela 'questoes' limpa.")
    except Exception as e: print(f"ERRO ao limpar 'questoes': {e}"); return 0, 0
    sucesso_count = 0; falha_count = 0; linhas_total = 0
    try:
        encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1']; detected_encoding = None
        for enc in encodings_to_try:
             try:
                 with open(csv_file, mode='r', encoding=enc) as file: file.read(1024)
                 detected_encoding = enc; print(f"Detectado encoding: {detected_encoding}"); break
             except UnicodeDecodeError: continue
             except Exception as e_enc: print(f"Erro inesperado ao testar {enc}: {e_enc}")
        if not detected_encoding: print("ERRO FATAL: Encoding não detectado."); return 0, 0
        with open(csv_file, mode='r', encoding=detected_encoding) as file:
            try:
                 sample = file.read(4096); dialect = csv.Sniffer().sniff(sample, delimiters=';,')
                 print(f"Sniffer detectou delimitador: '{dialect.delimiter}'")
            except csv.Error:
                 print("AVISO: Sniffer falhou. Verificando ';' vs ','..."); file.seek(0); first_line = file.readline()
                 if first_line.count(';') >= first_line.count(','): dialect = csv.excel; dialect.delimiter = ';'; print("Assumindo delimitador: ';'")
                 else: dialect = csv.excel; dialect.delimiter = ','; print("Assumindo delimitador: ','")
            file.seek(0); reader = csv.DictReader(file, dialect=dialect)
            colunas = reader.fieldnames
            if not colunas: print("ERRO FATAL: CSV vazio ou colunas não lidas."); return 0, 0
            print(f"Colunas encontradas: {colunas}")
            mapa_colunas = { 'disciplina': next((c for c in colunas if 'disciplina' in c.lower()), None), 'materia': next((c for c in colunas if 'materia' in c.lower() or 'matéria' in c.lower()), None), 'enunciado': next((c for c in colunas if 'enunciado' in c.lower()), None), 'alternativas': next((c for c in colunas if 'alternativas' in c.lower()), None), 'resposta_correta': next((c for c in colunas if 'resposta' in c.lower()), None), 'dificuldade': next((c for c in colunas if 'dificuldade' in c.lower()), None), 'justificativa': next((c for c in colunas if 'justificativa' in c.lower()), None), 'dica': next((c for c in colunas if 'dica' in c.lower()), None), 'formula': next((c for c in colunas if 'formula' in c.lower()), None), 'peso': next((c for c in colunas if 'peso' in c.lower()), None) }
            essenciais = ['disciplina', 'materia', 'enunciado', 'alternativas', 'resposta_correta']
            if any(mapa_colunas[key] is None for key in essenciais): print(f"ERRO FATAL: Colunas essenciais ({', '.join(essenciais)}) não encontradas."); print(f"Mapeamento: {mapa_colunas}"); return 0, 0
            print("Mapeamento de colunas OK.")
            questoes_para_inserir = []; print("\n--- Processando linhas do CSV ---")
            for i, row in enumerate(reader):
                linhas_total += 1; print(f"  Linha CSV {i+2}: Processando...")
                if not all(row.get(mapa_colunas[key]) for key in essenciais if mapa_colunas[key]): print(f"      ERRO: Linha {i+2} inválida/vazia. Pulando.\n      Dados: {row}"); falha_count += 1; continue
                try:
                    texto_alt = row.get(mapa_colunas['alternativas'], ''); alt_dict = parse_alternativas(texto_alt)
                    if alt_dict is None: raise ValueError(f"Falha ao processar alternativas: '{texto_alt[:100]}...'")
                    alternativas_json = json.dumps(alt_dict, ensure_ascii=False)
                    try: peso_valor = int(row.get(mapa_colunas.get('peso'), 1) or 1)
                    except (ValueError, TypeError): print(f"      AVISO: Peso inválido linha {i+2}, usando 1. Valor: '{row.get(mapa_colunas.get('peso'))}'"); peso_valor = 1
                    q = ( row.get(mapa_colunas['disciplina'], 'N/A').strip(), row.get(mapa_colunas['materia'], 'N/A').strip(), row.get(mapa_colunas['enunciado'], 'N/A').strip(), alternativas_json, row.get(mapa_colunas['resposta_correta'], 'N/A').strip().upper(), row.get(mapa_colunas['dificuldade'], 'Médio').strip().capitalize(), row.get(mapa_colunas.get('justificativa'), '').strip(), row.get(mapa_colunas.get('dica'), '').strip(), row.get(mapa_colunas.get('formula'), '').strip(), peso_valor )
                    if not all(q[:5]): raise ValueError("Dados essenciais ausentes.")
                    questoes_para_inserir.append(q); print(f"      OK: Linha {i+2} processada."); sucesso_count += 1
                except (ValueError, TypeError, json.JSONDecodeError, KeyError) as e_row: print(f"      ERRO DETALHADO linha {i+2}: {e_row}\n      Dados: {row}"); falha_count += 1
                except Exception as e_inesperado: print(f"      ERRO GRAVE linha {i+2}: {e_inesperado}"); falha_count += 1
            print("\n--- Fim do Processamento ---")
            if not questoes_para_inserir: print("\nERRO GRAVE: Nenhuma questão processada!"); return sucesso_count, falha_count
            print(f"\nInserindo {len(questoes_para_inserir)} questões...");
            cursor.executemany('INSERT INTO questoes (disciplina, materia, enunciado, alternativas, resposta_correta, dificuldade, justificativa, dica, formula, peso) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', questoes_para_inserir)
            conn.commit(); print("Inserção concluída.")
    except FileNotFoundError: print(f"ERRO FATAL: '{csv_file}' não encontrado.")
    except Exception as e:
        print(f"ERRO GERAL na importação CSV: {e}")
        try: exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]; print(f"   Erro no arquivo {fname}, linha {exc_tb.tb_lineno}")
        except: pass
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
        print("\n--- IMPORTAÇÃO E ATUALIZAÇÃO CONCLUÍDAS ---")
        if questoes_ok == 0: print("\n!!! ALERTA MÁXIMO: NENHUMA QUESTÃO IMPORTADA !!!\n   Verifique erros e corrija 'questoes.csv'.")
        elif questoes_falha > 0: print(f"\nAVISO: {questoes_falha} linha(s) do CSV tiveram erro.\n   Verifique os detalhes acima.")
        else: print("\nOK: Importação de questões parece OK.")
        if temas_ok == 50: print("OK: Importação de temas OK.")
        else: print("AVISO: Problema na importação dos temas.")
    else: print("Importação falhou: Não conectou ao banco.")
'@

# Salvar o script Python MELHORADO no disco
try {
    Set-Content -Path "importar_dados.py" -Value $pythonScriptContentMelhorado -Encoding UTF8
    Write-Host "✅ Sucesso! Script 'importar_dados.py' foi atualizado com mais diagnósticos." -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao salvar o arquivo 'importar_dados.py' melhorado." -ForegroundColor Red
    Write-Host $_
}

Write-Host "---------------------------------------------------------"
Write-Host "Próximo passo: Recriar o banco USANDO ESTE NOVO SCRIPT." -ForegroundColor Cyan
Write-Host "Execute novamente o script do Passo 9 (SE VOCÊ JÁ O SALVOU):"
Write-Host "   .\\Passo_9_Refazer_Banco.ps1" -ForegroundColor White
Write-Host "OU, se não salvou, salve o código do Passo 9 e execute."
Write-Host "OBSERVE ATENTAMENTE a saída dele. Ele vai detalhar erros por linha no CSV."