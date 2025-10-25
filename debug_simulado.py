# debug_simulado.py - Para verificar problemas específicos

import sqlite3
import json

def debug_questoes():
    print("🔍 DEBUG DAS QUESTÕES NO BANCO")
    
    conn = sqlite3.connect('concurso.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Ver estrutura da tabela
    cursor.execute("PRAGMA table_info(questoes)")
    colunas = cursor.fetchall()
    print("📋 ESTRUTURA DA TABELA:")
    for col in colunas:
        print(f"   - {col[1]} ({col[2]})")
    
    # Ver algumas questões
    cursor.execute("SELECT * FROM questoes LIMIT 2")
    questao_exemplo = cursor.fetchone()
    
    if questao_exemplo:
        print("📄 EXEMPLO DE QUESTÃO:")
        print(f"   ID: {questao_exemplo['id']}")
        print(f"   Matéria: {questao_exemplo['materia']}")
        print(f"   Enunciado: {questao_exemplo['enunciado'][:50]}...")
        print(f"   Alternativas: {questao_exemplo['alternativas'][:100]}...")
        print(f"   Resposta: {questao_exemplo['resposta_correta']}")
        print(f"   Dificuldade: {questao_exemplo['dificuldade'] if 'dificuldade' in questao_exemplo.keys() else 'NÃO ENCONTRADA'}")
        
        # Testar acesso às colunas
        print("🔧 TESTANDO ACESSO ÀS COLUNAS:")
        try:
            print(f"   q['id']: {questao_exemplo['id']} ✅")
            print(f"   q['materia']: {questao_exemplo['materia']} ✅")
            print(f"   q['enunciado']: OK ✅")
            print(f"   q['alternativas']: OK ✅")
            print(f"   q['resposta_correta']: OK ✅")
            print(f"   q['explicacao']: OK ✅")
            print(f"   q['dificuldade']: OK ✅")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    conn.close()

if __name__ == "__main__":
    debug_questoes()
