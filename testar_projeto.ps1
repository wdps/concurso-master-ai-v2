# Script de Teste Rápido
Write-Host "🧪 EXECUTANDO TESTES RÁPIDOS..." -ForegroundColor Cyan

# Testar se o app.py tem sintaxe válida
Write-Host "`n1. Verificando sintaxe Python..." -ForegroundColor Yellow
try {
    $syntaxCheck = python -m py_compile app.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Sintaxe Python: OK" -ForegroundColor Green
    } else {
        Write-Host "❌ Erro de sintaxe:" -ForegroundColor Red
        Write-Host $syntaxCheck
        exit 1
    }
} catch {
    Write-Host "❌ Erro ao verificar sintaxe: $($_.Exception.Message)" -ForegroundColor Red
}

# Testar importações
Write-Host "`n2. Verificando importações..." -ForegroundColor Yellow
$importTest = @"
try:
    from app import app, get_db_connection
    print("✅ Importações: OK")
    
    # Testar conexão com banco
    conn = get_db_connection()
    if conn:
        print("✅ Conexão DB: OK")
        conn.close()
    else:
        print("❌ Conexão DB: FALHA")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    exit(1)
"@

try {
    $importResult = python -c $importTest 2>&1
    Write-Host $importResult
} catch {
    Write-Host "❌ Erro nas importações: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 TESTES CONCLUÍDOS!" -ForegroundColor Green
Write-Host "`n📝 PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Inicie o servidor: python app.py" -ForegroundColor White
Write-Host "2. Acesse: http://localhost:5000" -ForegroundColor White
Write-Host "3. Teste a correção de redação" -ForegroundColor White
Write-Host "4. Teste o simulado completo" -ForegroundColor White
Write-Host "`n💡 DICA: Verifique se a GEMINI_API_KEY está configurada no arquivo .env" -ForegroundColor Yellow
