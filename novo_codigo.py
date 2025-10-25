if __name__ == "__main__":
    import uvicorn
    import os
    
    print("\n" + "="*60)
    print("🚀 CONCURSOMASTER AI PREMIUM v2.0 - SERVIDOR INICIANDO")
    print("="*60)
    
    if GEMINI_AVAILABLE:
        print("🤖 Google Gemini AI: ✅ ATIVADO")
    else:
        print("🔧 Google Gemini AI: ⚠️  Configure sua API key para recursos avançados")
    
    # CONFIGURAÇÕES PARA PRODUÇÃO (ONLINE)
    host = "0.0.0.0"  # ← MUDAR de "127.0.0.1" para "0.0.0.0"
    port = int(os.environ.get("PORT", 8000))  # ← Usar PORT do ambiente
    
    print(f"🌐 Servidor rodando em: http://{host}:{port}")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("🔍 Health Check: http://127.0.0.1:8000/health")
    print("="*60 + "\n")
    
    # MUDAR para produção:
    uvicorn.run(
        app, 
        host=host,      # ← 0.0.0.0 em vez de 127.0.0.1
        port=port,      # ← Porta do ambiente
        log_level="info"
    )
