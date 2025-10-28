# Passo 9 (Versão FINAL): Recriando banco, tratando path com espaco

Write-Host "Iniciando Passo 9 (Versao FINAL): Recriando banco..." -ForegroundColor Cyan

# --- 1. Parar Servidor ---
try {
    Write-Host "Parando servidor Flask..." -ForegroundColor Yellow
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*Flask*"} | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Servidor parado (ou nao estava rodando)." -ForegroundColor Green
} catch { Write-Host "Erro ao parar servidor." -ForegroundColor Gray }

# --- 2. Apagar Banco Antigo ---
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = (Get-Location).Path } # Fallback se colado
$dbFile = Join-Path $scriptDir "concurso.db"
if (Test-Path $dbFile) {
    Write-Host "Removendo '$dbFile' antigo..." -ForegroundColor Yellow
    try { Remove-Item $dbFile -Force; Write-Host "Banco antigo removido." -ForegroundColor Green }
    catch { Write-Host "ERRO ao remover '$dbFile'!" -ForegroundColor Red; return }
} else { Write-Host "'$dbFile' nao encontrado." -ForegroundColor Blue }

# --- 3. Verificar Importador ---
$importScriptPath = Join-Path $scriptDir "importar_dados.py"
if (-not (Test-Path $importScriptPath)) { Write-Host "ERRO: '$importScriptPath' nao encontrado! Execute Passo 15." -ForegroundColor Red; return }
Write-Host "'$importScriptPath' encontrado." -ForegroundColor Green

# --- 4. Executar Importador (COM ASPAS NO ARGUMENTO) ---
Write-Host "Executando '$importScriptPath'..." -ForegroundColor Yellow
Write-Host "---------------------------------"
$stdOutput = ""; $stdError = ""; $exitCode = 1 # Assume erro inicial
$stdoutLog = Join-Path $scriptDir "stdout.log"
$stderrLog = Join-Path $scriptDir "stderr.log"
try {
    $env:PYTHONIOENCODING = "utf-8"
    # *** CORREÇÃO: Coloca aspas ao redor do caminho do script Python ***
    $pythonArgs = "`"$importScriptPath`""

    # Tenta encontrar o python.exe de forma mais robusta
    $pythonExe = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $pythonExe) { throw "Comando 'python.exe' nao encontrado no PATH." }

    Write-Host "Comando Python a ser executado: $($pythonExe.Source) $pythonArgs (no diretorio: $scriptDir)" -ForegroundColor Gray

    $process = Start-Process $pythonExe.Source -ArgumentList $pythonArgs `
                 -WorkingDirectory $scriptDir `
                 -NoNewWindow -Wait -PassThru `
                 -RedirectStandardOutput $stdoutLog `
                 -RedirectStandardError $stderrLog

    $exitCode = $process.ExitCode # Guarda o código de saída real
    $stdOutput = Get-Content $stdoutLog -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    $stdError = Get-Content $stderrLog -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    Write-Host "--- Saida do Script Python ---" -ForegroundColor Magenta
    Write-Host $stdOutput
    Write-Host "--- Fim da Saida ---" -ForegroundColor Magenta

    if ($exitCode -ne 0) {
        Write-Host "---------------------------------"
        Write-Host "ERRO Python (Codigo $exitCode). Verifique saida." -ForegroundColor Yellow
        if ($stdError) { Write-Host "--- Erro Python (stderr) ---" -ForegroundColor Red; Write-Host $stdError; Write-Host "--- Fim Erro ---" -ForegroundColor Red }
    } else {
        Write-Host "---------------------------------"
        Write-Host "SUCESSO Python (Codigo 0). Verifique resumo na saida." -ForegroundColor Green
    }
} catch { Write-Host "ERRO PowerShell ao executar Python!" -ForegroundColor Red; Write-Host $_.Exception.Message }
finally {
    if (Test-Path $stdoutLog) { Remove-Item $stdoutLog -ErrorAction SilentlyContinue }
    if (Test-Path $stderrLog) { Remove-Item $stderrLog -ErrorAction SilentlyContinue }
}
Write-Host "---------------------------------"
if ($exitCode -eq 0) {
     Write-Host "Proximo passo: Analise a saida. Se o resumo indicar SUCESSO > 0, execute: python.exe app.py" -ForegroundColor Cyan
} else {
     Write-Host "A execucao do Python falhou. Corrija o problema indicado e tente rodar este script novamente." -ForegroundColor Red
}