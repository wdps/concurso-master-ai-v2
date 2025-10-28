// Diagnóstico do Simulado - Execute no console do navegador
console.log("🔍 DIAGNÓSTICO DO SIMULADO");

// Verificar se os elementos existem
const elementos = [
    'questao-numero', 'questao-disciplina', 'questao-materia', 
    'questao-dificuldade', 'questao-enunciado', 'questao-alternativas'
];

elementos.forEach(id => {
    const elemento = document.getElementById(id);
    console.log(`${id}:`, elemento ? '✅ Existe' : '❌ Não existe');
});

// Verificar estrutura do simulado
if (window.app && window.app.simuladoAtual) {
    console.log("📊 Simulado atual:", window.app.simuladoAtual);
    console.log("📝 Questão atual:", window.app.questaoAtual);
} else {
    console.log("❌ Nenhum simulado ativo");
}
