import csv

def corrigir_gabaritos():
    print("🔧 INICIANDO CORREÇÃO AUTOMÁTICA DE GABARITOS")
    print("=" * 50)
    
    # Ler todo o conteúdo
    try:
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            linhas = list(csv.reader(file, delimiter=';'))
        print("✅ Arquivo CSV carregado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return
    
    # Mostrar as linhas problemáticas primeiro
    print("\n🔍 LINHAS PROBLEMÁTICAS ENCONTRADAS:")
    print("-" * 40)
    
    for numero in [132, 157]:
        if numero-1 < len(linhas):
            linha = linhas[numero-1]
            if len(linha) > 8:
                gabarito_atual = linha[8]
                disciplina = linha[1] if len(linha) > 1 else "N/A"
                enunciado = linha[3][:80] + "..." if len(linha) > 3 and len(linha[3]) > 80 else (linha[3] if len(linha) > 3 else "N/A")
                
                print(f"\n📝 LINHA {numero}:")
                print(f"   Disciplina: {disciplina}")
                print(f"   Gabarito atual: '{gabarito_atual}'")
                print(f"   Enunciado: {enunciado}")
                
                # Mostrar alternativas
                if len(linha) > 7:
                    print("   Alternativas:")
                    for i, letra in enumerate(['A', 'B', 'C', 'D']):
                        if 4 + i < len(linha):
                            alt_texto = linha[4 + i][:60] + "..." if len(linha[4 + i]) > 60 else linha[4 + i]
                            print(f"     {letra}: {alt_texto}")
    
    # Perguntar ao usuário qual correção fazer
    print("\n🎯 CORREÇÃO DAS LINHAS:")
    print("-" * 40)
    
    correcoes = {}
    
    for numero in [132, 157]:
        if numero-1 < len(linhas) and len(linhas[numero-1]) > 8:
            linha = linhas[numero-1]
            gabarito_antigo = linha[8]
            
            while True:
                try:
                    novo_gabarito = input(f"\n📝 Qual deve ser o gabarito CORRETO para linha {numero}? (A/B/C/D): ").strip().upper()
                    
                    if novo_gabarito in ['A', 'B', 'C', 'D']:
                        correcoes[numero] = (gabarito_antigo, novo_gabarito)
                        break
                    else:
                        print("❌ Por favor, digite apenas A, B, C ou D")
                except KeyboardInterrupt:
                    print("\n❌ Correção cancelada pelo usuário")
                    return
    
    # Aplicar correções
    if correcoes:
        print("\n💾 APLICANDO CORREÇÕES...")
        for numero, (antigo, novo) in correcoes.items():
            linhas[numero-1][8] = novo
            print(f"✅ Linha {numero}: '{antigo}' → '{novo}'")
        
        # Criar backup antes de salvar
        import shutil
        from datetime import datetime
        
        backup_name = f"questoes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        shutil.copy2('questoes.csv', backup_name)
        print(f"📦 Backup criado: {backup_name}")
        
        # Salvar correções
        try:
            with open('questoes.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerows(linhas)
            print(f"\n🎉 {len(correcoes)} correções aplicadas com sucesso!")
            print("💡 Execute 'python criar_banco.py' novamente para atualizar o banco")
            
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")
    
    else:
        print("ℹ️ Nenhuma correção foi aplicada.")

def verificar_todos_gabaritos():
    """Verifica todos os gabaritos do arquivo"""
    print("\n🔍 VERIFICANDO TODOS OS GABARITOS...")
    print("-" * 40)
    
    try:
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=';')
            linhas = list(reader)
        
        problemas = []
        for numero, linha in enumerate(linhas[1:], start=2):  # Pular cabeçalho
            if len(linha) > 8:
                gabarito = linha[8].strip().upper()
                if gabarito not in ['A', 'B', 'C', 'D']:
                    problemas.append((numero, gabarito, linha[1] if len(linha) > 1 else "N/A"))
        
        if problemas:
            print(f"⚠️  Encontrados {len(problemas)} gabaritos inválidos:")
            for num, gab, disc in problemas:
                print(f"   Linha {num}: '{gab}' - {disc}")
        else:
            print("✅ Todos os gabaritos estão válidos!")
            
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🚀 CORRETOR DE GABARITOS - CONCURSOMASTER AI")
    print("=" * 50)
    
    # Verificar todos os gabaritos primeiro
    verificar_todos_gabaritos()
    
    # Perguntar se quer corrigir as linhas problemáticas
    resposta = input("\n🎯 Deseja corrigir as linhas 132 e 157? (S/N): ").strip().upper()
    
    if resposta == 'S':
        corrigir_gabaritos()
    else:
        print("❌ Correção cancelada")