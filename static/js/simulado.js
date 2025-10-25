// static/js/simulado.js - CORRIGIDO E MELHORADO

class SimuladoConfig {
    constructor() {
        this.quantidade = 5;
        this.materiasSelecionadas = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.selecionarTodasMaterias(); // Seleciona todas automaticamente
        this.updateUI();
    }

    setupEventListeners() {
        // Botões de quantidade
        document.querySelectorAll('.quantidade-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.quantidade = parseInt(e.target.dataset.quantidade);
                this.updateQuantidadeButtons();
            });
        });

        // Checkboxes de matérias
        document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.updateMateriasSelecionadas();
            });
        });

        // Botão selecionar todas
        const selectAllBtn = document.getElementById('selectAll');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                this.selecionarTodasMaterias();
            });
        }

        // Botão iniciar simulado
        const btnIniciar = document.getElementById('btnIniciarSimulado');
        if (btnIniciar) {
            btnIniciar.addEventListener('click', () => {
                this.iniciarSimulado();
            });
        }
    }

    selecionarTodasMaterias() {
        document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
            checkbox.checked = true;
        });
        this.updateMateriasSelecionadas();
    }

    updateMateriasSelecionadas() {
        this.materiasSelecionadas = Array.from(document.querySelectorAll('.materia-checkbox:checked'))
            .map(checkbox => checkbox.value);
        
        this.updateUI();
    }

    updateQuantidadeButtons() {
        document.querySelectorAll('.quantidade-btn').forEach(btn => {
            btn.classList.remove('active');
            if (parseInt(btn.dataset.quantidade) === this.quantidade) {
                btn.classList.add('active');
            }
        });
    }

    updateUI() {
        const btnIniciar = document.getElementById('btnIniciarSimulado');
        const contador = document.getElementById('contadorMaterias');
        
        // Atualizar contador
        if (contador) {
            contador.textContent = \\ matérias selecionadas\;
        }
        
        // Habilitar/desabilitar botão
        if (btnIniciar) {
            btnIniciar.disabled = this.materiasSelecionadas.length === 0;
        }
    }

    async iniciarSimulado() {
        // Verificar se há matérias selecionadas
        if (this.materiasSelecionadas.length === 0) {
            this.mostrarErro('Por favor, selecione pelo menos uma matéria');
            return;
        }

        const btnIniciar = document.getElementById('btnIniciarSimulado');
        const textoOriginal = btnIniciar.textContent;
        
        try {
            // Mostrar loading
            btnIniciar.disabled = true;
            btnIniciar.textContent = '🔄 Iniciando...';
            
            console.log('🚀 Iniciando simulado com:', {
                quantidade: this.quantidade,
                materias: this.materiasSelecionadas
            });

            const response = await fetch('/api/simulado/iniciar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    quantidade: this.quantidade,
                    materias: this.materiasSelecionadas
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log('✅ Simulado iniciado com sucesso:', data);
                // Redirecionar para a primeira questão
                window.location.href = '/questao/1';
            } else {
                throw new Error(data.error || 'Erro ao iniciar simulado');
            }

        } catch (error) {
            console.error('❌ Erro ao iniciar simulado:', error);
            this.mostrarErro(error.message || 'Erro ao iniciar simulado. Tente novamente.');
        } finally {
            // Restaurar botão
            btnIniciar.disabled = false;
            btnIniciar.textContent = textoOriginal;
        }
    }

    mostrarErro(mensagem) {
        // Criar ou atualizar elemento de erro
        let erroElement = document.getElementById('erroSimulado');
        if (!erroElement) {
            erroElement = document.createElement('div');
            erroElement.id = 'erroSimulado';
            erroElement.style.cssText = \
                background: #ff4757;
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 15px 0;
                text-align: center;
                font-weight: 500;
                animation: slideIn 0.3s ease;
            \;
            const configPanel = document.querySelector('.config-panel');
            if (configPanel) {
                configPanel.prepend(erroElement);
            }
        }
        
        erroElement.textContent = mensagem;
        
        // Remover após 5 segundos
        setTimeout(() => {
            if (erroElement && erroElement.parentNode) {
                erroElement.remove();
            }
        }, 5000);
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    new SimuladoConfig();
    
    // Adicionar estilos de animação
    const style = document.createElement('style');
    style.textContent = \
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .materia-item {
            animation: slideIn 0.3s ease;
        }
        
        .fade-in {
            animation: slideIn 0.5s ease;
        }
    \;
    document.head.appendChild(style);
});

// Função global para debug
window.debugSimulado = function() {
    console.log('🔍 Debug Simulado:', {
        quantidade: window.simuladoConfig?.quantidade,
        materias: window.simuladoConfig?.materiasSelecionadas
    });
};
