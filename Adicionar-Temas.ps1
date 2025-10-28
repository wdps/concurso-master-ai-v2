# --- Script PowerShell para ADICIONAR Temas de Redação ---
.\sqlite3.exe = ".\sqlite3.exe"
.\concursos.db = ".\concursos.db"
if (-not (Test-Path .\sqlite3.exe)) { Write-Host "ERRO: 'sqlite3.exe' não encontrado." -ForegroundColor Red; Read-Host "Pressione Enter"; exit }
if (-not (Test-Path .\concursos.db)) { Write-Host "ERRO: Banco de dados 'concursos.db' não encontrado." -ForegroundColor Red; Read-Host "Pressione Enter"; exit }
INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('Desafios da Educação a Distância no Brasil', 'Educação', 'ENEM'); = "INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('Desafios da Educação a Distância no Brasil', 'Educação', 'ENEM');"
INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('O impacto das Fake News no processo eleitoral', 'Sociedade', 'Atualidades'); = "INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('O impacto das Fake News no processo eleitoral', 'Sociedade', 'Atualidades');"
INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('A persistência da violência contra a mulher na sociedade brasileira', 'Segurança', 'VUNESP'); = "INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('A persistência da violência contra a mulher na sociedade brasileira', 'Segurança', 'VUNESP');"
Write-Host "Inserindo Tema 1..."
& .\sqlite3.exe .\concursos.db INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('Desafios da Educação a Distância no Brasil', 'Educação', 'ENEM');
Write-Host "Inserindo Tema 2..."
& .\sqlite3.exe .\concursos.db INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('O impacto das Fake News no processo eleitoral', 'Sociedade', 'Atualidades');
Write-Host "Inserindo Tema 3..."
& .\sqlite3.exe .\concursos.db INSERT OR IGNORE INTO temas_redacao (titulo, eixo, tipo) VALUES ('A persistência da violência contra a mulher na sociedade brasileira', 'Segurança', 'VUNESP');
Write-Host "----------------------------------------------------"
Write-Host "SUCESSO: Temas de redação adicionados ao 'concursos.db'." -ForegroundColor Green
Read-Host "Pressione Enter para fechar."
