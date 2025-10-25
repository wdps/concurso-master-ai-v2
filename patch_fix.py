import re
import os
import shutil

# --- CONFIGURAÇÃO ---
FILE_TO_PATCH = 'index.html'
BACKUP_FILE = 'index.html.bak'

# --- CÓDIGO NOVO (CORRIGIDO) ---

# Versão corrigida da função proximaQuestao
PROXIMA_QUESTAO_FIX = """
        async function proximaQuestao() {
            // Verifica se é a última questão
            if (questaoAtualIndice >= totalQuestoesSessao - 1) {
                // Última questão - Iniciar processo de finalização
                
                // 1. Parar cronômetros
                stopTimer();
                stopCronometroSimulado();
                
                // 2. Mostrar indicador de salvamento
                document.getElementById('question-content-container').innerHTML = `
                    <div style="padding: 60px; text-align: center; color: var(--color-secondary); font-size: 1.2em;">
                        <div class="loading-spinner" style="border-top-color: var(--color-primary); margin: 0 auto 20px auto;"></div>
                        💾 Registrando seu resultado...
                    </div>
                `;
                // Esconder botão de finalizar (pois já estamos finalizando)
                document.getElementById('btn-finalizar-sessao').style.display = 'none';

                // 3. Registrar o histórico (se for simulado)
                if (modoSessao === 'simulado') {
                    await registrarHistoricoSimulado();
                }
                
                // 4. Mostrar a tela de resultados
                mostrarFim();

            } else {
                // Se não for a última, apenas avança
                questaoAtualIndice++;
                carregarQuestao();
            }
        }
"""

# Versão corrigida da função finalizarSessaoAntecipada
FINALIZAR_SESSAO_FIX = """
        async function finalizarSessaoAntecipada() {
            if (confirm("🎯 Tem certeza que deseja finalizar a sessão agora? Sua nota será calculada com base nas questões respondidas.")) {
                
                // 1. Parar cronômetros
                stopTimer();
                stopCronometroSimulado();
                
                // 2. Mostrar indicador de salvamento
                document.getElementById('question-content-container').innerHTML = `
                    <div style="padding: 60px; text-align: center; color: var(--color-secondary); font-size: 1.2em;">
                        <div class="loading-spinner" style="border-top-color: var(--color-primary); margin: 0 auto 20px auto;"></div>
                        💾 Registrando seu resultado...
                    </div>
                `;
                // Esconder botão de finalizar
                document.getElementById('btn-finalizar-sessao').style.display = 'none';

                // 3. Registrar histórico (se for simulado)
                if (modoSessao === 'simulado') {
                    await registrarHistoricoSimulado();
                }
                
                // 4. Mostrar tela de resultados
                mostrarFim();
            }
        }
"""

# Versão corrigida da função mostrarFim
MOSTRAR_FIM_FIX = """
        // --- TELA DE RESULTADO FINAL PREMIUM ---
        function mostrarFim() {
            // REMOVIDO: stopTimer() e stopCronometroSimulado()
            // (Agora são chamados ANTES de salvar o histórico)
            
            const percentualAcertos = totalQuestoesSessao > 0 ? (acertosSessao / totalQuestoesSessao) * 100 : 0;
            const percentualPontuacao = notaMaximaSessao > 0 ? (pontuacaoSessao / notaMaximaSessao) * 100 : 0;
            const tempoMedio = tempoPorQuestao.length > 0 ? 
                tempoPorQuestao.reduce((a, b) => a + b) / tempoPorQuestao.length : 0;

            const resultadoHTML = `
                <div class="resultado-final">
                    <h2>🎉 ${modoSessao === 'estudo' ? 'Sessão de Estudo' : 'Simulado'} Concluído!</h2>
                    <span class="mode-tag">${modoSessao === 'estudo' ? '📚 Modo Estudo' : '🎯 Modo Simulado'}</span>
                    
                    <strong class="score">${percentualPontuacao.toFixed(1)}%</strong>
                    
                    <div class="metricas-container">
                        <div class="metrica">
                            <span class="valor">${acertosSessao}/${totalQuestoesSessao}</span>
                            <span class="label">✅ Questões Corretas</span>
                        </div>
                        <div class="metrica">
                            <span class="valor">${formatTime(totalTimeElapsed)}</span>
                            <span class="label">⏱️ Tempo Total</span>
                        </div>
                        <div class="metrica">
                            <span class="valor">${tempoMedio.toFixed(1)}s</span>
                            <span class="label">📊 Tempo Médio/Q</span>
                        </div>
                        <div class="metrica">
                            <span class="valor">${pontuacaoSessao.toFixed(1)}</span>
                            <span class="label">⚖️ Pontuação Total</span>
                        </div>
                    </div>
                    
                    <div class="analise-final">
                        <h3>📈 Análise do Desempenho</h3>
                        <p>${gerarAnaliseDesempenho(percentualPontuacao, tempoMedio)}</p>
                        <p><strong>🎯 Recomendação:</strong> ${gerarRecomendacao(percentualPontuacao)}</p>
                    </div>
                    
                    <div style="margin-top: 30px;">
                        <button onclick="window.location.reload()" style="
                            background: var(--gradient-primary);
                            color: white;
                            padding: 15px 30px;
                            border: none;
                            border-radius: 10px;
                            font-size: 1.1em;
                            cursor: pointer;
                            margin: 0 10px;
                        ">🔄 Nova Sessão</button>
                        
                        <button onclick="window.location.href='dashboard.html'" style="
                            background: var(--gradient-success);
                            color: white;
                            padding: 15px 30px;
                            border: none;
                            border-radius: 10px;
                            font-size: 1.1em;
                            cursor: pointer;
                            margin: 0 10px;
                        ">📊 Ver Dashboard</button>
                    </div>
                </div>
            `;
            
            document.getElementById('question-content-container').innerHTML = resultadoHTML;
            
            // Garante que o botão de finalizar sessão seja ocultado
            document.getElementById('btn-finalizar-sessao').style.display = 'none';
        }
"""

# --- LÓGICA DO PATCH ---

def patch_file():
    print(f"--- Iniciando patch para {FILE_TO_PATCH} ---")

    # 1. Verificar se o arquivo existe
    if not os.path.exists(FILE_TO_PATCH):
        print(f"❌ ERRO: Arquivo '{FILE_TO_PATCH}' não encontrado.")
        print("Certifique-se de que este script está na mesma pasta que o seu index.html")
        return

    # 2. Criar backup
    try:
        shutil.copyfile(FILE_TO_PATCH, BACKUP_FILE)
        print(f"✅ Backup criado com sucesso: {BACKUP_FILE}")
    except Exception as e:
        print(f"❌ ERRO ao criar backup: {e}")
        return

    # 3. Ler o conteúdo do arquivo
    try:
        with open(FILE_TO_PATCH, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ ERRO ao ler o arquivo: {e}")
        return

    # 4. Definir os padrões (Regex) para encontrar as funções antigas
    # (re.DOTALL faz o '.' incluir quebras de linha)
    # (re.MULTILINE faz o '^' e '$' funcionarem em cada linha)
    patterns = {
        "proximaQuestao": (
            re.compile(r"async function proximaQuestao\(\) \{.*?\n\s*\}", re.DOTALL | re.MULTILINE),
            PROXIMA_QUESTAO_FIX
        ),
        "finalizarSessaoAntecipada": (
            re.compile(r"async function finalizarSessaoAntecipada\(\) \{.*?\n\s*\}", re.DOTALL | re.MULTILINE),
            FINALIZAR_SESSAO_FIX
        ),
        "mostrarFim": (
            re.compile(r"function mostrarFim\(\) \{.*?\n\s*\}", re.DOTALL | re.MULTILINE),
            MOSTRAR_FIM_FIX
        )
    }

    # 5. Aplicar as substituições
    modified_content = content
    replacements_made = 0

    for func_name, (pattern, fix) in patterns.items():
        if pattern.search(modified_content):
            modified_content = pattern.sub(fix, modified_content, count=1)
            print(f"✅ Função '{func_name}' corrigida.")
            replacements_made += 1
        else:
            print(f"⚠️ AVISO: Função '{func_name}' não encontrada. Pode já ter sido corrigida.")

    # 6. Salvar o arquivo modificado
    if replacements_made > 0:
        try:
            with open(FILE_TO_PATCH, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"\n🎉 Sucesso! O arquivo '{FILE_TO_PATCH}' foi corrigido.")
        except Exception as e:
            print(f"❌ ERRO ao salvar o arquivo corrigido: {e}")
            print(f"Seu arquivo original está salvo em: {BACKUP_FILE}")
    else:
        print("\nNenhuma correção foi aplicada. O arquivo não foi modificado.")

if __name__ == "__main__":
    patch_file()