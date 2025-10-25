// static/js/simulado-novo.js - VERSÃO CORRIGIDA E TESTADA
console.log('🎯 Simulado Premium - JavaScript carregado!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM carregado - inicializando simulado...');
    
    let quantidade = 10;
    let materiasSelecionadas = [];
    
    // Inicializar estado
    function inicializar() {
        console.log('🔧 Inicializando configurações...');
        
        // Selecionar todas as matérias inicialmente
        materiasSelecionadas = Array.from(document.querySelectorAll('.materia-checkbox'))
            .map(checkbox => checkbox.value);
        
        atualizarContador();
        configurarEventos();
        verificarEstadoBotao();
        
        console.log('✅ Configuração inicializada:', { quantidade, materias: materiasSelecionadas });
    }
    
    function configurarEventos() {
        console.log('🔗 Configurando eventos...');
        
        // Botões de quantidade
        document.querySelectorAll('.quantidade-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                const novaQuantidade = parseInt(this.dataset.quantidade);
                console.log('📊 Quantidade selecionada:', novaQuantidade);
                selecionarQuantidade(novaQuantidade);
            });
        });
        
        // Input personalizado
        const inputCustom = document.getElementById('quantidade-custom');
        if (inputCustom) {
            inputCustom.addEventListener('input', function(e) {
                const valor = parseInt(this.value);
                if (valor && valor >= 1 && valor <= 50) {
                    console.log('📝 Quantidade personalizada:', valor);
                    selecionarQuantidade(valor);
                }
            });
        }
        
        // Checkboxes de matérias
        document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function(e) {
                console.log('📚 Matéria alterada:', this.value, this.checked);
                toggleMateria(this.value, this.checked);
            });
        });
        
        // Clique nos cards de matéria
        document.querySelectorAll('.materia-card').forEach(card => {
            card.addEventListener('click', function(e) {
                if (!e.target.matches('input')) {
                    const checkbox = this.querySelector('.materia-checkbox');
                    checkbox.checked = !checkbox.checked;
                    console.log('🎴 Card clicado:', checkbox.value, checkbox.checked);
                    toggleMateria(checkbox.value, checkbox.checked);
                }
            });
        });
        
        // Botões rápidos
        const btnTodas = document.getElementById('btnTodas');
        if (btnTodas) {
            btnTodas.addEventListener('click', function() {
                console.log('✅ Selecionando todas matérias');
                selecionarTodasMaterias();
            });
        }
        
        const btnPrincipais = document.getElementById('btnPrincipais');
        if (btnPrincipais) {
            btnPrincipais.addEventListener('click', function() {
                console.log('⭐ Selecionando matérias principais');
                selecionarPrincipais();
            });
        }
        
        // Botão iniciar - CORREÇÃO PRINCIPAL
        const btnIniciar = document.getElementById('btnIniciar');
        if (btnIniciar) {
            console.log('🔘 Botão iniciar encontrado, configurando evento...');
            btnIniciar.addEventListener('click', function(e) {
                console.log('🚀 Botão iniciar clicado!');
                e.preventDefault();
                iniciarSimulado();
            });
        } else {
            console.error('❌ Botão iniciar NÃO encontrado!');
        }
        
        console.log('✅ Todos os eventos configurados');
    }
    
    function selecionarQuantidade(novaQuantidade) {
        quantidade = novaQuantidade;
        
        // Atualizar botões visuais
        document.querySelectorAll('.quantidade-btn').forEach(btn => {
            btn.classList.remove('active');
            if (parseInt(btn.dataset.quantidade) === novaQuantidade) {
                btn.classList.add('active');
            }
        });
        
        // Atualizar input
        const inputCustom = document.getElementById('quantidade-custom');
        if (inputCustom) {
            inputCustom.value = novaQuantidade;
        }
        
        verificarEstadoBotao();
    }
    
    function toggleMateria(materia, selecionada) {
        const card = document.querySelector(\[data-materia=\"\\"]\);
        
        if (selecionada) {
            if (!materiasSelecionadas.includes(materia)) {
                materiasSelecionadas.push(materia);
            }
            if (card) card.classList.add('selected');
        } else {
            materiasSelecionadas = materiasSelecionadas.filter(m => m !== materia);
            if (card) card.classList.remove('selected');
        }
        
        atualizarContador();
        verificarEstadoBotao();
    }
    
    function selecionarTodasMaterias() {
        console.log('🔧 Selecionando todas matérias...');
        document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
            checkbox.checked = true;
            toggleMateria(checkbox.value, true);
        });
        mostrarAlerta('✅ Todas as matérias foram selecionadas', 'success');
    }
    
    function selecionarPrincipais() {
        console.log('🔧 Selecionando matérias principais...');
        const principais = ['Língua Portuguesa', 'Matemática', 'Raciocínio Lógico', 
                           'Direito Constitucional', 'Direito Administrativo'];
        
        document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
            const selecionar = principais.includes(checkbox.value);
            checkbox.checked = selecionar;
            toggleMateria(checkbox.value, selecionar);
        });
        mostrarAlerta('📚 Matérias principais selecionadas', 'success');
    }
    
    function atualizarContador() {
        const contador = document.getElementById('contador');
        if (contador) {
            contador.textContent = \\ matérias selecionadas\;
        }
    }
    
    function verificarEstadoBotao() {
        const btnIniciar = document.getElementById('btnIniciar');
        if (btnIniciar) {
            const temMaterias = materiasSelecionadas.length > 0;
            const quantidadeValida = quantidade >= 1 && quantidade <= 50;
            
            btnIniciar.disabled = !(temMaterias && quantidadeValida);
            
            console.log('🔘 Estado do botão:', {
                disabled: btnIniciar.disabled,
                temMaterias: temMaterias,
                quantidadeValida: quantidadeValida,
                quantidade: quantidade,
                materiasCount: materiasSelecionadas.length
            });
        }
    }
    
    async function iniciarSimulado() {
        console.log('🚀 Iniciando simulado...', {
            quantidade: quantidade,
            materias: materiasSelecionadas
        });
        
        // Validações
        if (materiasSelecionadas.length === 0) {
            mostrarAlerta('❌ Selecione pelo menos uma matéria', 'error');
            return;
        }
        
        if (!quantidade || quantidade < 1 || quantidade > 50) {
            mostrarAlerta('❌ Quantidade inválida (1-50)', 'error');
            return;
        }
        
        const btnIniciar = document.getElementById('btnIniciar');
        const loading = document.getElementById('loading');
        
        if (!btnIniciar) {
            console.error('❌ Botão iniciar não encontrado');
            return;
        }
        
        try {
            // Mostrar loading
            btnIniciar.disabled = true;
            if (loading) loading.style.display = 'block';
            
            console.log('📡 Enviando requisição para API...');
            
            const response = await fetch('/api/simulado/iniciar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    quantidade: quantidade,
                    materias: materiasSelecionadas
                })
            });
            
            console.log('📨 Resposta recebida:', response.status);
            
            const data = await response.json();
            console.log('📊 Dados da resposta:', data);
            
            if (data.success) {
                mostrarAlerta('🎉 Simulado iniciado! Redirecionando...', 'success');
                console.log('✅ Redirecionando para questão 1');
                
                setTimeout(() => {
                    window.location.href = '/questao/1';
                }, 1000);
                
            } else {
                throw new Error(data.error || 'Erro desconhecido');
            }
            
        } catch (error) {
            console.error('❌ Erro:', error);
            mostrarAlerta(\❌ Falha: \\, 'error');
        } finally {
            // Restaurar UI
            btnIniciar.disabled = false;
            if (loading) loading.style.display = 'none';
        }
    }
    
    function mostrarAlerta(mensagem, tipo) {
        console.log('💬 Alert:', tipo, mensagem);
        
        const container = document.getElementById('alert-container');
        if (!container) {
            console.error('❌ Container de alertas não encontrado');
            return;
        }
        
        const alert = document.createElement('div');
        alert.className = \lert alert-\\;
        alert.innerHTML = \
            <i class="fas \"></i>
            \
        \;
        
        container.innerHTML = '';
        container.appendChild(alert);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
    
    // Inicializar
    inicializar();
    console.log('🎉 Simulado Premium totalmente inicializado!');
    
    // Debug global
    window.debugSimulado = function() {
        console.log('🔍 Debug:', {
            quantidade: quantidade,
            materias: materiasSelecionadas,
            btnIniciar: document.getElementById('btnIniciar')
        });
    };
});
