import sqlite3
import json

print("🔍 DIAGNÓSTICO DE ENCODING E BANCO DE DADOS")
print("=" * 50)

try:
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    # Verificar encoding dos temas
    print("\n📝 VERIFICANDO TEMAS DE REDAÇÃO:")
    cursor.execute("SELECT titulo FROM temas_redacao LIMIT 5")
    temas = cursor.fetchall()
    
    for i, tema in enumerate(temas, 1):
        titulo = tema[0]
        print(f"  {i}. {titulo}")
        print(f"     Bytes: {titulo.encode('utf-8')}")
        print(f"     Com problemas: {'Sim' if 'Ã' in titulo or 'Â' in titulo else 'Não'}")
    
    # Verificar questões
    print("\n📚 VERIFICANDO QUESTÕES:")
    cursor.execute("SELECT enunciado FROM questoes LIMIT 3")
    quests = cursor.fetchall()
    
    for i, quest in enumerate(quests, 1):
        enunciado = quest[0][:100] + "..." if len(quest[0]) > 100 else quest[0]
        print(f"  {i}. {enunciado}")
        print(f"     Com problemas: {'Sim' if 'Ã' in quest[0] or 'Â' in quest[0] else 'Não'}")
    
    # Verificar estrutura das alternativas
    print("\n🔍 VERIFICANDO ESTRUTURA DAS ALTERNATIVAS:")
    cursor.execute("SELECT alternativas FROM questoes LIMIT 1")
    alt_exemplo = cursor.fetchone()
    if alt_exemplo:
        try:
            alternativas = json.loads(alt_exemplo[0])
            print(f"  ✅ Alternativas parseadas corretamente")
            print(f"  📊 Estrutura: {type(alternativas)}")
            for key, value in alternativas.items():
                print(f"     {key}: {value[:50]}...")
        except Exception as e:
            print(f"  ❌ Erro ao parsear alternativas: {e}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Erro no diagnóstico: {e}")
