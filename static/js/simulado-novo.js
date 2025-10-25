// static/js/simulado-novo.js - SISTEMA 100% FUNCIONAL
class SimuladoNovo {
    constructor() {
        this.quantidade = 10;
        this.materiasSelecionadas = [];
        this.init();
    }

    init() {
        console.log('🎯 Simulado Premium inicializado');
        this.carregarEstadoInicial();
        this.configurarEventos();
        this.atualizarInterface();
    }

    carregarEstadoInicial() {
        // Selecionar todas as matérias inicialmente
        this.materiasSelecionadas = Array.from(document.querySelectorAll('.materia-checkbox'))
            .map(checkbox => checkbox.value);
        this.atualizarContador();
    }

    configurarEventos() {
        // Botões de quantidade
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

        // Clique nos cards de matéria
        document.querySelectorAll('.materia-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.matches('input')) {
                    const checkbox = card.querySelector('.materia-checkbox');
                    checkbox.checked = !checkbox.checked;
                    this.toggleMateria(checkbox.value, checkbox.checked);
                }
            });
        });

        // Botões rápidos
        document.getElementById('btnTodas').addEventListener('click', () => {
            this.selecionarTodasMaterias();
        });

        document.getElementById('btnPrincipais').addEventListener('click', () => {
            this.selecionarPrincipais();
        });

        // Botão iniciar
        document.getElementById('btnIniciar').addEventListener('click', () => {
            this.iniciarSimulado();
        });

        // Enter no input personalizado
        document.getElementById('quantidade-custom').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.iniciarSimulado();
            }
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
        const card = document.querySelector(\[data-materia=\"\\"]\);
        
        if (selecionada) {
            if (!this.materiasSelecionadas.includes(materia)) {
                this.materiasSelecionadas.push(materia);
            }
            card.classList.add('selected');
        } else {
            this.materiasSelecionadas = this.materiasSelecionadas.filter(m => m !== materia);
            card.classList.remove('selected');
        }
        
        this.atualizarContador();
        this.verificarEstadoBotao();
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
        const contador = document.getElementById('contador');
        if (contador) {
            contador.textContent = \\ matérias selecionadas\;
        }
    }

    verificarEstadoBotao() {
        const btnIniciar = document.getElementById('btnIniciar');
        const temMaterias = this.materiasSelecionadas.length > 0;
        const quantidadeValida = this.quantidade >= 1 && this.quantidade <= 50;
        
        btnIniciar.disabled = !(temMaterias && quantidadeValida);
    }

    atualizarInterface() {
        this.atualizarContador();
        this.verificarEstadoBotao();
    }

    async iniciarSimulado() {
        // Validações finais
        if (this.materiasSelecionadas.length === 0) {
            this.mostrarAlerta('❌ Selecione pelo menos uma matéria para iniciar o simulado', 'error');
            return;
        }

        if (!this.quantidade || this.quantidade < 1 || this.quantidade > 50) {
            this.mostrarAlerta('❌ Selecione uma quantidade válida de questões (1-50)', 'error');
            return;
        }

        const btnIniciar = document.getElementById('btnIniciar');
        const loading = document.getElementById('loading');
        const textoOriginal = btnIniciar.innerHTML;

        try {
            // Mostrar loading
            btnIniciar.disabled = true;
            btnIniciar.style.display = 'none';
            loading.style.display = 'block';

            console.log('🚀 Iniciando simulado premium:', {
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
                this.mostrarAlerta('🎉 Simulado configurado! Redirecionando...', 'success');
                
                // Redirecionar após breve feedback visual
                setTimeout(() => {
                    window.location.href = '/questao/1';
                }, 1500);
                
            } else {
                throw new Error(data.error || 'Erro desconhecido ao iniciar simulado');
            }

        } catch (error) {
            console.error('❌ Erro ao iniciar simulado:', error);
            this.mostrarAlerta(\❌ Falha: \\, 'error');
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
        alert.innerHTML = \
            <i class="fas \"></i>
            \
        \;
        
        container.innerHTML = ''; // Limpar alertas anteriores
        container.appendChild(alert);
        
        // Remover após 5 segundos
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.simuladoPremium = new SimuladoNovo();
});

// Debug
window.debugSimulado = function() {
    console.log('🔍 Debug Simulado Premium:', {
        quantidade: window.simuladoPremium?.quantidade,
        materias: window.simuladoPremium?.materiasSelecionadas
    });
};
