# --- Script PowerShell para Corrigir o Esquema do Banco de Dados ---
#
# OBJETIVO: Sincronizar o 'concursos.db' com o código 'app.py' que espera
#           a tabela 'questions' e a coluna 'tipo'.
#
# PRÉ-REQUISITO: Este script precisa do 'sqlite3.exe' no mesmo diretório
#                ou no PATH do sistema.
# -----------------------------------------------------------------

# --- CONFIGURAÇÃO ---
$sqliteExe = ".\sqlite3.exe"       # Caminho para o executável (.\ significa 'neste diretório')
$dbPath = ".\concursos.db"         # Caminho para seu banco de dados
# --------------------

Write-Host "Iniciando script de correção de banco de dados..." -ForegroundColor Yellow

# 1. Verificar se o sqlite3.exe existe
if (-not (Test-Path $sqliteExe)) {
    Write-Host "ERRO: 'sqlite3.exe' não encontrado em '$sqliteExe'." -ForegroundColor Red
    Write-Host "Por favor, baixe o 'sqlite-tools' do site oficial do SQLite e coloque o .exe neste diretório." -ForegroundColor Red
    Read-Host "Pressione Enter para sair..."
    exit
}

# 2. Verificar se o banco de dados existe
if (-not (Test-Path $dbPath)) {
    Write-Host "ERRO: Banco de dados 'concursos.db' não encontrado em '$dbPath'." -ForegroundColor Red
    Read-Host "Pressione Enter para sair..."
    exit
}

# --- CORREÇÃO 1: Renomear Tabela 'questoes' para 'questions' ---
$sql_rename_table = "ALTER TABLE questoes RENAME TO questions;"

Write-Host "Passo 1: Tentando renomear a tabela 'questoes' para 'questions'..."
try {
    # Usamos '&' para executar o comando e redirecionamos a saída de erro (2>&1) para Out-Null
    # para evitar que erros de "tabela já existe" parem o script.
    & $sqliteExe $dbPath $sql_rename_table 2>&1 | Out-Null
    Write-Host "SUCESSO: Tabela 'questoes' foi renomeada para 'questions'." -ForegroundColor Green
} catch {
    $errorMessage = $_.Exception.Message
    if ($errorMessage -like "*no such table: questoes*") {
        Write-Host "AVISO: A tabela 'questoes' não foi encontrada. Talvez ela já se chame 'questions'." -ForegroundColor Cyan
    } else {
        Write-Host "ERRO no Passo 1: $errorMessage" -ForegroundColor Red
    }
}

# --- CORREÇÃO 2: Adicionar Coluna 'tipo' em 'temas_redacao' ---
$sql_add_column = "ALTER TABLE temas_redacao ADD COLUMN tipo TEXT;"

Write-Host "Passo 2: Tentando adicionar a coluna 'tipo' na tabela 'temas_redacao'..."
try {
    & $sqliteExe $dbPath $sql_add_column 2>&1 | Out-Null
    Write-Host "SUCESSO: Coluna 'tipo' foi adicionada em 'temas_redacao'." -ForegroundColor Green
} catch {
    $errorMessage = $_.Exception.Message
    if ($errorMessage -like "*duplicate column name: tipo*") {
        Write-Host "AVISO: A coluna 'tipo' já existe em 'temas_redacao'. Nada a fazer." -ForegroundColor Cyan
    } else {
        Write-Host "ERRO no Passo 2: $errorMessage" -ForegroundColor Red
    }
}

Write-Host "----------------------------------------------------"
Write-Host "Correção do banco de dados concluída." -ForegroundColor Yellow
Read-Host "Pressione Enter para fechar."