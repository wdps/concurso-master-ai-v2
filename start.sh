#!/bin/bash
echo '🚀 INICIANDO CONCURSOIA NO RAILWAY...'
echo '📊 Porta: 5001'
echo '🔧 Verificando banco de dados...'

# Verificar se o banco existe e tem dados
if [ ! -f concursos.db ] || [  -eq 0 ]; then
    echo '🗄️ Inicializando banco de dados...'
    python init_db.py
fi

echo '🎯 Iniciando servidor Flask...'
exec python app.py
