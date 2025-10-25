import csv
import os
import sys

# O nome do arquivo que queremos verificar
CSV_FILENAME = 'questoes.csv'

def analyze_csv(encoding_to_try):
    """
    Tenta abrir o CSV com uma codificação, lê o cabeçalho e a primeira linha.
    """
    with open(CSV_FILENAME, mode='r', encoding=encoding_to_try, newline='') as f:
        # Detectar o dialeto (ex: delimitador ; ou ,)
        try:
            # Lê um pedaço do arquivo para o Sniffer
            sample = f.read(2048) 
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.reader(f, dialect)
            print(f"Dialeto detectado: Delimitador='{dialect.delimiter}'")
        except csv.Error:
            # Sniffer pode falhar, usar o padrão (vírgula)
            f.seek(0)
            reader = csv.reader(f)
            print("Dialeto não detectado. Usando padrão (delimitador = ',')")
        
        try:
            # Ler o cabeçalho (primeira linha)
            header = next(reader)
        except StopIteration:
            print("\nERRO: O arquivo CSV está completamente vazio.")
            return

        # Tentar ler a primeira linha de dados (segunda linha)
        first_data_row = None
        try:
            first_data_row = next(reader)
        except StopIteration:
            pass # O arquivo só tem o cabeçalho
        
        print("\n" + "="*40)
        print("--- RELATÓRIO DO ARQUIVO CSV ---")
        print(f"Arquivo: {CSV_FILENAME}")
        print(f"Codificação: {encoding_to_try}")
        print(f"Total de colunas: {len(header)}")
        
        print("\n--- NOMES DAS COLUNAS (Cabeçalho) ---")
        for i, col_name in enumerate(header):
            print(f"  [{i+1}] {col_name}")
        
        if first_data_row:
            print("\n--- EXEMPLO (Primeira Linha de Dados) ---")
            for i in range(len(header)):
                # Garante que não tenhamos um erro se a linha for mais curta
                data_sample = first_data_row[i] if i < len(first_data_row) else "[CAMPO VAZIO]"
                # Limitar o tamanho da amostra para não poluir o log
                if len(data_sample) > 70:
                    data_sample = data_sample[:70] + "..."
                
                # Garante que o nome da coluna exista (caso a linha seja mais longa que o header)
                col_name = header[i] if i < len(header) else f"[COLUNA EXTRA {i+1}]"
                print(f"  {col_name}: '{data_sample}'")
        else:
            print("\nAVISO: O arquivo CSV parece estar vazio (só tem cabeçalho).")

        print("\n" + "="*40)
        print("PRÓXIMO PASSO: Copie e cole TODA esta saída")
        print("(de '--- RELATÓRIO...' até aqui) e me envie.")
        print("Com isso, eu criarei seu script 'seed.py'!")
        print("="*40)

# --- Execução Principal ---

if not os.path.exists(CSV_FILENAME):
    print(f"--- ERRO ---")
    print(f"Arquivo '{CSV_FILENAME}' NÃO ENCONTRADO.")
    print(f"Por favor, coloque o '{CSV_FILENAME}' na mesma pasta que este script (check_csv.py) e tente novamente.")
    sys.exit(1)

try:
    # Tentar com UTF-8 (padrão moderno)
    print("Tentando ler com codificação 'utf-8'...")
    analyze_csv('utf-8')
except UnicodeDecodeError:
    # Se falhar, tentar com 'latin-1' (comum no Excel/Windows em português)
    print("\nUTF-8 falhou. Tentando 'latin-1'...")
    try:
        analyze_csv('latin-1')
    except Exception as e:
        print(f"--- ERRO GERAL ---")
        print(f"Não consegui ler o arquivo nem com 'utf-8' nem com 'latin-1'. Erro: {e}")
except Exception as e:
    print(f"--- ERRO INESPERADO ---")
    print(f"Ocorreu um erro ao processar o CSV: {e}")
