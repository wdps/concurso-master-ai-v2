// CONCURSOIA - Sistema Inteligente de Estudos para Concursos

let simuladoAtual = null;
let questaoAtual = null;
let dadosDisciplinas = []; 

// Exposição Global de Funções
const GlobalFunctions = {
    navegarPara: navegarPara,
    iniciarSimulado: iniciarSimulado,
    selecionarDisciplina: selecionarDisciplina,
    responderQuestao: responderQuestao,
    mudarQuestao: mudarQuestao,
    finalizarSimulado: finalizarSimulado,
    corrigirRedacao: corrigirRedacao,
    voltarInicio: voltarInicio
};

for (const key in GlobalFunctions) {
    window[key] = GlobalFunctions[key];
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 ConcursoIA inicializado');
    
    carregarConteudoInicial(); 

    document.querySelectorAll('.tela').forEach(t => {
        t.classList.add('hidden');
    });

    const currentPath = window.location.pathname;
    if (currentPath.includes('simulado')) {
        navegarPara('tela-simulado');
    } else if (currentPath.includes('redacao')) {
        navegarPara('tela-redacao');
    } else if (currentPath.includes('dashboard')) {
        navegarPara('tela-dashboard');
    } else {
        navegarPara('tela-inicio');
    }
});

// Carregar conteúdo inicial
function carregarConteudoInicial() {
    carregarMaterias(); 
    carregarTemasRedacao(); 
    carregarDashboard(); 
}

// Navegação
function navegarPara(tela) {
    document.querySelectorAll('.tela').forEach(t => {
        t.classList.add('hidden');
    });
    
    const telaElement = document.getElementById(tela);
    if (telaElement) {
        telaElement.classList.remove('hidden');
    } else {
        console.error(`Tela não encontrada: ${tela}`);
        return;
    }
    
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    const navTab = document.querySelector(`.nav-tab[onclick="navegarPara('${tela}')"]`);
    if (navTab) {
        navTab.classList.add('active');
    }
    
    if (tela === 'tela-simulado') {
        const selecaoSimulado = document.getElementById('selecao-simulado');
        const simuladoAtivo = document.getElementById('simulado-ativo');
        const resultado = document.getElementById('tela-resultado');

        if (selecaoSimulado) selecaoSimulado.classList.remove('hidden');
        if (simuladoAtivo) simuladoAtivo.classList.add('hidden'); 
        if (resultado) resultado.classList.add('hidden'); 
        
        carregarMaterias(); 
    } else if (tela === 'tela-redacao') {
        carregarTemasRedacao(); 
    } else if (tela === 'tela-dashboard') {
        carregarDashboard();
    }
}

// ==========================================================
// FUNÇÕES AUXILIARES E UI
// ==========================================================

function mostrarLoading(containerId, mensagem = 'Carregando...') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="text-center">
            <div class="loading" style="margin: 0 auto;"></div>
            <p>${mensagem}</p>
        </div>`;
    }
}

function mostrarErro(containerId, mensagem) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="feedback erro">
            <h4>❌ Erro</h4>
            <p>${mensagem}</p>
        </div>`;
    }
}

function mostrarTelaSimuladoAtivo() {
    const selecaoSimulado = document.getElementById('selecao-simulado');
    const simuladoAtivo = document.getElementById('simulado-ativo');
    if (selecaoSimulado) selecaoSimulado.classList.add('hidden');
    if (simuladoAtivo) simuladoAtivo.classList.remove('hidden');
}

function atualizarProgresso(indice, total) {
    const progresso = ((indice + 1) / total) * 100;
    const progressBar = document.getElementById('progresso-simulado');
    if (progressBar) {
        progressBar.style.width = `${progresso}%`;
    }
}

function desabilitarInteracaoQuestao() {
    document.querySelectorAll('.alternativas-container input[type="radio"]').forEach(input => {
        input.disabled = true;
    });
    const btnResponder = document.querySelector('.simulado-navigation .btn-primary');
    if (btnResponder) {
        btnResponder.disabled = true;
    }
}

function habilitarInteracaoQuestao() {
    document.querySelectorAll('.alternativas-container input[type="radio"]').forEach(input => {
        input.disabled = false;
    });
    const btnResponder = document.querySelector('.simulado-navigation .btn-primary');
    if (btnResponder) {
        btnResponder.disabled = false;
    }
}

// CORREÇÃO: Justificativa apenas para erros
function mostrarFeedbackQuestao(data) {
    const feedback = document.getElementById('feedback-questao');
    if (feedback) {
        let feedbackHTML = `
            <div class="feedback ${data.acertou ? 'acerto' : 'erro'}">
                <h4>${data.acertou ? '✅ Acertou!' : '❌ Errou!'}</h4>
                <p><strong>Resposta correta:</strong> ${data.resposta_correta}</p>
        `;
        
        // Só mostra justificativa se errou
        if (!data.acertou && data.justificativa) {
            feedbackHTML += `<p><strong>Explicação:</strong> ${data.justificativa}</p>`;
        }
        
        feedbackHTML += `</div>`;
        feedback.innerHTML = feedbackHTML;
        feedback.style.display = 'block';
    }
}

// ==========================================================
// FUNÇÕES DO SIMULADO
// ==========================================================

async function carregarMaterias() {
    try {
        mostrarLoading('materias-container', 'Carregando disciplinas...');
        
        const response = await fetch('/api/materias');
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`❌ ERRO HTTP ${response.status}:`, errorText);
            mostrarErro('materias-container', `Erro ao carregar (Status: ${response.status}). Verifique o console do servidor.`);
            return;
        }

        const data = await response.json();
        
        if (data.success) {
            dadosDisciplinas = data.disciplinas; 
            exibirDisciplinas(dadosDisciplinas);
        } else {
            console.error('❌ ERRO RETORNADO PELO BACKEND:', data.error);
            mostrarErro('materias-container', 'Erro do Servidor: ' + data.error);
        }
    } catch (error) {
        console.error('❌ ERRO CRÍTICO JS (Provavelmente rede/DB):', error);
        mostrarErro('materias-container', 'Falha na comunicação com o servidor. Consulte o console (F12).');
    }
}

function exibirDisciplinas(disciplinas) {
    const container = document.getElementById('materias-container');
    if (!container) return;

    if (disciplinas.length === 0) {
        mostrarErro('materias-container', 'Nenhuma Disciplina encontrada no banco de dados. Verifique a importação do CSV.');
        return;
    }

    let html = '';
    
    html += `<div class="card" style="margin-top: 25px;">
        <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Disciplinas (Caixas de Conhecimento)</h3>
        <p style="margin-bottom: 15px; color: #555;">Selecione uma ou mais disciplinas. Todas as matérias (subáreas) serão incluídas.</p>
        <div class="materias-grid">`;
    
    disciplinas.forEach(disciplinaData => {
        html += `<div class="materia-item" onclick="selecionarDisciplina(this)">
            <div class="materia-checkbox">
                <input type="checkbox" value="${disciplinaData.disciplina}">
                <label>
                    <strong>${disciplinaData.disciplina}</strong>
                    <span>(${disciplinaData.total_questoes} questões totais)</span>
                </label>
            </div>
        </div>`;
    });
    
    html += '</div></div>';
    container.innerHTML = html;
}

function selecionarDisciplina(elemento) {
    const checkbox = elemento.querySelector('input[type="checkbox"]');
    checkbox.checked = !checkbox.checked;
    
    if (checkbox.checked) {
        elemento.classList.add('selected');
    } else {
        elemento.classList.remove('selected');
    }
}

async function iniciarSimulado() {
    const disciplinasSelecionadas = Array.from(
        document.querySelectorAll('#materias-container input[type="checkbox"]:checked')
    ).map(cb => cb.value);
    
    const quantidade = document.getElementById('quantidade-questoes').value || 10;
    
    if (disciplinasSelecionadas.length === 0) {
        alert('Selecione pelo menos uma Disciplina!');
        return;
    }

    let materiasParaSimulado = [];
    
    dadosDisciplinas.forEach(discData => {
        if (disciplinasSelecionadas.includes(discData.disciplina)) {
            discData.materias.forEach(materia => {
                materiasParaSimulado.push(materia.nome);
            });
        }
    });

    materiasParaSimulado = [...new Set(materiasParaSimulado)];
    
    let limiteQuantidade = parseInt(quantidade);
    if (limiteQuantidade >= 295) {
        let totalDisponivel = dadosDisciplinas
            .filter(d => disciplinasSelecionadas.includes(d.disciplina))
            .reduce((sum, d) => sum + d.total_questoes, 0);
        limiteQuantidade = totalDisponivel; 
    }
    
    try {
        const selecaoContainer = document.getElementById('selecao-simulado');
        const simuladoAtivoContainer = document.getElementById('simulado-ativo');

        if (selecaoContainer) selecaoContainer.classList.add('hidden');
        if (simuladoAtivoContainer) {
             simuladoAtivoContainer.classList.remove('hidden');
             simuladoAtivoContainer.innerHTML = '<div class="card"><div class="text-center"><div class="loading"></div><p>Buscando questões no banco...</p></div></div>';
        } else {
            console.error("Contêiner do simulado ativo não encontrado.");
            return;
        }

        const response = await fetch('/api/simulado/iniciar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                materias: materiasParaSimulado, 
                quantidade: limiteQuantidade 
            })
        });
        
        const data = await response.json();

        if (data.success) {
            simuladoAtual = data;
            mostrarTelaSimuladoAtivo();
            
            const questaoCardHtml = `
                <div class="card questao-container">
                    <div class="questao-header">
                        <div>
                            <h3 id="questao-numero">Questão 1 de 10</h3>
                            <div class="questao-info">
                                <span class="questao-tag" id="questao-disciplina">-</span>
                                <span class="questao-tag" id="questao-materia">-</span>
                                <span class="questao-tag" id="questao-dificuldade">-</span>
                            </div>
                        </div>
                    </div>

                    <div style="background: #ecf0f1; border-radius: 10px; height: 10px; margin: 20px 0;">
                        <div id="progresso-simulado" style="background: #3498db; height: 100%; border-radius: 10px; width: 0%; transition: width 0.3s ease;"></div>
                    </div>

                    <div class="questao-content-wrapper">
                        <div class="questao-enunciado-container">
                            <div class="questao-enunciado" id="questao-enunciado">
                                Carregando questão...
                            </div>
                        </div>
                        
                        <div class="questao-auxiliar" id="questao-auxiliar">
                            <!-- Dica e Fórmula serão inseridas aqui -->
                        </div>
                    </div>

                    <div class="alternativas-container" id="questao-alternativas">
                    </div>

                    <div id="feedback-questao" style="display: none;"></div>

                    <div class="simulado-navigation">
                        <div style="display: flex; gap: 10px;">
                            <button id="btn-anterior" class="btn" onclick="mudarQuestao(-1)" disabled>⬅️ Anterior</button>
                            <button id="btn-proximo" class="btn" onclick="mudarQuestao(1)">Próxima ➡️</button>
                        </div>
                        
                        <button class="btn btn-primary btn-large" onclick="responderQuestao()">✅ Responder</button>
                        
                        <button id="btn-finalizar-geral" class="btn btn-danger" onclick="finalizarSimulado()">🏁 Finalizar Agora</button> 
                    </div>
                </div>`;
                
            if (simuladoAtivoContainer) {
                 simuladoAtivoContainer.innerHTML = questaoCardHtml;
            } else {
                console.error("Falha fatal ao montar a estrutura da questão.");
                carregarMaterias();
                return;
            }

            exibirQuestao(data.questao, data.indice_atual, data.total_questoes, null); 
        } else {
            alert('Erro ao iniciar simulado: ' + (data.error || 'Erro desconhecido.'));
            if (selecaoContainer) selecaoContainer.classList.remove('hidden');
            if (simuladoAtivoContainer) simuladoAtivoContainer.classList.add('hidden');
            carregarMaterias(); 
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao iniciar simulado');
        carregarMaterias(); 
    }
}

async function mudarQuestao(direcao) {
    const indiceAtual = simuladoAtual?.indice_atual || 0; 
    const novoIndice = indiceAtual + direcao;
    
    try {
        const response = await fetch(`/api/simulado/questao/${novoIndice}`);
        const data = await response.json();
        
        if (data.success) {
            simuladoAtual = data;
            exibirQuestao(data.questao, novoIndice, data.total_questoes, data.resposta_anterior); 
        } else {
            alert('Erro: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao navegar');
    }
}

async function responderQuestao() {
    const alternativaSelecionada = document.querySelector('input[name="alternativa"]:checked');
    
    if (!alternativaSelecionada) {
        alert('Selecione uma alternativa!');
        return;
    }
    
    try {
        const response = await fetch('/api/simulado/responder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                questao_id: questaoAtual.id,
                alternativa: alternativaSelecionada.value
            })
        });
        
        if (response.status === 400) {
            const errorData = await response.json();
            alert(errorData.error); 
            if (errorData.error.includes("já foi respondida")) {
                mudarQuestao(0);
            }
            return;
        }

        const data = await response.json();
        
        if (data.success) {
            mostrarFeedbackQuestao(data);
            desabilitarInteracaoQuestao(); 
        } else {
            alert('Erro: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao responder');
    }
}

async function finalizarSimulado() {
    if (!confirm("Tem certeza que deseja finalizar o simulado agora? Todas as questões não respondidas serão consideradas erradas.")) {
        return;
    }

    const simuladoContainer = document.getElementById('simulado-ativo');
    
    document.querySelectorAll('.simulado-navigation .btn').forEach(btn => btn.disabled = true);
    if (simuladoContainer) { 
        simuladoContainer.innerHTML = '<div class="text-center"><div class="loading"></div><p>Finalizando simulado e gerando resultados...</p></div>';
    }
    
    try {
        const response = await fetch('/api/simulado/finalizar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            alert('Erro ao finalizar simulado: ' + (errorData.error || 'Erro desconhecido.'));
            console.error('Erro de Finalização:', errorData);
            voltarInicio();
            return;
        }

        const data = await response.json();

        if (data.success) {
            exibirResultado(data.relatorio);
            const simuladoAtivo = document.getElementById('simulado-ativo');
            const resultado = document.getElementById('tela-resultado');
            if (simuladoAtivo) simuladoAtivo.classList.add('hidden');
            if (resultado) resultado.classList.remove('hidden');
            carregarDashboard();
        } else {
            alert('Erro ao finalizar simulado: ' + (data.error || 'Erro desconhecido.'));
            voltarInicio();
        }
    } catch (error) {
        console.error('Erro na requisição de finalização:', error);
        alert('Erro de rede ao finalizar simulado.');
        voltarInicio();
    } finally {
         document.querySelectorAll('.simulado-navigation .btn').forEach(btn => btn.disabled = false);
    }
}

function exibirQuestao(questao, indice, total, respostaAnterior) {
    questaoAtual = questao;
    
    const elementos = {
        'questao-numero': `Questão ${indice + 1} de ${total}`,
        'questao-disciplina': questao.disciplina,
        'questao-materia': questao.materia,
        'questao-dificuldade': questao.dificuldade
    };
    
    for (const [id, texto] of Object.entries(elementos)) {
        const elemento = document.getElementById(id);
        if (elemento) {
            elemento.textContent = texto;
        }
    }
    
    const enunciadoElement = document.getElementById('questao-enunciado');
    if (enunciadoElement) {
        enunciadoElement.innerHTML = questao.enunciado;
    }
    
    // Exibir dica e fórmula ao lado do enunciado
    const auxiliarElement = document.getElementById('questao-auxiliar');
    if (auxiliarElement) {
        let auxiliarHTML = '';
        
        if (questao.dica) {
            auxiliarHTML += `
                <div class="auxiliar-item dica-auxiliar">
                    <div class="auxiliar-header">
                        <span class="auxiliar-icon">💡</span>
                        <h4>Dica</h4>
                    </div>
                    <div class="auxiliar-content">
                        ${questao.dica}
                    </div>
                </div>
            `;
        }
        
        if (questao.formula) {
            auxiliarHTML += `
                <div class="auxiliar-item formula-auxiliar">
                    <div class="auxiliar-header">
                        <span class="auxiliar-icon">📐</span>
                        <h4>Fórmula</h4>
                    </div>
                    <div class="auxiliar-content">
                        ${questao.formula}
                    </div>
                </div>
            `;
        }
        
        if (!questao.dica && !questao.formula) {
            auxiliarHTML = '<div class="auxiliar-vazio">Nenhuma informação auxiliar para esta questão.</div>';
        }
        
        auxiliarElement.innerHTML = auxiliarHTML;
    }
    
    const alternativasContainer = document.getElementById('questao-alternativas');
    if (alternativasContainer) {
        alternativasContainer.innerHTML = '';
        
        Object.entries(questao.alternativas).forEach(([letra, texto]) => {
            const alternativaDiv = document.createElement('div');
            alternativaDiv.className = 'alternativa';
            
            const isSelected = respostaAnterior && (respostaAnterior.alternativa_escolhida === letra);
            
            const disabledAttr = respostaAnterior ? 'disabled' : '';

            alternativaDiv.innerHTML = `
                <input type="radio" name="alternativa" id="alt-${letra}" value="${letra}" ${isSelected ? 'checked' : ''} ${disabledAttr}>
                <label for="alt-${letra}">
                    <span class="letra-alternativa">${letra.toUpperCase()})</span>
                    ${texto}
                </label>
            `;
            alternativaDiv.onclick = function() {
                if (respostaAnterior) return; 
                this.querySelector('input[type="radio"]').checked = true;
                alternativasContainer.querySelectorAll('.alternativa').forEach(alt => {
                    alt.classList.remove('selected');
                });
                this.classList.add('selected');
            };
            
            if (isSelected) {
                alternativaDiv.classList.add('selected');
            }
            
            alternativasContainer.appendChild(alternativaDiv);
        });
    }
    
    if (respostaAnterior) {
        const feedbackData = {
             acertou: respostaAnterior.acertou,
             resposta_correta: questao.resposta_correta,
             justificativa: questao.justificativa
        };
        mostrarFeedbackQuestao(feedbackData); 
        desabilitarInteracaoQuestao(); 
    } else {
        const feedbackQuestao = document.getElementById('feedback-questao');
        if(feedbackQuestao) feedbackQuestao.style.display = 'none'; 
        habilitarInteracaoQuestao(); 
    }
    
    const btnAnterior = document.getElementById('btn-anterior');
    if (btnAnterior) {
        btnAnterior.disabled = indice === 0;
    }
    
    const btnProximo = document.getElementById('btn-proximo');
    if (btnProximo) {
        if (indice < total - 1) {
            btnProximo.style.display = 'inline-block';
        } else {
            btnProximo.style.display = 'none';
        }
    }
    
    const btnFinalizarGeral = document.getElementById('btn-finalizar-geral');
    if (btnFinalizarGeral) { 
        btnFinalizarGeral.style.display = 'inline-block';
    }

    atualizarProgresso(indice, total);
}

function exibirResultado(relatorio) {
    document.getElementById('resultado-acertos').textContent = 
        `${relatorio.total_acertos}/${relatorio.total_questoes}`;
    document.getElementById('resultado-percentual').textContent = 
        `${relatorio.percentual_acerto}%`;
    document.getElementById('resultado-nota').textContent = 
        `${relatorio.nota_final}%`;
}

// ==========================================================
// REDAÇÃO APRIMORADA
// ==========================================================

async function carregarTemasRedacao() {
    try {
        const response = await fetch('/api/redacao/temas');
        
        if (!response.ok) {
             console.error("Erro ao carregar temas de redação:", response.status);
             return;
        }

        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('temas-redacao');
            if (!select) return; 

            select.innerHTML = '<option value="">Selecione um tema</option>';
            
            data.temas.forEach(tema => {
                let titulo = tema.titulo ? tema.titulo.trim() : "Tema sem título";
                
                titulo = titulo.replace(/Ã£/g, 'ã').replace(/Ã§/g, 'ç').replace(/Ã¡/g, 'á').replace(/Ã©/g, 'é').replace(/Ã³/g, 'ó').replace(/Ãº/g, 'ú').replace(/Ãµ/g, 'õ');
                titulo = titulo.replace(/Ãª/g, 'ê').replace(/Ãª/g, 'ê').replace(/Ãª/g, 'ê').replace(/Ãª/g, 'ê');
                
                titulo = titulo.replace(/\s*\([^)]*\)$/, '');

                const option = document.createElement('option');
                option.value = titulo;
                option.textContent = titulo;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro na API de Redação:', error);
    }
}

async function corrigirRedacao() {
    const temaSelect = document.getElementById('temas-redacao');
    const textoRedacao = document.getElementById('texto-redacao').value;
    
    if (!temaSelect.value) {
        alert('Selecione um tema!');
        return;
    }
    
    if (!textoRedacao.trim()) {
        alert('Digite sua redação!');
        return;
    }
    
    const btnCorrigir = document.getElementById('btn-corrigir');
    const textoOriginal = btnCorrigir ? btnCorrigir.innerHTML : '🤖 Corrigir Redação';
    if(btnCorrigir) {
        btnCorrigir.innerHTML = '<span class="loading"></span> Corrigindo...';
        btnCorrigir.disabled = true;
    }
    
    try {
        const response = await fetch('/api/redacao/corrigir-gemini', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tema: temaSelect.value,
                texto: textoRedacao
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            exibirCorrecaoRedacao(data.correcao);
        } else {
            alert('Erro: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao corrigir');
    } finally {
        if(btnCorrigir) {
            btnCorrigir.innerHTML = textoOriginal;
            btnCorrigir.disabled = false;
        }
    }
}

function exibirCorrecaoRedacao(correcao) {
    const resultadoDiv = document.getElementById('resultado-correcao');
    
    let html = `
        <div class="card resultado-header">
            <div class="nota-container">
                <h3>📊 Resultado da Correção</h3>
                <div class="nota-final">${correcao.nota_final}/100</div>
                <div class="nota-descricao">
                    ${correcao.nota_final >= 80 ? '🎉 Excelente! Nível competitivo para concursos!' : 
                      correcao.nota_final >= 60 ? '👍 Bom desempenho, mas pode melhorar!' : 
                      '📝 Precisa de mais prática. Continue estudando!'}
                </div>
            </div>
        </div>
        
        <div class="card">
            <h4>📝 Análise por Competências:</h4>
    `;
    
    correcao.analise_competencias.forEach(comp => {
        const percentual = (comp.nota / 20) * 100;
        html += `
            <div class="competencia-item">
                <div class="competencia-header">
                    <h5>${comp.competencia}</h5>
                    <span class="nota-competencia">${comp.nota}/20</span>
                </div>
                <div class="progress-bar-competencia">
                    <div class="progress-fill" style="width: ${percentual}%"></div>
                </div>
                <p class="comentario-competencia">${comp.comentario}</p>
            </div>
        `;
    });
    
    html += `
        </div>
        
        <div class="analise-grid">
            <div class="card">
                <h4>✅ Pontos Fortes:</h4>
                <ul class="lista-pontos">
                    ${correcao.pontos_fortes.map(ponto => `<li>${ponto}</li>`).join('')}
                </ul>
            </div>
            
            <div class="card">
                <h4>📝 Pontos a Melhorar:</h4>
                <ul class="lista-pontos">
                    ${correcao.pontos_fracos.map(ponto => `<li>${ponto}</li>`).join('')}
                </ul>
            </div>
        </div>
        
        <div class="card">
            <h4>💡 Sugestões de Melhoria:</h4>
            <ul class="lista-pontos">
                ${correcao.sugestoes_melhoria.map(sugestao => `<li>${sugestao}</li>`).join('')}
            </ul>
        </div>
        
        <div class="card dicas-redacao">
            <h4>🎯 Dicas Específicas para Concursos:</h4>
            <ul class="lista-pontos">
                ${correcao.dicas_concursos ? correcao.dicas_concursos.map(dica => `<li>${dica}</li>`).join('') : `
                    <li>Mantenha a estrutura dissertativa clara (introdução, desenvolvimento, conclusão)</li>
                    <li>Use argumentos sólidos e fundamentados com dados quando possível</li>
                    <li>Cuidado com a norma culta - concursos são rigorosos na gramática</li>
                    <li>Pratique a gestão do tempo (cerca de 5min para planejamento, 25min para escrita, 5min para revisão)</li>
                    <li>Revise cuidadosamente antes de entregar, focando em concordância e pontuação</li>
                `}
            </ul>
        </div>
    `;
    
    if (resultadoDiv) {
        resultadoDiv.innerHTML = html;
        resultadoDiv.classList.remove('hidden');
        resultadoDiv.scrollIntoView({ behavior: 'smooth' });
    }
}

// ==========================================================
// DASHBOARD APRIMORADO
// ==========================================================

async function carregarDashboard() {
    try {
        const response = await fetch('/api/dashboard/estatisticas');
        const data = await response.json();
        
        if (data.success) {
            exibirDashboard(data);
        }
    } catch (error) {
        console.error('Erro:', error);
    }
}

function exibirDashboard(data) {
    const container = document.getElementById('dashboard-content');
    
    let html = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">${data.total_simulados}</div>
                <div class="stat-label">Simulados Realizados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${data.total_questoes_respondidas}</div>
                <div class="stat-label">Questões Respondidas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${data.total_acertos}</div>
                <div class="stat-label">Total de Acertos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${data.media_geral}%</div>
                <div class="stat-label">Média Geral</div>
            </div>
        </div>
        
        <div class="performance-grid">
            <div class="card performance-card">
                <h4>🎯 Desempenho</h4>
                <div class="performance-stats">
                    <div class="performance-item">
                        <span class="performance-label">Melhor Desempenho:</span>
                        <span class="performance-value success">${data.melhor_desempenho}%</span>
                    </div>
                    <div class="performance-item">
                        <span class="performance-label">Pior Desempenho:</span>
                        <span class="performance-value danger">${data.pior_desempenho}%</span>
                    </div>
                </div>
            </div>
            
            <div class="card evolution-card">
                <h4>📈 Evolução Recente</h4>
                <div class="evolution-chart">
                    ${data.evolucao.length > 0 ? data.evolucao.map((simulado, index) => `
                        <div class="evolution-item">
                            <span class="evolution-label">Simulado ${index + 1}</span>
                            <div class="evolution-bar">
                                <div class="evolution-fill" style="width: ${simulado.nota_final}%"></div>
                            </div>
                            <span class="evolution-value">${simulado.nota_final}%</span>
                        </div>
                    `).join('') : '<p class="no-data">Nenhum dado disponível</p>'}
                </div>
            </div>
        </div>
    `;
    
    if (data.historico_recente && data.historico_recente.length > 0) {
        html += `
            <div class="card historico-card">
                <h4>📋 Histórico de Simulados</h4>
                <div class="table-container">
                    <table class="historico-table">
                        <thead>
                            <tr>
                                <th>Data</th>
                                <th>Questões</th>
                                <th>Acertos</th>
                                <th>Desempenho</th>
                                <th>Nota</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.historico_recente.map((simulado, index) => {
                                const dataFormatada = new Date(simulado.data_fim).toLocaleDateString('pt-BR');
                                return `
                                    <tr>
                                        <td>${dataFormatada}</td>
                                        <td>${simulado.total_questoes}</td>
                                        <td>${simulado.total_acertos}</td>
                                        <td>
                                            <div class="progress-bar-small">
                                                <div class="progress-fill" style="width: ${simulado.percentual_acerto}%"></div>
                                            </div>
                                        </td>
                                        <td class="nota-cell ${simulado.nota_final >= 70 ? 'nota-boa' : 'nota-ruim'}">
                                            ${simulado.nota_final}%
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="card">
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <h4>Nenhum simulado realizado</h4>
                    <p>Comece fazendo seu primeiro simulado para ver suas estatísticas aqui!</p>
                    <button class="btn btn-primary" onclick="navegarPara('tela-simulado')">Iniciar Simulado</button>
                </div>
            </div>
        `;
    }
    
    if (container) container.innerHTML = html;
}

function voltarInicio() {
    document.querySelectorAll('.tela').forEach(t => {
        t.classList.add('hidden');
    });
    const telaInicio = document.getElementById('tela-inicio');
    if (telaInicio) telaInicio.classList.remove('hidden');
    
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    const navTab = document.querySelector('.nav-tab[onclick="navegarPara(\'tela-inicio\')"]');
    if (navTab) navTab.classList.add('active');
}
