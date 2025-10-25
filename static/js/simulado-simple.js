// static/js/simulado-simple.js - CORRIGIDO
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Simulado Simple carregado');
    
    // Selecionar TODAS as matérias automaticamente
    selecionarTodasMaterias();
    
    // Configurar eventos
    document.getElementById('btnIniciarSimulado').addEventListener('click', iniciarSimulado);
    document.getElementById('btnTodasMaterias').addEventListener('click', selecionarTodasMaterias);
    document.getElementById('btnPrincipais').addEventListener('click', selecionarPrincipais);
    
    // Quantidade padrão
    document.getElementById('quantidade').value = 10;
    
    // Verificar se há parâmetros na URL
    const urlParams = new URLSearchParams(window.location.search);
    const quantidadeParam = urlParams.get('quantidade');
    if (quantidadeParam) {
        document.getElementById('quantidade').value = quantidadeParam;
    }
});

function selecionarTodasMaterias() {
    console.log('✅ Selecionando TODAS as matérias');
    document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
        checkbox.checked = true;
    });
    atualizarContador();
}

function selecionarPrincipais() {
    console.log('✅ Selecionando matérias principais');
    const principais = ['Língua Portuguesa', 'Matemática', 'Raciocínio Lógico', 'Direito Constitucional', 'Direito Administrativo'];
    
    document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
        checkbox.checked = principais.includes(checkbox.value);
    });
    atualizarContador();
}

function atualizarContador() {
    const materiasSelecionadas = Array.from(document.querySelectorAll('.materia-checkbox:checked')).length;
    const contador = document.getElementById('contadorMaterias');
    if (contador) {
        contador.textContent = \\ matérias selecionadas\;
    }
}

// Atualizar contador quando checkboxes mudarem
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.materia-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', atualizarContador);
    });
    atualizarContador();
});

async function iniciarSimulado() {
    console.log('🎯 Iniciando simulado...');
    
    const quantidade = parseInt(document.getElementById('quantidade').value);
    const materias = Array.from(document.querySelectorAll('.materia-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    console.log('Configuração:', { quantidade, materias });
    
    if (materias.length === 0) {
        alert('Por favor, selecione pelo menos uma matéria');
        return;
    }
    
    if (!quantidade || quantidade < 1 || quantidade > 100) {
        alert('Por favor, informe uma quantidade válida de questões (1-100)');
        return;
    }
    
    const btn = document.getElementById('btnIniciarSimulado');
    const textoOriginal = btn.textContent;
    btn.disabled = true;
    btn.textContent = '🔄 Iniciando...';
    
    try {
        const response = await fetch('/api/simulado/iniciar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                quantidade: quantidade, // CORRIGIDO: garantir que é número
                materias: materias
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Simulado iniciado com sucesso!', data);
            // Redirecionar para a primeira questão
            window.location.href = '/questao/1';
        } else {
            throw new Error(data.error || 'Erro desconhecido');
        }
        
    } catch (error) {
        console.error('❌ Erro:', error);
        alert('Erro ao iniciar simulado: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = textoOriginal;
    }
}
