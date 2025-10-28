#!/bin/bash
echo '🚀 INICIANDO CONCURSOIA NO RAILWAY...'
echo '📊 Porta: 5001'
echo '🔧 Iniciando servidor Python...'

# Inicializar banco de dados se não existir
if [ ! -f concursos.db ]; then
    echo '🗄️ Inicializando banco de dados...'
    python init_db.py
fi

# Executar a aplicação Python
exec python app.py
