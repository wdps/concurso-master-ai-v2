# ESQUEMATIZA.AI - VERSÃO CORRIGIDA TEMPORÁRIA
import sys
import os

# Correção imediata para encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Importar o app original com correções
from app import app

if __name__ == '__main__':
    print("🚀 ESQUEMATIZA.AI - VERSÃO CORRIGIDA")
    print("========================================")
    
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    if debug:
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        try:
            from waitress import serve
            print(f"🌐 Servidor Waitress rodando na porta {port}")
            serve(app, host='0.0.0.0', port=port)
        except ImportError:
            print("⚠️  Waitress não disponível, usando servidor de desenvolvimento")
            app.run(debug=False, host='0.0.0.0', port=port)
