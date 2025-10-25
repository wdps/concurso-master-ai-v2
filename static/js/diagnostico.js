// static/js/diagnostico.js - SISTEMA DE DIAGNÓSTICO CLIENTE
class DiagnosticoSimulado {
    constructor() {
        this.iniciarDiagnostico();
    }

    iniciarDiagnostico() {
        console.log('🔧 INICIANDO DIAGNÓSTICO DO SIMULADO');
        this.monitorarEventos();
        this.testarAPI();
        this.verificarConsole();
    }

    monitorarEventos() {
        // Monitorar clique no botão de iniciar
        const btnIniciar = document.getElementById('btnIniciarSimulado');
        if (btnIniciar) {
            btnIniciar.addEventListener('click', (e) => {
                console.log('🎯 BOTÃO INICIAR CLICADO');
                this.verificarFormulario();
            });
        }

        // Monitorar submissão do formulário
        const form = document.getElementById('configSimuladoForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                console.log('📝 FORMULÁRIO SUBMETIDO');
                this.logDadosFormulario(e);
            });
        }

        // Monitorar erros JavaScript
        window.addEventListener('error', (e) => {
            console.error('❌ ERRO JAVASCRIPT:', e.error);
            this.mostrarErro('Erro JavaScript: ' + e.message);
        });
    }

    verificarFormulario() {
        console.log('🔍 VERIFICANDO FORMULÁRIO...');
        
        const quantidade = document.querySelector('.quantidade-option.active')?.dataset.quantidade || 
                          document.getElementById('quantidadeCustom')?.value;
        const materias = Array.from(document.querySelectorAll('.materia-checkbox:checked'))
                            .map(cb => cb.value);
        
        console.log('📊 DADOS DO FORMULÁRIO:');
        console.log('  Quantidade:', quantidade);
        console.log('  Matérias:', materias);
        console.log('  Total matérias selecionadas:', materias.length);

        if (materias.length === 0) {
            console.error('❌ NENHUMA MATÉRIA SELECIONADA');
            this.mostrarErro('Selecione pelo menos uma matéria');
        }
    }

    async testarAPI() {
        console.log('🧪 TESTANDO CONEXÃO COM API...');
        
        try {
            const response = await fetch('/debug');
            const data = await response.json();
            console.log('✅ API RESPONDEU:', data);
            
            if (data.questoes_no_banco === 0) {
                console.error('❌ NENHUMA QUESTÃO NO BANCO');
                this.mostrarErro('Sistema sem questões. Use /debug/reset para recarregar.');
            }
        } catch (error) {
            console.error('❌ ERRO NA API:', error);
        }
    }

    logDadosFormulario(e) {
        const formData = new FormData(e.target);
        const dados = {};
        
        for (let [key, value] of formData.entries()) {
            dados[key] = value;
        }
        
        console.log('📦 DADOS DO FORMULÁRIO (FormData):', dados);
        
        // Coletar dados manualmente também
        const dadosManuais = this.coletarDadosManuais();
        console.log('📦 DADOS MANUAIS:', dadosManuais);
    }

    coletarDadosManuais() {
        return {
            quantidade: document.querySelector('.quantidade-option.active')?.dataset.quantidade || 
                       document.getElementById('quantidadeCustom')?.value,
            materias: Array.from(document.querySelectorAll('.materia-checkbox:checked'))
                         .map(cb => cb.value),
            tempoCronometrado: document.getElementById('tempoCronometrado')?.checked,
            dicasAutomaticas: document.getElementById('dicasAutomaticas')?.checked,
            formulasMatematicas: document.getElementById('formulasMatematicas')?.checked,
            feedbackDetalhado: document.getElementById('feedbackDetalhado')?.checked
        };
    }

    verificarConsole() {
        console.log('🖥️  CONSOLE DO NAVEGADOR ATIVO');
        console.log('📍 Para diagnóstico completo:');
        console.log('  1. Abra o Console (F12)');
        console.log('  2. Clique em "Iniciar Simulado"');
        console.log('  3. Verifique as mensagens acima');
        console.log('  4. Copie os erros e compartilhe');
    }

    mostrarErro(mensagem) {
        // Criar notificação de erro
        const erroDiv = document.createElement('div');
        erroDiv.style.cssText = 
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dc3545;
            color: white;
            padding: 15px;
            border-radius: 8px;
            z-index: 10000;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        ;
        erroDiv.innerHTML = 
            <strong>❌ Erro de Diagnóstico:</strong><br>
            
            <button onclick="this.parentElement.remove()" 
                    style="background: none; border: none; color: white; float: right; cursor: pointer;">
                ×
            </button>
        ;
        document.body.appendChild(erroDiv);
        
        setTimeout(() => {
            if (erroDiv.parentElement) {
                erroDiv.remove();
            }
        }, 10000);
    }

    // Método para teste manual
    testarIniciarSimulado() {
        console.log('🧪 TESTE MANUAL DO SIMULADO');
        
        const dadosTeste = {
            quantidade: 10,
            materias: ['Geografia', 'Matemática'],
            configs: {
                tempoCronometrado: true,
                dicasAutomaticas: true,
                formulasMatematicas: true,
                feedbackDetalhado: true
            }
        };
        
        console.log('📦 Enviando dados de teste:', dadosTeste);
        
        fetch('/api/simulado/iniciar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dadosTeste)
        })
        .then(response => response.json())
        .then(data => {
            console.log('📊 RESPOSTA DA API:', data);
            if (data.success) {
                console.log('✅ TESTE BEM-SUCEDIDO! Redirecionando...');
                window.location.href = data.redirect_url;
            } else {
                console.error('❌ TESTE FALHOU:', data.error);
            }
        })
        .catch(error => {
            console.error('❌ ERRO NO TESTE:', error);
        });
    }
}

// Inicializar diagnóstico quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    window.diagnostico = new DiagnosticoSimulado();
    
    // Adicionar botão de teste manual
    const btnTeste = document.createElement('button');
    btnTeste.innerHTML = '🧪 Teste Manual';
    btnTeste.style.cssText = 
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #ffc107;
        color: black;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        z-index: 10000;
        font-weight: bold;
    ;
    btnTeste.onclick = () => window.diagnostico.testarIniciarSimulado();
    document.body.appendChild(btnTeste);
    
    console.log('🔧 DIAGNÓSTICO INICIADO - Botão de teste adicionado');
});

// Função global para debug
window.debugSimulado = function() {
    console.log('=== 🐛 DEBUG MANUAL DO SIMULADO ===');
    console.log('Sessão:', window.sessionStorage);
    console.log('LocalStorage:', window.localStorage);
    console.log('Cookies:', document.cookie);
    
    const form = document.getElementById('configSimuladoForm');
    if (form) {
        const dados = new FormData(form);
        console.log('FormData:', Object.fromEntries(dados));
    }
};
