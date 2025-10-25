import sqlalchemy as db
import sys

try:
    print("🔍 Testando conexão com banco...")
    engine = db.create_engine("sqlite:///concurso.db")
    metadata = db.MetaData()
    metadata.reflect(bind=engine)
    print("✅ Banco conectado com sucesso!")
    
    print("🔍 Testando importação do Flask...")
    from flask import Flask
    print("✅ Flask importado com sucesso!")
    
    print("🔍 Testando criação do app...")
    app = Flask(__name__)
    print("✅ App criado com sucesso!")
    
    print("🎉 Tudo funcionando!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
