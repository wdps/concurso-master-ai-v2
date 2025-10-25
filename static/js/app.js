// static/js/app.js - SISTEMA INTERATIVO PREMIUM

class ConcursoMaster {
    constructor() {
        this.init();
    }

    init() {
        this.initTooltips();
        this.initMathFormulas();
        this.initProgressBars();
        this.initInteractiveElements();
    }

    initTooltips() {
        // Sistema de dicas flutuantes
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(tooltip => {
            tooltip.addEventListener('mouseenter', this.showTooltip);
            tooltip.addEventListener('mouseleave', this.hideTooltip);
        });
    }

    initMathFormulas() {
        // Renderizar fórmulas matemáticas
        const formulas = document.querySelectorAll('.math-formula');
        formulas.forEach(formula => {
            this.renderMathFormula(formula);
        });
    }

    initProgressBars() {
        // Animar barras de progresso
        const progressBars = document.querySelectorAll('.progress-fill');
        progressBars.forEach(bar => {
            const width = bar.style.width || bar.getAttribute('data-width');
            setTimeout(() => {
                bar.style.width = width;
            }, 500);
        });
    }

    initInteractiveElements() {
        // Elementos interativos
        this.initAlternativaSelection();
        this.initHintSystem();
        this.initFormulaModal();
    }

    initAlternativaSelection() {
        const alternativas = document.querySelectorAll('.alternativa-item');
        alternativas.forEach(alt => {
            alt.addEventListener('click', function() {
                // Remover seleção anterior
                alternativas.forEach(a => a.classList.remove('selected'));
                // Selecionar atual
                this.classList.add('selected');
                // Atualizar input hidden
                const input = this.querySelector('input[type="radio"]');
                if (input) input.checked = true;
            });
        });
    }

    initHintSystem() {
        // Sistema de dicas contextuais
        const hintButtons = document.querySelectorAll('.hint-btn');
        hintButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const hintId = this.getAttribute('data-hint');
                const hintContent = document.getElementById(hintId);
                if (hintContent) {
                    hintContent.classList.toggle('show');
                }
            });
        });
    }

    initFormulaModal() {
        // Modal de fórmulas matemáticas
        const formulaButtons = document.querySelectorAll('.formula-btn');
        const formulaModal = document.getElementById('formulaModal');
        
        formulaButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const formulaType = this.getAttribute('data-formula');
                showFormulaModal(formulaType);
            });
        });

        function showFormulaModal(type) {
            // Implementar modal de fórmulas
            console.log('Mostrar fórmulas:', type);
        }
    }

    showTooltip(e) {
        const tooltipText = this.getAttribute('data-tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = 'premium-tooltip';
        tooltip.textContent = tooltipText;
        document.body.appendChild(tooltip);
        
        const rect = this.getBoundingClientRect();
        tooltip.style.left = rect.left + 'px';
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
    }

    hideTooltip() {
        const tooltip = document.querySelector('.premium-tooltip');
        if (tooltip) tooltip.remove();
    }

    renderMathFormula(element) {
        // Usar MathJax ou KaTeX para renderizar fórmulas
        const formula = element.textContent;
        // Implementação básica - pode ser extendida com MathJax
        element.innerHTML = this.formatMathFormula(formula);
    }

    formatMathFormula(formula) {
        // Formatação básica de fórmulas matemáticas
        return formula
            .replace(/\^(\d+)/g, '<sup></sup>')
            .replace(/_(\d+)/g, '<sub></sub>')
            .replace(/\\sqrt/g, '√')
            .replace(/\\frac{([^}]+)}{([^}]+)}/g, '<sup></sup>/<sub></sub>');
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.concursoMaster = new ConcursoMaster();
});

// Funções utilitárias
function showLoading() {
    const loading = document.createElement('div');
    loading.className = 'loading-overlay';
    loading.innerHTML = 
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Carregando...</p>
        </div>
    ;
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.querySelector('.loading-overlay');
    if (loading) loading.remove();
}

// Sistema de notificações
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = 
otification notification-;
    notification.innerHTML = 
        <div class="notification-content">
            <span class="notification-message"></span>
            <button class="notification-close">&times;</button>
        </div>
    ;
    
    document.body.appendChild(notification);
    
    // Animação de entrada
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
    
    // Botão fechar
    notification.querySelector('.notification-close').addEventListener('click', function() {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    });
}
