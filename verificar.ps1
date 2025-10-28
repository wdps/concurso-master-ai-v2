powershell
# SISTEMA ESQUEMATIZA.AI - VERIFICADOR E CORRETOR COMPLETO
Write-Host "🧠 INICIANDO VERIFICACAO COMPLETA DO ESQUEMATIZA.AI" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# Configuração
$ErrorActionPreference = "Continue"

# Funções de utilitário
function Write-Success { param($msg) Write-Host "SUCESSO $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "AVISO $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "ERRO $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "INFO $msg" -ForegroundColor Cyan }

# 1. Verificar Python
Write-Info "Verificando ambiente Python..."
try {
    $pythonVersion = python --version
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python encontrado: $pythonVersion"
    } else {
        Write-Error "Python nao encontrado. Instale o Python primeiro."
        exit 1
    }
} catch {
    Write-Error "Python nao encontrado. Instale o Python primeiro."
    exit 1
}

# 2. Verificar e corrigir questões.csv
Write-Info "Verificando arquivo questoes.csv..."
if (-not (Test-Path "questoes.csv")) {
    Write-Warning "Arquivo questoes.csv nao encontrado. Criando arquivo de exemplo..."
    
    $exemploCSV = 'id,disciplina,materia,enunciado,alternativas,resposta_correta,justificativa,dificuldade,peso,dica,formula
1,Matematica,Algebra,"Qual e o resultado de 2 + 2?","{""A"": ""3"", ""B"": ""4"", ""C"": ""5"", ""D"": ""6""}","B","2 + 2 = 4","Facil",1,"Some os numeros","a + b = c"
2,Portugues,Gramatica,"Assinale a alternativa correta sobre concordancia verbal:","{""A"": ""Eu vai ao mercado"", ""B"": ""Nos vamos ao mercado"", ""C"": ""Tu ir ao mercado"", ""D"": ""Ele vao ao mercado""}","B","A concordancia correta e 'nos vamos'","Media",2,"Verifique a conjugacao verbal",""
3,Historia,Brasil Colon,"Quem descobriu o Brasil?","{""A"": ""Cristovao Colombo"", ""B"": ""Pedro Alvares Cabral"", ""C"": ""Dom Pedro I"", ""D"": ""Tiradentes""}","B","Pedro Alvares Cabral descobriu o Brasil em 1500","Facil",1,"Ano de 1500",""'
    
    Set-Content -Path "questoes.csv" -Value $exemploCSV -Encoding UTF8
    Write-Success "Arquivo questoes.csv de exemplo criado com 3 questões"
} else {
    $fileSize = (Get-Item "questoes.csv").Length
    $lineCount = (Get-Content "questoes.csv").Count
    Write-Success "Arquivo questoes.csv encontrado ($([math]::Round($fileSize/1KB, 2)) KB, $lineCount linhas)"
}

# 3. Verificar estrutura do CSV
Write-Info "Verificando estrutura do CSV..."
try {
    python -c "import csv; import json
try:
    with open('questoes.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        questions = list(reader)
    
    print(f'Total de questões no CSV: {len(questions)}')
    
    valid_questions = 0
    for i, q in enumerate(questions, 1):
        if not q.get('enunciado') or not q.get('resposta_correta'):
            print(f'Questão {i}: Campos obrigatorios faltando')
            continue
        try:
            alternatives = json.loads(q['alternativas'].replace('""', '\"'))
            if not isinstance(alternatives, dict):
                print(f'Questão {i}: Alternativas não é um dicionário JSON válido')
                continue
        except Exception as e:
            print(f'Questão {i}: Erro no JSON das alternativas: {e}')
            continue
        valid_questions += 1
    
    print(f'Questões válidas: {valid_questions}')
    print(f'Questões com problemas: {len(questions) - valid_questions}')
except Exception as e:
    print(f'Erro ao verificar CSV: {e}')"
    
    Write-Success "Verificacao do CSV concluida"
} catch {
    Write-Warning "Problema ao verificar estrutura do CSV"
}

# 4. Verificar e inicializar banco de dados
Write-Info "Verificando banco de dados..."
if (-not (Test-Path "concurso.db")) {
    Write-Warning "Banco de dados nao encontrado. Inicializando..."
}

# Criar script Python para inicialização do banco
$initDBScript = @'
import sqlite3
import csv
import json
import os

print("Inicializando banco de dados...")

# Conectar ou criar banco
conn = sqlite3.connect('concurso.db')
cursor = conn.cursor()

# Criar tabelas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disciplina TEXT,
        materia TEXT,
        enunciado TEXT,
        alternativas TEXT,
        resposta_correta TEXT,
        justificativa TEXT,
        dificuldade TEXT,
        peso REAL DEFAULT 1,
        dica TEXT,
        formula TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico_simulados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        simulado_id TEXT,
        respostas TEXT,
        relatorio TEXT,
        data_fim TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS temas_redacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT UNIQUE,
        descricao TEXT
    )
''')

# Inserir temas de redacao
temas_exemplo = [
    ('A importancia da educacao digital', 'Reflita sobre tecnologia na educacao'),
    ('Mobilidade urbana nas grandes cidades', 'Problemas e solucoes para transporte'),
    ('Trabalho na era da inteligencia artificial', 'Como a IA transforma o mercado')
]

for tema in temas_exemplo:
    try:
        cursor.execute('INSERT OR IGNORE INTO temas_redacao (titulo, descricao) VALUES (?, ?)', tema)
    except:
        pass

# Importar questoes do CSV
if os.path.exists('questoes.csv'):
    print("Importando questões do CSV...")
    with open('questoes.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        imported = 0
        
        for row in reader:
            try:
                # Verificar se a questao ja existe
                cursor.execute('SELECT id FROM questoes WHERE enunciado = ?', (row['enunciado'],))
                if cursor.fetchone() is None:
                    cursor.execute('''INSERT INTO questoes (disciplina, materia, enunciado, alternativas, resposta_correta, justificativa, dificuldade, peso, dica, formula) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (row.get('disciplina', ''), row.get('materia', ''), row.get('enunciado', ''), row.get('alternativas', '{}'), row.get('resposta_correta', ''), row.get('justificativa', ''), row.get('dificuldade', 'Media'), float(row.get('peso', 1)), row.get('dica', ''), row.get('formula', '')))
                    imported += 1
            except Exception as e:
                print(f"Erro ao importar questão: {e}")

    print(f"Questões importadas: {imported}")

# Contar totais
cursor.execute('SELECT COUNT(*) FROM questoes')
total_questoes = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM temas_redacao')
total_temas = cursor.fetchone()[0]

conn.commit()
conn.close()

print(f"Banco inicializado com sucesso!")
print(f"Questões no banco: {total_questoes}")
print(f"Temas de redação: {total_temas}")
'@

Set-Content -Path "temp_init_db.py" -Value $initDBScript -Encoding UTF8
python temp_init_db.py
Remove-Item "temp_init_db.py" -ErrorAction SilentlyContinue
Write-Success "Banco de dados inicializado"

# 5. Verificar dependencias Python
Write-Info "Verificando dependencias Python..."
$dependencies = @("flask", "python-dotenv", "google-generativeai", "waitress")

foreach ($dep in $dependencies) {
    try {
        python -c "import $dep" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Dependencia: $dep"
        } else {
            Write-Warning "Instalando: $dep"
            pip install $dep
        }
    } catch {
        Write-Warning "Instalando: $dep"
        pip install $dep
    }
}

# 6. Verificar e corrigir app.py
Write-Info "Verificando arquivo app.py..."
if (-not (Test-Path "app.py")) {
    Write-Error "Arquivo app.py nao encontrado. Criando versao basica..."
    
    $basicApp = @'
from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta_esquematiza'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/materias')
def api_materias():
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT materia, disciplina FROM questoes')
    materias = cursor.fetchall()
    conn.close()
    
    areas = {}
    for materia, disciplina in materias:
        if disciplina not in areas:
            areas[disciplina] = []
        areas[disciplina].append({'materia_chave': materia, 'materia_nome': materia})
    
    return jsonify({'success': True, 'areas': areas})

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    data = request.get_json()
    materias = data.get('materias', [])
    quantidade = data.get('quantidade', 10)
    
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    placeholders = ','.join(['?'] * len(materias))
    query = f'SELECT * FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
    cursor.execute(query, materias + [quantidade])
    questões = cursor.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'questoes': len(questões)})

if __name__ == '__main__':
    print("ESQUEMATIZA.AI - Servidor iniciado")
    print("Acesse: http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
'@
    
    Set-Content -Path "app.py" -Value $basicApp -Encoding UTF8
    Write-Success "Arquivo app.py basico criado"
} else {
    # Corrigir problemas de logging no app.py existente
    Write-Info "Verificando problemas no app.py..."
    
    $content = Get-Content -Path "app.py" -Raw -Encoding UTF8
    
    # Substituir emojis problemáticos no logging
    $replacements = @{
        'logger\.info\(f"✅' = 'logger.info(f"SUCESSO'
        'logger\.error\(f"❌' = 'logger.error(f"ERRO'
        'logger\.warning\(f"⚠️' = 'logger.warning(f"AVISO'
    }
    
    $newContent = $content
    foreach ($key in $replacements.Keys) {
        $newContent = $newContent -replace $key, $replacements[$key]
    }
    
    if ($newContent -ne $content) {
        Set-Content -Path "app.py" -Value $newContent -Encoding UTF8
        Write-Success "Problemas de logging corrigidos no app.py"
    } else {
        Write-Success "app.py esta OK"
    }
}

# 7. Verificar templates
Write-Info "Verificando templates..."
$templates = @("index.html", "simulado.html", "redacao.html", "dashboard.html")
foreach ($template in $templates) {
    if (-not (Test-Path "templates\$template")) {
        Write-Warning "Template faltando: $template"
        # Criar template basico se nao existir
        $basicTemplate = @'
<!DOCTYPE html>
<html>
<head>
    <title>ESQUEMATIZA.AI</title>
    <style>body { font-family: Arial, sans-serif; padding: 20px; }</style>
</head>
<body>
    <h1>ESQUEMATIZA.AI</h1>
    <p>Sistema de simulados para concursos</p>
    <nav>
        <a href="/">Inicio</a> | 
        <a href="/simulado">Simulado</a> | 
        <a href="/redacao">Redacao</a> | 
        <a href="/dashboard">Dashboard</a>
    </nav>
    <div id="content">
        <p>Conteudo da pagina</p>
    </div>
</body>
</html>
'@
        if (-not (Test-Path "templates")) {
            New-Item -ItemType Directory -Path "templates" | Out-Null
        }
        Set-Content -Path "templates\$template" -Value $basicTemplate -Encoding UTF8
        Write-Success "Template basico criado: $template"
    }
}

# 8. Verificar arquivos estaticos
Write-Info "Verificando arquivos estaticos..."
if (-not (Test-Path "static")) {
    New-Item -ItemType Directory -Path "static" | Out-Null
    New-Item -ItemType Directory -Path "static\css" | Out-Null
    New-Item -ItemType Directory -Path "static\js" | Out-Null
    Write-Success "Diretorios static criados"
}

# Criar CSS basico se nao existir
if (-not (Test-Path "static\css\style.css")) {
    $basicCSS = @'
body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
.container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
.header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; text-align: center; }
.nav-tabs { display: flex; gap: 10px; margin: 20px 0; }
.nav-tab { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
.card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.hidden { display: none; }
'@
    Set-Content -Path "static\css\style.css" -Value $basicCSS -Encoding UTF8
    Write-Success "CSS basico criado"
}

# Criar JavaScript basico se nao existir
if (-not (Test-Path "static\js\script.js")) {
    $basicJS = @'
function navegarPara(tela) {
    document.querySelectorAll('.tela').forEach(t => t.classList.add('hidden'));
    document.getElementById(tela).classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('ESQUEMATIZA.AI carregado');
    navegarPara('tela-inicio');
});
'@
    Set-Content -Path "static\js\script.js" -Value $basicJS -Encoding UTF8
    Write-Success "JavaScript basico criado"
}

# 9. Teste final
Write-Info "Realizando teste final..."
try {
    python -c "
try:
    from app import app
    print('SUCESSO: Aplicacao Flask importada corretamente')
    
    import sqlite3
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM questoes')
    q_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM temas_redacao') 
    t_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f'Questoes no banco: {q_count}')
    print(f'Temas de redacao: {t_count}')
    print('SISTEMA PRONTO PARA USO!')
    
except Exception as e:
    print(f'ERRO NO TESTE: {e}')
    import traceback
    traceback.print_exc()
"
    Write-Success "Teste final concluido"
} catch {
    Write-Warning "Problema no teste final, mas tentando iniciar mesmo assim"
}