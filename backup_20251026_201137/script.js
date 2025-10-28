// SISTEMA DE SIMULADOS PARA CONCURSOS - JAVASCRIPT OTIMIZADO (ESQUEMATIZA.AI)

let simuladoAtual = null;
let questaoAtual = null;
let materiasPorArea = {};
let totalPontos = 0; // Para gamificação

// Função para calcular o nível (Lógica Gamificada)
function calcularNivel(pontos) {
    if (pontos < 50) return { nivel: 1, nome: "Iniciante (Cadete)" };
    if (pontos < 150) return { nivel: 2, nome: "Aprendiz (Aspirante)" };
    if (pontos < 350) return { nivel: 3, nome: "Especialista (Oficial)" };
    if (pontos < 700) return { nivel: 4, nome: "Mestre da Lei (Comandante)" };
    return { nivel: 5, nome: "Esquematizador Supremo" };
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('🧠 Sistema Esquematiza.ai inicializado');
    
    const initialNavButton = document.querySelector('.nav-tab[onclick*="tela-inicio"]');
    if(initialNavButton) {
        navegarPara('tela-inicio', initialNavButton);
    }
    carregarConteudoInicial();
    // Tenta carregar o total de pontos para exibir no dashboard
    carregarDashboard(true); 
});

// Navegação entre telas
function navegarPara(tela, elementoClicado = null) {
    document.querySelectorAll('.tela').forEach(t => {
        t.classList.add('hidden');
    });
    
    const targetElement = document.getElementById(tela);
    if(targetElement) {
        targetElement.classList.remove('hidden');
    }
    
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    if (elementoClicado) {
        elementoClicado.classList.add('active');
    } else {
        const tab = document.querySelector(`.nav-tab[onclick*="'${tela}'"]`);
        if (tab) tab.classList.add('active');
    }

    if (tela === 'tela-dashboard') {
        carregarDashboard();
    }
}

// Carregar conteúdo inicial
function carregarConteudoInicial() {
    carregarMaterias();
    carregarTemasRedacao();
}


// ========== SIMULADO (Otimização da Seleção) ==========

// Carregar matérias
async function carregarMaterias() {
    try {
        mostrarLoading('materias-container', 'Carregando áreas de conhecimento...');
        
        const response = await fetch('/api/materias');
        const data = await response.json();
        
        if (data.success) {
            materiasPorArea = data.areas;
            exibirAreas(materiasPorArea);
        } else {
            mostrarErro('materias-container', 'Erro ao carregar áreas: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarErro('materias-container', 'Erro de conexão ao carregar matérias');
    }
}

// Exibir áreas de conhecimento (somente a área, com as matérias por baixo)
function exibirAreas(areas) {
    const container = document.getElementById('materias-container');
    if (!container) return;
    
    let html = '<div class="materias-config-grid">';
    
    for (const [area, materias] of Object.entries(areas)) {
        if (materias.length === 0) continue; 
        
        const todasMatChave = materias.map(m => m.materia_chave);
        const todasMatNome = materias.map(m => m.materia_nome).join(' | ');
        const totalQuestoesArea = materias.reduce((sum, m) => sum + m.total_questoes, 0);

        // CORREÇÃO: O clique na caixa ativa/desativa a seleção da área
        html += `<div class="area-agrupamento" data-mat-chaves='${JSON.stringify(todasMatChave)}' onclick="selecionarArea(this, '${area}')">
            <h3 style="margin-bottom: 0;">
                ${area} 
                <span style="font-size: 0.7em; font-weight: normal; opacity: 0.8; float: right;">
                    (${totalQuestoesArea} Questões)
                </span>
            </h3>
            <p style="font-size: 0.8em; color: var(--secondary); margin-top: 5px;">
                 Matérias: ${todasMatNome}
            </p>
        </div>`;
    }
    
    html += '</div>';
    container.innerHTML = html;
    
    document.getElementById('selecao-simulado').classList.remove('hidden');
}

// Selecionar área inteira
function selecionarArea(elemento) {
    elemento.classList.toggle('selected');
}


// Iniciar simulado (Coleta as chaves das caixas selecionadas)
async function iniciarSimulado() {
    const areasSelecionadas = document.querySelectorAll('#materias-container .area-agrupamento.selected');
    
    let materiasSelecionadas = [];
    areasSelecionadas.forEach(areaDiv => {
        const chaves = JSON.parse(areaDiv.dataset.matChaves);
        materiasSelecionadas = materiasSelecionadas.concat(chaves);
    });

    const quantidade = document.getElementById('quantidade-questoes').value || 10;
    
    if (materiasSelecionadas.length === 0) {
        alert('Selecione pelo menos uma Área de Conhecimento!');
        return;
    }

    try {
        mostrarLoading('selecao-simulado', 'Preparando ambiente de prova...');
        
        const response = await fetch('/api/simulado/iniciar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                materias: materiasSelecionadas,
                quantidade: parseInt(quantidade)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            simuladoAtual = data;
            mostrarTelaSimuladoAtivo();
            exibirQuestao(data.questao, data.indice_atual, data.total_questoes);
        } else {
            alert('Erro ao iniciar simulado: ' + data.error);
            carregarMaterias(); 
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao iniciar simulado');
        carregarMaterias();
    }
}

// Mostrar tela do simulado ativo
function mostrarTelaSimuladoAtivo() {
    document.getElementById('selecao-simulado').classList.add('hidden');
    document.getElementById('simulado-ativo').classList.remove('hidden');
}

// Exibir questão
function exibirQuestao(questao, indice, total) {
    questaoAtual = questao;
    
    // Coluna Principal
    const questaoNumeroEl = document.getElementById('questao-numero');
    if (questaoNumeroEl) questaoNumeroEl.textContent = `Questão ${indice + 1} de ${total}`;
    
    const infoElements = {
        'questao-disciplina': `Disciplina: ${questao.disciplina}`,
        'questao-materia': `Matéria: ${questao.materia}`,
        'questao-dificuldade': `Dificuldade: ${questao.dificuldade}`,
        'questao-peso': `Peso: ${questao.peso}`
    };
    
    for (const [id, texto] of Object.entries(infoElements)) {
        const el = document.getElementById(id);
        if (el) el.textContent = texto;
    }
    
    const enunciadoEl = document.getElementById('questao-enunciado');
    if (enunciadoEl) enunciadoEl.innerHTML = questao.enunciado;
    
    // Alternativas
    const alternativasContainer = document.getElementById('questao-alternativas');
    if (alternativasContainer) {
        alternativasContainer.innerHTML = '';
        
        Object.entries(questao.alternativas).forEach(([letra, texto]) => {
            const alternativaDiv = document.createElement('div');
            alternativaDiv.className = 'alternativa';
            alternativaDiv.innerHTML = `
                <input type="radio" name="alternativa" id="alt-${letra}" value="${letra}" style="margin-top: 5px;">
                <label for="alt-${letra}">
                    <span class="letra-alternativa">${letra.toUpperCase()})</span>
                    <span>${texto}</span>
                </label>
            `;
            alternativaDiv.onclick = function() {
                this.querySelector('input[type="radio"]').checked = true;
                alternativasContainer.querySelectorAll('.alternativa').forEach(alt => {
                    alt.classList.remove('selected');
                });
                this.classList.add('selected');
            };
            alternativasContainer.appendChild(alternativaDiv);
        });
    }
    
    // Coluna Lateral (Pré-correção - Dicas Genéricas)
    const lateralBox = document.getElementById('lateral-dicas-box');
    lateralBox.innerHTML = `
        <h4>Guia de Interpretação</h4>
        <div class="dicas-interpretacao-box" style="position: static; border: none; box-shadow: none; padding: 0;">
            <p style="font-weight: bold; color: var(--primary);">Rastreamento de Conteúdo:</p>
            <ul class="dica-item-list">
                <li style="border-left-color: var(--primary);"><strong>Disciplina:</strong> ${questao.disciplina}</li>
                <li style="border-left-color: var(--primary);"><strong>Foco:</strong> ${questao.materia}</li>
                <li style="border-left-color: var(--primary);"><strong>Peso (XP):</strong> ${questao.peso}</li>
            </ul>
        </div>
    `;

    // Navegação
    const btnAnterior = document.getElementById('btn-anterior');
    if (btnAnterior) btnAnterior.disabled = indice === 0;

    const btnResponder = document.getElementById('btn-responder');
    if (btnResponder) btnResponder.style.display = 'inline-block';

    const btnProxima = document.getElementById('btn-proximo');
    if (btnProxima) btnProxima.style.display = 'none'; 

    const btnFinalizar = document.getElementById('btn-finalizar');
    if (btnFinalizar) btnFinalizar.style.display = 'inline-block'; 
    
    // Progresso
    atualizarProgresso(indice, total);
    document.getElementById('feedback-questao').style.display = 'none';
}

// Navegar questão
async function navegarQuestao(direcao) {
    const indiceAtual = simuladoAtual.indice_atual || 0;
    const novoIndice = indiceAtual + direcao;
    
    try {
        const response = await fetch(`/api/simulado/questao/${novoIndice}`);
        const data = await response.json();
        
        if (data.success) {
            simuladoAtual = data;
            exibirQuestao(data.questao, novoIndice, data.total_questoes);
        } else {
            alert('Erro: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao navegar');
    }
}


// Responder questão
async function responderQuestao() {
    const alternativaSelecionada = document.querySelector('input[name="alternativa"]:checked');
    
    if (!alternativaSelecionada) {
        alert('Selecione uma alternativa!');
        return;
    }

    if (!questaoAtual || !questaoAtual.id) {
        alert('Erro interno: ID da questão não encontrado. Recarregue o simulado.');
        console.error("Erro ao responder: questaoAtual ou questaoAtual.id é null.", questaoAtual);
        return;
    }
    
    try {
        const response = await fetch('/api/simulado/responder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                questao_id: questaoAtual.id,
                alternativa: alternativaSelecionada.value
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarFeedbackQuestao(data);
            const btnResponder = document.getElementById('btn-responder');
            if (btnResponder) btnResponder.style.display = 'none';
            
            const indiceAtual = simuladoAtual.indice_atual;
            const total = simuladoAtual.total_questoes;
            const btnProxima = document.getElementById('btn-proximo');
            if (btnProxima && indiceAtual < total - 1) {
                btnProxima.style.display = 'inline-block';
            }
        } else {
            alert('Erro: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao responder');
    }
}

// Mostrar feedback (inclui fórmulas e dicas)
function mostrarFeedbackQuestao(data) {
    const feedbackDiv = document.getElementById('feedback-questao');
    const lateralBox = document.getElementById('lateral-dicas-box');

    // Feedback na Coluna Principal
    feedbackDiv.innerHTML = `
        <div class="feedback ${data.acertou ? 'acerto' : 'erro'}">
            <h4>${data.acertou ? '✅ Acerto: '+ questaoAtual.peso + ' XP!' : '❌ Erro: Revise o Esquema!'}</h4>
            <p><strong>Sua resposta:</strong> ${data.alternativa_escolhida} &mdash; <strong>Correta:</strong> ${data.resposta_correta}</p>
        </div>
        <div class="justificativa-box card" style="padding: 15px;">
             <strong>Justificativa:</strong> ${data.justificativa}
        </div>
    `;
    feedbackDiv.style.display = 'block';

    // Dicas e Fórmulas na Coluna Lateral (Permanente)
    let lateralHTML = `
        <h4>Análise Pós-Questão (Esquematiza)</h4>
        <div class="dicas-interpretacao-box" style="position: static; border: none; box-shadow: none; padding: 0;">
            <p style="font-weight: bold; color: var(--primary);">Ferramentas de Estudo:</p>
            <ul class="dica-item-list">
                <li style="border-left-color: ${data.acertou ? 'var(--success)' : 'var(--danger)'};">
                    <strong>${data.acertou ? 'Reforço:' : 'Foco:'}</strong> ${data.dicas_interpretacao}
                </li>
                ${data.dica ? `<li style="border-left-color: var(--info);"><strong>Dica da Questão:</strong> ${data.dica}</li>` : ''}
            </ul>
        </div>
    `;
    
    if (data.formula) {
        lateralHTML += `<div class="formula-box">
            FÓRMULA CHAVE: ${data.formula}
        </div>`;
    }

    lateralBox.innerHTML = lateralHTML;
}

// Atualizar progresso
function atualizarProgresso(indice, total) {
    const progresso = ((indice + 1) / total) * 100;
    const progressBar = document.getElementById('progresso-simulado');
    if (progressBar) {
        progressBar.style.width = `${progresso}%`;
    }
}

// Finalizar simulado
async function finalizarSimulado() {
    if (!confirm('Deseja finalizar o simulado agora? Sua pontuação será calculada com base no peso das questões respondidas.')) return;
    
    try {
        const response = await fetch('/api/simulado/finalizar', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            if (document.getElementById('tela-resultado')) {
                exibirResultado(data.relatorio);
                document.getElementById('simulado-ativo').classList.add('hidden');
                document.getElementById('tela-resultado').classList.remove('hidden');
                // Após finalizar, recarrega o dashboard para atualizar o XP
                carregarDashboard(true);
            } else {
                console.error("Erro fatal: tela-resultado não encontrada. Reiniciando...");
                alert("Erro ao exibir resultado. A aplicação será reiniciada.");
                window.location.reload();
            }
        } else {
            alert('Erro ao finalizar: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao finalizar simulado');
    }
}

// Exibir resultado
function exibirResultado(relatorio) {
    const ids = {
        'resultado-acertos': `${relatorio.total_acertos}/${relatorio.total_questoes}`,
        'resultado-percentual': `${relatorio.percentual_acerto_simples}%`,
        'resultado-nota-peso': `${relatorio.nota_final}%`,
        'resultado-pontuacao-total': `${relatorio.pontos_obtidos} XP`
    };

    for (const [id, value] of Object.entries(ids)) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }
}


// ========== REDAÇÃO (Corrigido e Aprimorado) ==========

// Carregar temas
async function carregarTemasRedacao() {
    try {
        mostrarLoading('temas-redacao-container', 'Carregando temas...');
        const response = await fetch('/api/redacao/temas');
        const data = await response.json();
        
        const select = document.getElementById('temas-redacao');
        if (data.success) {
            select.innerHTML = '<option value="">Selecione um tema</option>';
            
            data.temas.forEach(tema => {
                const option = document.createElement('option');
                option.value = tema.titulo;
                option.textContent = `${tema.titulo}`; // Sem dificuldade!
                select.appendChild(option);
            });
            document.getElementById('temas-redacao-container').innerHTML = '';
        } else {
            document.getElementById('temas-redacao-container').innerHTML = '❌ Erro ao carregar temas.';
        }
    } catch (error) {
        console.error('Erro:', error);
        document.getElementById('temas-redacao-container').innerHTML = '❌ Erro de conexão ao carregar temas.';
    }
}


// Corrigir redação
async function corrigirRedacao() {
    const temaSelect = document.getElementById('temas-redacao');
    const textoRedacao = document.getElementById('texto-redacao').value;
    
    if (!temaSelect.value || !textoRedacao.trim()) {
        alert('Selecione um tema e digite sua redação!');
        return;
    }
    
    const btnCorrigir = document.getElementById('btn-corrigir');
    const textoOriginal = btnCorrigir.innerHTML;
    btnCorrigir.innerHTML = '<span class="loading"></span> Corrigindo...';
    btnCorrigir.disabled = true;
    
    try {
        document.getElementById('resultado-correcao').classList.remove('hidden');
        mostrarLoading('resultado-correcao', 'Analisando sua redação com métricas de concurso...');
        
        const response = await fetch('/api/redacao/corrigir-gemini', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tema: temaSelect.value,
                texto: textoRedacao
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            exibirCorrecaoRedacao(data.correcao);
        } else {
            alert('Erro na correção: ' + data.error);
            document.getElementById('resultado-correcao').innerHTML = `<div class="card feedback erro">Erro ao processar a correção: ${data.error}</div>`;
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao corrigir redação');
        document.getElementById('resultado-correcao').innerHTML = `<div class="card feedback erro">Erro de conexão ao corrigir a redação.</div>`;
    } finally {
        btnCorrigir.innerHTML = textoOriginal;
        btnCorrigir.disabled = false;
        window.scrollTo({ top: document.getElementById('resultado-correcao').offsetTop - 100, behavior: 'smooth' });
    }
}

// Exibir correção
function exibirCorrecaoRedacao(correcao) {
    const resultadoDiv = document.getElementById('resultado-correcao');
    
    let html = `
        <div class="correcao-header">
            <h3>Resultado Final</h3>
            <div class="nota-final">${correcao.nota_final}/100</div>
        </div>
        
        <div class="card">
            <h4>📝 Análise Detalhada por Competência:</h4>
    `;
    
    correcao.analise_competencias.forEach(comp => {
        html += `
            <div class="competencia-item">
                <h5 style="margin: 0 0 10px 0;">${comp.competencia} <span style="float: right; color: var(--success); font-weight: bold;">${comp.nota}/20</span></h5>
                <p style="margin: 0; font-size: 0.95em;">${comp.comentario}</p>
            </div>
        `;
    });
    
    html += `
            </div>
            
            <div class="card" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h4>✅ Pontos Fortes:</h4>
                    <ul style="list-style-type: none; padding: 0;">
                        ${correcao.pontos_fortes.map(ponto => `<li style="color: var(--success); margin-bottom: 5px; border-left: 3px solid var(--success); padding-left: 10px;">${ponto}</li>`).join('')}
                    </ul>
                </div>
                <div>
                    <h4>❌ Pontos a Melhorar:</h4>
                    <ul style="list-style-type: none; padding: 0;">
                        ${correcao.pontos_fracos.map(ponto => `<li style="color: var(--danger); margin-bottom: 5px; border-left: 3px solid var(--danger); padding-left: 10px;">${ponto}</li>`).join('')}
                    </ul>
                </div>
            </div>

            <div class="card">
                <h4>💡 Sugestões de Melhoria e Dicas:</h4>
                <ul style="list-style-type: none; padding: 0;">
                    ${correcao.sugestoes_melhoria.map(sugestao => `<li style="margin-bottom: 8px; border-left: 3px solid var(--primary); padding-left: 10px;">• ${sugestao}</li>`).join('')}
                    ${correcao.dicas_concursos.map(dica => `<li style="margin-bottom: 8px; border-left: 3px solid var(--info); padding-left: 10px;">🎯 ${dica}</li>`).join('')}
                </ul>
            </div>
        `;
    
    resultadoDiv.innerHTML = html;
    resultadoDiv.classList.remove('hidden');
}

// ========== DASHBOARD Melhorado ==========

async function carregarDashboard(inicial = false) {
    try {
        if (!inicial) mostrarLoading('dashboard-content', 'Carregando estatísticas de desempenho...');
        
        const response = await fetch('/api/dashboard/estatisticas');
        const data = await response.json();
        
        if (data.success) {
            if (!inicial) exibirDashboard(data);
            // Lógica de XP baseada na prática
            totalPontos = Math.floor(data.total_questoes_respondidas * 1.5) + data.total_simulados * 10; 
            
            // Atualiza o badge de nível no Dashboard e Index
            const nivelInfo = calcularNivel(totalPontos);
            document.querySelectorAll('.level-info').forEach(el => {
                el.innerHTML = `<span class="level-badge">Nível ${nivelInfo.nivel}: ${nivelInfo.nome}</span>`;
            });

        } else if (!inicial) {
             mostrarErro('dashboard-content', 'Erro ao carregar dados: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        if (!inicial) mostrarErro('dashboard-content', 'Erro de conexão ao carregar estatísticas.');
    }
}

function exibirDashboard(data) {
    const container = document.getElementById('dashboard-content');
    
    let html = `
        <div style="text-align: center;">
            <p class="level-info" style="font-size: 1.1em;"></p>
            <h3 style="color: var(--primary); margin-bottom: 20px;">Pontuação Total (XP): ${totalPontos}</h3>
        </div>
        <div class="dashboard-metrics">
            <div class="metric-card">
                <div class="metric-number primary">${data.total_simulados}</div>
                <div>Missões (Simulados) Realizadas</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">${data.total_questoes_respondidas}</div>
                <div>Questões Praticadas</div>
            </div>
            <div class="metric-card">
                <div class="metric-number metric-number.primary">${data.media_geral}%</div>
                <div style="font-weight: bold;">MÉDIA PONDERADA</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">${data.media_acertos}%</div>
                <div>Média Simples de Acertos</div>
            </div>
        </div>
    `;
    
    if (data.historico_recente.length > 0) {
        html += `<div class="card">
            <h4>📈 Histórico Recente de Desafios</h4>
            <table class="historico-tabela">
                <thead>
                    <tr>
                        <th>Simulado ID</th>
                        <th style="text-align: center;">Acertos</th>
                        <th style="text-align: center;">Nota Ponderada</th>
                        <th style="text-align: center;">Data</th>
                    </tr>
                </thead>
                <tbody>`;
        
        data.historico_recente.forEach((simulado, index) => {
            html += `
                <tr>
                    <td>#${simulado.simulado_id.split('_')[1]}</td>
                    <td style="text-align: center;">${simulado.total_acertos}/${simulado.total_questoes}</td>
                    <td style="text-align: center; font-weight: bold; color: var(--primary);">${simulado.nota_final}%</td>
                    <td style="text-align: center;">${new Date(simulado.data_fim).toLocaleDateString()}</td>
                </tr>
            `;
        });
        
        html += `</tbody></table></div>`;
    } else {
        html += `<div class="card text-center" style="color: var(--secondary);">Nenhum histórico encontrado. Comece seu primeiro simulado!</div>`;
    }
    
    container.innerHTML = html;
}


// ========== UTILITÁRIOS ==========

function mostrarLoading(containerId, mensagem = 'Carregando...') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="text-center" style="padding: 40px;">
            <div class="loading" style="margin: 0 auto;"></div>
            <p style="margin-top: 15px;">${mensagem}</p>
        </div>`;
    }
}

function mostrarErro(containerId, mensagem) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="card feedback erro">
            <h4>❌ Erro</h4>
            <p>${mensagem}</p>
        </div>`;
    }
}

function voltarInicio() {
    navegarPara('tela-inicio');
}
