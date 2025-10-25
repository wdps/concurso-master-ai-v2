import sqlalchemy as db

engine = db.create_engine("sqlite:///concurso.db")
metadata = db.MetaData()
metadata.reflect(bind=engine)
questoes_table = metadata.tables['questoes']

print("📊 ESTRUTURA DA TABELA:")
for column in questoes_table.columns:
    print(f"  {column.name}: {column.type} {'(NULLABLE)' if column.nullable else '(NOT NULL)'}")
