// static/js/simulado.js - SISTEMA 100% FUNCIONAL
console.log('✅ JavaScript do simulado carregado!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando sistema de simulado...');
    
    let quantidadeSelecionada = 30;
    const materiasCheckboxes = document.querySelectorAll('.materia-checkbox');
    
    // SISTEMA DE SELEÇÃO DE QUANTIDADE
    const quantidadeBtns = document.querySelectorAll('.quantidade-btn');
    quantidadeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            console.log('📊 Botão de quantidade clicado:', this.dataset.quantidade);
            
            // Remover classe active de todos
            quantidadeBtns.forEach(b => b.classList.remove('active'));
            
            // Adicionar classe active ao clicado
            this.classList.add('active');
            
            // Atualizar quantidade
            quantidadeSelecionada = parseInt(this.dataset.quantidade);
            
            // Atualizar input custom
            document.getElementById('quantidadeCustom').value = quantidadeSelecionada;
            
            console.log('✅ Quantidade selecionada:', quantidadeSelecionada);
        });
    });
    
    // INPUT CUSTOM
    const inputCustom = document.getElementById('quantidadeCustom');
    if (inputCustom) {
        inputCustom.addEventListener('input', function() {
            const valor = parseInt(this.value);
            if (valor >= 5 && valor <= 100) {
                quantidadeSelecionada = valor;
                
                // Remover active dos botões
                quantidadeBtns.forEach(b => b.classList.remove('active'));
                
                console.log('✅ Quantidade customizada:', quantidadeSelecionada);
            }
        });
    }
    
    // BOTÕES DE SELEÇÃO RÁPIDA
    const btnTodas = document.getElementById('btnSelecionarTodas');
    if (btnTodas) {
        btnTodas.addEventListener('click', function() {
            console.log('✅ Selecionando todas matérias');
            materiasCheckboxes.forEach(cb => {
                cb.checked = true;
                atualizarEstadoMateria(cb);
            });
            atualizarContadorMaterias();
        });
    }
    
    const btnPrincipais = document.getElementById('btnSelecionarPrincipais');
    if (btnPrincipais) {
        btnPrincipais.addEventListener('click', function() {
            console.log('⭐ Selecionando matérias principais');
            const principais = ['Língua Portuguesa', 'Matemática', 'Raciocínio Lógico', 'Direito Constitucional', 'Direito Administrativo'];
            
            materiasCheckboxes.forEach(cb => {
                const selecionar = principais.includes(cb.value);
                cb.checked = selecionar;
                atualizarEstadoMateria(cb);
            });
            atualizarContadorMaterias();
        });
    }
    
    // ATUALIZAR ESTADO DAS MATÉRIAS
    function atualizarEstadoMateria(checkbox) {
        const label = document.querySelector(label[for=""]);
        if (checkbox.checked) {
            label.classList.add('selected');
        } else {
            label.classList.remove('selected');
        }
    }
    
    // CONTADOR DE MATÉRIAS
    function atualizarContadorMaterias() {
        const selecionadas = Array.from(materiasCheckboxes).filter(cb => cb.checked).length;
        const contador = document.getElementById('contadorMaterias');
        if (contador) {
            contador.textContent = selecionadas + ' matérias selecionadas';
        }
        console.log('📚 Matérias selecionadas:', selecionadas);
    }
    
    // EVENTOS NAS MATÉRIAS
    materiasCheckboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            atualizarEstadoMateria(this);
            atualizarContadorMaterias();
        });
        
        // Inicializar estado
        atualizarEstadoMateria(cb);
    });
    
    // FORMULÁRIO DE SUBMISSÃO
    const formSimulado = document.getElementById('configSimuladoForm');
    if (formSimulado) {
        formSimulado.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('🚀 Formulário submetido!');
            
            // Coletar dados
            const materiasSelecionadas = Array.from(materiasCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            
            const configs = {
                tempoCronometrado: document.getElementById('tempoCronometrado')?.checked || false,
                dicasAutomaticas: document.getElementById('dicasAutomaticas')?.checked || false,
                formulasMatematicas: document.getElementById('formulasMatematicas')?.checked || false,
                feedbackDetalhado: document.getElementById('feedbackDetalhado')?.checked || false
            };
            
            console.log('📦 Dados coletados:', {
                quantidade: quantidadeSelecionada,
                materias: materiasSelecionadas,
                configs: configs
            });
            
            // VALIDAÇÕES
            if (materiasSelecionadas.length === 0) {
                alert('❌ Selecione pelo menos uma matéria para continuar.');
                return;
            }
            
            if (!quantidadeSelecionada || quantidadeSelecionada < 5 || quantidadeSelecionada > 100) {
                alert('❌ Selecione uma quantidade entre 5 e 100 questões.');
                return;
            }
            
            // BOTÃO DE LOADING
            const btnIniciar = document.getElementById('btnIniciarSimulado');
            const btnTextoOriginal = btnIniciar.innerHTML;
            
            btnIniciar.disabled = true;
            btnIniciar.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Preparando simulado...';
            
            try {
                console.log('📡 Enviando requisição para API...');
                
                const response = await fetch('/api/simulado/iniciar', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        quantidade: quantidadeSelecionada,
                        materias: materiasSelecionadas,
                        configs: configs
                    })
                });
                
                const data = await response.json();
                console.log('📊 Resposta da API:', data);
                
                if (data.success) {
                    console.log('✅ Simulado iniciado com sucesso! Redirecionando...');
                    
                    // Feedback visual
                    showNotification('🎉 Simulado configurado! Redirecionando...', 'success');
                    
                    // Redirecionar após breve delay
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 1000);
                    
                } else {
                    throw new Error(data.error || 'Erro desconhecido ao iniciar simulado');
                }
                
            } catch (error) {
                console.error('❌ Erro ao iniciar simulado:', error);
                
                // Restaurar botão
                btnIniciar.disabled = false;
                btnIniciar.innerHTML = btnTextoOriginal;
                
                // Mostrar erro
                showNotification('❌ Erro: ' + error.message, 'error');
            }
        });
    }
    
    // INICIALIZAR
    atualizarContadorMaterias();
    console.log('✅ Sistema de simulado inicializado com sucesso!');
});

// SISTEMA DE NOTIFICAÇÕES
function showNotification(mensagem, tipo = 'info') {
    // Criar elemento de notificação
    const notification = document.createElement('div');
    notification.className = lert alert- position-fixed;
    notification.style.cssText = 
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    ;
    notification.innerHTML = 
        <div class="d-flex justify-content-between align-items-center">
            <span></span>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    ;
    
    document.body.appendChild(notification);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// DEBUG
window.debugSimulado = function() {
    console.log('🔍 Debug do Simulado:', {
        quantidade: quantidadeSelecionada,
        materias: Array.from(document.querySelectorAll('.materia-checkbox:checked')).map(cb => cb.value)
    });
};
