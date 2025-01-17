// Selecionando os botões
const casaButton = document.getElementById('casaButton');
const trabalhoButton = document.getElementById('trabalhoButton');
const hiddenInput = document.getElementById('local');

// Função para selecionar "Casa"
casaButton.addEventListener('click', function() {
    casaButton.classList.add('bg-gradient-danger');
    casaButton.classList.remove('btn-light');
    casaButton.classList.remove('text-dark');
    trabalhoButton.classList.add('btn-light');
    trabalhoButton.classList.add('text-dark');
    trabalhoButton.classList.remove('bg-gradient-danger');
    hiddenInput.value = 'casa';  // Define o valor para 'local' como 'casa'
});

// Função para selecionar "Trabalho"
trabalhoButton.addEventListener('click', function() {
    trabalhoButton.classList.add('bg-gradient-danger');
    trabalhoButton.classList.remove('btn-light');
    trabalhoButton.classList.remove('text-dark');
    casaButton.classList.add('btn-light');
    casaButton.classList.add('text-dark');
    casaButton.classList.remove('bg-gradient-danger');
    hiddenInput.value = 'trabalho';  // Define o valor para 'local' como 'trabalho'
});