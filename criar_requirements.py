# Conteúdo do requirements.txt
conteudo = """# 🌐 CORE FRAMEWORKS
fastapi==0.104.1
uvicorn==0.24.0

# 🗄️ DATABASE
sqlalchemy==2.0.23

# 🔧 UTILITIES
python-dotenv==1.0.0
pydantic==2.5.0

# 🤖 AI SERVICES
google-generativeai==0.3.2

# 📊 DATA PROCESSING
pandas==2.1.3
numpy==1.24.3

# 🌐 HTTP CLIENT
httpx==0.25.2
requests==2.31.0

# 🎯 CONCURSOMASTER SPECIFIC
aiofiles==23.2.1
python-multipart==0.0.6
"""

# Criar arquivo requirements.txt
with open('requirements.txt', 'w', encoding='utf-8') as arquivo:
    arquivo.write(conteudo)

print("✅ Arquivo requirements.txt criado com sucesso!")
