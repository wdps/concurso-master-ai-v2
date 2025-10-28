# --- Script para adicionar a coluna 'eixo' ---
.\sqlite3.exe = ".\sqlite3.exe"
.\concursos.db = ".\concursos.db"
if (-not (Test-Path .\sqlite3.exe)) { Write-Host "ERRO: 'sqlite3.exe' não encontrado." -ForegroundColor Red; Read-Host "Pressione Enter"; exit }
ALTER TABLE temas_redacao ADD COLUMN eixo TEXT; = "ALTER TABLE temas_redacao ADD COLUMN eixo TEXT;"
Write-Host "Tentando adicionar a coluna 'eixo' em 'temas_redacao'..."
try {
    & .\sqlite3.exe .\concursos.db ALTER TABLE temas_redacao ADD COLUMN eixo TEXT; 2>&1 | Out-Null
    Write-Host "SUCESSO: Coluna 'eixo' foi adicionada." -ForegroundColor Green
} catch {
     = .Exception.Message
    if ( -like "*duplicate column name: eixo*") {
        Write-Host "AVISO: A coluna 'eixo' já existe." -ForegroundColor Cyan
    } else {
        Write-Host "ERRO: " -ForegroundColor Red
    }
}
Write-Host "Correção da coluna 'eixo' concluída."
Read-Host "Pressione Enter para fechar."
