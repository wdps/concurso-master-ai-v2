# testar_sistema_final.py - Teste completo do sistema
import requests
import json
import time

def testar_sistema_completo():
    BASE_URL = "https://concurso-master-ai-v2.up.railway.app"
    
    print("🎯 TESTE COMPLETO DO SISTEMA CONCURSOMASTER")
    print("=" * 50)
    
    try:
        # 1. Testar página inicial
        print("1. 📄 Testando página inicial...")
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("   ✅ Página inicial OK")
        else:
            print(f"   ❌ Erro {response.status_code} na página inicial")
            return False
        
        # 2. Testar página do simulado
        print("2. 🎯 Testando página do simulado...")
        response = requests.get(f"{BASE_URL}/simulado")
        if response.status_code == 200:
            print("   ✅ Página do simulado OK")
        else:
            print(f"   ❌ Erro {response.status_code} no simulado")
            return False
        
        # 3. Testar API de iniciar simulado
        print("3. 🚀 Testando API de iniciar simulado...")
        payload = {
            "quantidade": 5,
            "materias": ["Língua Portuguesa", "Matemática"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/simulado/iniciar",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ API de iniciar simulado OK")
                print(f"   📊 {data['total']} questões carregadas")
                
                # 4. Testar primeira questão
                print("4. ❓ Testando primeira questão...")
                response = requests.get(f"{BASE_URL}/questao/1")
                if response.status_code == 200:
                    print("   ✅ Página da questão 1 OK")
                    
                    # Verificar se tem alternativas
                    if 'alternativa' in response.text.lower():
                        print("   ✅ Alternativas detectadas na página")
                    else:
                        print("   ⚠️  Alternativas não detectadas")
                        
                else:
                    print(f"   ❌ Erro {response.status_code} na questão 1")
                    return False
                    
            else:
                print(f"   ❌ API retornou erro: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Erro {response.status_code} na API")
            return False
            
        # 5. Testar outras páginas
        print("5. 📚 Testando outras funcionalidades...")
        
        paginas = [
            ('/redacao', 'Redação'),
            ('/dashboard', 'Dashboard')
        ]
        
        for pagina, nome in paginas:
            response = requests.get(f"{BASE_URL}{pagina}")
            if response.status_code == 200:
                print(f"   ✅ {nome} OK")
            else:
                print(f"   ⚠️  {nome}: Erro {response.status_code}")
        
        print("=" * 50)
        print("🎉 SISTEMA TESTADO COM SUCESSO!")
        print("📍 Agora teste manualmente no navegador:")
        print(f"   🌐 {BASE_URL}/simulado")
        print("")
        print("📋 CHECKLIST PARA TESTE MANUAL:")
        print("   ✅ Configurar simulado com 10 questões")
        print("   ✅ Selecionar 2-3 matérias específicas") 
        print("   ✅ Clique em alternativas - devem ficar azuis")
        print("   ✅ Verificar resposta - deve mostrar feedback")
        print("   ✅ Navegar entre questões")
        print("   ✅ Finalizar e ver resultado com estatísticas")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        return False

if __name__ == "__main__":
    print("⏳ Aguardando aplicação reiniciar no Railway...")
    time.sleep(10)  # Aguardar 10 segundos para o deploy
    testar_sistema_completo()
