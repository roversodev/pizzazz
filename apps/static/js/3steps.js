document.addEventListener("DOMContentLoaded", function () {

    // Selecionando os elementos do formulário e dos botões
    const nextButtons = document.querySelectorAll('.js-btn-next');
    const prevButtons = document.querySelectorAll('.js-btn-prev');
    const formPanels = document.querySelectorAll('.multisteps-form__panel');
    const progressButtons = document.querySelectorAll('.multisteps-form__progress-btn');
    let currentStep = 0; // Começando do primeiro passo
    
    // Função para mudar de painel
    function showPanel(step) {
        // Esconde todos os painéis
        formPanels.forEach(panel => panel.classList.remove('js-active'));
        // Mostra o painel correspondente ao passo atual
        formPanels[step].classList.add('js-active');
        
        // Atualiza a barra de progresso: Remove 'js-active' de todos os botões de progresso
        progressButtons.forEach((button, index) => {
            // Se o botão representa um passo anterior ou o passo atual, adiciona 'js-active'
            if (index <= step) {
                button.classList.add('js-active');
            } else {
                button.classList.remove('js-active');
            }
        });
    }
    
    // Função para ir para o próximo passo
    nextButtons.forEach(button => {
        button.addEventListener('click', function () {
            if (currentStep < formPanels.length - 1) {
                currentStep++;
                showPanel(currentStep);
            }
        });
    });
    
    // Função para voltar para o passo anterior
    prevButtons.forEach(button => {
        button.addEventListener('click', function () {
            if (currentStep > 0) {
                currentStep--;
                showPanel(currentStep);
            }
        });
    });
    
    // Adicionando a funcionalidade para os botões de progresso (permitindo clicar diretamente neles)
    progressButtons.forEach((button, index) => {
        button.addEventListener('click', function () {
            currentStep = index; // Atualiza o passo atual para o botão clicado
            showPanel(currentStep); // Exibe o painel correspondente
        });
    });
    
    // Inicializa o primeiro painel
    showPanel(currentStep);
    
    });