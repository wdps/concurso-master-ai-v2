// static/js/simulado-moderno.js - SISTEMA COMPLETAMENTE FUNCIONAL
class SimuladoModerno {
    constructor() {
        this.quantidade = 10;
        this.materiasSelecionadas = [];
        this.init();
    }

    init() {
        this.carregarMaterias();
        this.setupEventListeners();
        this.atualizarUI();
        console.log('🚀 Simulado Moderno inicializado');
    }

    carregarMaterias() {
        // Selecionar todas as matérias inicialmente
        this.materiasSelecionadas = Array.from(document.querySelectorAll('.materia-checkbox'))
            .map(checkbox => checkbox.value);
        this.atualizarContador();
    }

    setupEventListeners() {
        // Botões de quantidade rápida
        document.querySelectorAll('.quantidade-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selecionarQuantidade(parseInt(e.target.dataset.quantidade));
            });
        });

        // Input personalizado
        document.getElementById('quantidade-custom').addEventListener('input', (e) => {
            const valor = parseInt(e.target.value);
            if (valor && valor >= 1 && valor <= 50) {
                this.selecionarQuantidade(valor);
            }
        });

        // Checkboxes de matérias
        document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.toggleMateria(e.target.value, e.target.checked);
            });
        });

        // Clique nos itens de matéria
        document.querySelectorAll('.materia-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.matches('input')) {
                    const checkbox = item.querySelector('.materia-checkbox');
                    checkbox.checked = !checkbox.checked;
                    this.toggleMateria(checkbox.value, checkbox.checked);
                }
            });
        });

        // Botões rápidos
        document.getElementById('btnTodasMaterias').addEventListener('click', () => {
            this.selecionarTodasMaterias();
        });

        document.getElementById('btnPrincipais').addEventListener('click', () => {
            this.selecionarPrincipais();
        });

        // Botão iniciar
        document.getElementById('btnIniciarSimulado').addEventListener('click', () => {
            this.iniciarSimulado();
        });
    }

    selecionarQuantidade(novaQuantidade) {
        this.quantidade = novaQuantidade;
        
        // Atualizar botões
        document.querySelectorAll('.quantidade-btn').forEach(btn => {
            btn.classList.remove('active');
            if (parseInt(btn.dataset.quantidade) === novaQuantidade) {
                btn.classList.add('active');
            }
        });
        
        // Atualizar input
        document.getElementById('quantidade-custom').value = novaQuantidade;
        
        console.log('📊 Quantidade selecionada:', novaQuantidade);
    }

    toggleMateria(materia, selecionada) {
        const item = document.querySelector(\[data-materia=\"\\"]\);
        
        if (selecionada) {
            if (!this.materiasSelecionadas.includes(materia)) {
                this.materiasSelecionadas.push(materia);
            }
            item.classList.add('selected');
        } else {
            this.materiasSelecionadas = this.materiasSelecionadas.filter(m => m !== materia);
            item.classList.remove('selected');
        }
        
        this.atualizarContador();
        console.log('📚 Matérias selecionadas:', this.materiasSelecionadas);
    }

    selecionarTodasMaterias() {
        document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
            checkbox.checked = true;
            this.toggleMateria(checkbox.value, true);
        });
        this.mostrarAlerta('✅ Todas as matérias foram selecionadas', 'success');
    }

    selecionarPrincipais() {
        const principais = ['Língua Portuguesa', 'Matemática', 'Raciocínio Lógico', 
                           'Direito Constitucional', 'Direito Administrativo'];
        
        document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
            const selecionar = principais.includes(checkbox.value);
            checkbox.checked = selecionar;
            this.toggleMateria(checkbox.value, selecionar);
        });
        this.mostrarAlerta('📚 Matérias principais selecionadas', 'success');
    }

    atualizarContador() {
        const contador = document.getElementById('contador-materias');
        if (contador) {
            contador.textContent = \\ matérias selecionadas\;
        }
    }

    atualizarUI() {
        this.atualizarContador();
        
        // Habilitar/desabilitar botão baseado na seleção
        const btnIniciar = document.getElementById('btnIniciarSimulado');
        btnIniciar.disabled = this.materiasSelecionadas.length === 0;
    }

    async iniciarSimulado() {
        // Validações
        if (this.materiasSelecionadas.length === 0) {
            this.mostrarAlerta('❌ Selecione pelo menos uma matéria para iniciar o simulado', 'error');
            return;
        }

        if (!this.quantidade || this.quantidade < 1 || this.quantidade > 50) {
            this.mostrarAlerta('❌ Selecione uma quantidade válida de questões (1-50)', 'error');
            return;
        }

        const btnIniciar = document.getElementById('btnIniciarSimulado');
        const loading = document.getElementById('loading');
        const textoOriginal = btnIniciar.innerHTML;

        try {
            // Mostrar loading
            btnIniciar.disabled = true;
            btnIniciar.style.display = 'none';
            loading.style.display = 'block';

            console.log('🚀 Iniciando simulado com configuração:', {
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
                console.log('✅ Simulado iniciado com sucesso!', data);
                this.mostrarAlerta('🎉 Simulado iniciado! Redirecionando...', 'success');
                
                // Redirecionar para primeira questão após breve delay
                setTimeout(() => {
                    window.location.href = '/questao/1';
                }, 1000);
                
            } else {
                throw new Error(data.error || 'Erro desconhecido ao iniciar simulado');
            }

        } catch (error) {
            console.error('❌ Erro ao iniciar simulado:', error);
            this.mostrarAlerta(\❌ Erro: \\, 'error');
        } finally {
            // Restaurar UI
            btnIniciar.disabled = false;
            btnIniciar.style.display = 'inline-flex';
            loading.style.display = 'none';
            btnIniciar.innerHTML = textoOriginal;
        }
    }

    mostrarAlerta(mensagem, tipo) {
        const container = document.getElementById('alert-container');
        const alert = document.createElement('div');
        alert.className = \lert alert-\\;
        alert.innerHTML = mensagem;
        
        container.appendChild(alert);
        
        // Remover após 5 segundos
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.simuladoApp = new SimuladoModerno();
});

// Debug helper
window.debugSimulado = function() {
    console.log('🔍 Debug Simulado:', {
        quantidade: window.simuladoApp?.quantidade,
        materias: window.simuladoApp?.materiasSelecionadas
    });
};
