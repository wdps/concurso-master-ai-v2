# TESTE RÁPIDO DO SIMULADO
# Execute quando o Railway estiver online

import requests
import json

def testar_simulado():
    print("🧪 TESTANDO SIMULADO...")
    
    # URL base - substitua pela sua URL real
    BASE_URL = "https://concurso-master-ai-v2.up.railway.app"
    
    try:
        # 1. Testar acesso à página do simulado
        print("1. 📄 Acessando página do simulado...")
        response = requests.get(f"{BASE_URL}/simulado")
        if response.status_code == 200:
            print("   ✅ Página /simulado carrega OK")
        else:
            print(f"   ❌ Erro {response.status_code} na página /simulado")
            return False
        
        # 2. Testar API de iniciar simulado
        print("2. 🚀 Testando API de iniciar simulado...")
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
                print("   ✅ API /api/simulado/iniciar funciona OK")
                print(f"   📊 {data['total']} questões carregadas")
            else:
                print(f"   ❌ API retornou erro: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Erro {response.status_code} na API")
            return False
            
        # 3. Testar rota da questão
        print("3. ❓ Testando rota da questão...")
        response = requests.get(f"{BASE_URL}/questao/1")
        if response.status_code == 200:
            print("   ✅ Rota /questao/1 funciona OK")
        else:
            print(f"   ❌ Erro {response.status_code} na rota /questao/1")
            return False
            
        print("🎉 TODOS OS TESTES PASSARAM! O SIMULADO ESTÁ FUNCIONAL!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        return False

if __name__ == "__main__":
    testar_simulado()
