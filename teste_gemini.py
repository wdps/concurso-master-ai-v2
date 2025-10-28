import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY não encontrada")
    exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ API configurada")
    
    # Listar modelos - CONVERTER para lista
    models_list = list(genai.list_models())
    print(f"📊 Total de modelos: {len(models_list)}")
    
    # Filtrar modelos generativos
    generative_models = []
    for model in models_list:
        if 'generateContent' in model.supported_generation_methods:
            generative_models.append(model.name)
    
    print(f"🎯 Modelos generativos ({len(generative_models)}):")
    for model in generative_models[:5]:  # Mostrar apenas os 5 primeiros
        print(f"  - {model}")
    
    if generative_models:
        # Testar com modelos específicos
        test_models = [
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-001", 
            "models/gemini-pro-latest",
            "models/gemini-flash-latest"
        ]
        
        for test_model in test_models:
            if test_model in generative_models:
                print(f"🧪 Testando com: {test_model}")
                try:
                    model = genai.GenerativeModel(test_model)
                    response = model.generate_content("Responda apenas com: OK")
                    print(f"✅ {test_model} funcionando: {response.text}")
                    break
                except Exception as e:
                    print(f"❌ {test_model} falhou: {e}")
    else:
        print("❌ Nenhum modelo generativo encontrado!")
        
except Exception as e:
    print(f"❌ Erro geral: {e}")
    import traceback
    traceback.print_exc()
