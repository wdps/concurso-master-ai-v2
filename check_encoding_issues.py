import sqlite3
import traceback

DB_NAME = 'concurso.db'

def run_diagnostic():
    print(f"\n--- INICIANDO DIAGNÓSTICO DE CODIFICAÇÃO PARA {DB_NAME} ---")
    conn = None
    try:
        # Tenta conectar usando a decodificação padrão (que falha e gera Mojibake)
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        
        # Fazendo uma consulta bruta (sem text_factory especial)
        cursor = conn.cursor()
        cursor.execute("SELECT titulo, dificuldade FROM temas_redacao LIMIT 5")
        temas = cursor.fetchall()
        
        if not temas:
            print("⚠️ A tabela temas_redacao está vazia ou inacessível.")
            return

        print("\n[RESULTADOS DA LEITURA BRUTA (Provavelmente corrompida)]")
        print("----------------------------------------------------------")
        
        # Testando strings (usando Latin-1 para simular o erro oposto)
        for tema in temas:
            raw_title = tema['titulo']
            
            # Tenta reverter o Mojibake (o erro típico é UTF-8 lido como Latin-1)
            try:
                # 1. Encodar a string corrompida de volta para bytes (como se fosse Latin-1)
                corrupted_bytes = raw_title.encode('latin-1')
                # 2. Decodificar corretamente de volta para UTF-8
                decoded_title = corrupted_bytes.decode('utf-8')
                
                print(f"Original DB (Mojibake): {raw_title}")
                print(f"Diagnóstico (Corrigido): {decoded_title}")
                print("-" * 58)

                if "Democratiza" in decoded_title:
                     print(f"🚨 DIAGNÓSTICO: O tema foi corrigido com sucesso via reversão Latin-1/UTF-8.")
                     print("ORIGEM DO BUG: O texto foi inserido no DB com a codificação errada (Mojibake).")
                     return # Sair após o diagnóstico

            except Exception as e:
                print(f"Erro de decodificação para este tema: {e}")
                print("-" * 58)
                
    except sqlite3.Error as e:
        print(f"❌ ERRO SQLITE: {e}")
        print("Verifique se o arquivo 'concurso.db' existe.")
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    run_diagnostic()
