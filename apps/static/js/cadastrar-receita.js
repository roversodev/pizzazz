// Função para atualizar a imagem com base no item selecionado
function updateImage() {
    var selectElement = document.getElementById("cardapio");
    var selectedOption = selectElement.options[selectElement.selectedIndex];

    // Pega a URL da imagem associada ao item selecionado
    var imageUrl = selectedOption.getAttribute("data-img");

    // Atualiza a imagem
    var imageElement = document.getElementById("cardapioImage");
    imageElement.src = imageUrl;

    // Caso nenhum item seja selecionado, você pode limpar a imagem ou definir uma imagem padrão
    if (imageUrl === "null") {
        imageElement.src = "{% static 'assets/img/calabresa.jpg' %}"; // Ou defina uma imagem padrão aqui
    }
    var cardapioId = document.getElementById('cardapio').value;
    var mensagemCompleto = document.getElementById('mensagem-completo');
    
    // Se o valor do select estiver vazio, não faz nada
    if (!cardapioId) {
        return;
    }
    
    // Faz a requisição AJAX para verificar o campo 'completo' do cardápio
    fetch(`/empresas/{{empresa.cnpj|remove_mask}}/verificar_completo/?cardapio_id=${cardapioId}`)
        .then(response => response.json())
        .then(data => {
            if (data.completo) {
                // Se 'completo' for True, exibe a mensagem
                mensagemCompleto.style.display = 'block';
            } else {
                // Caso contrário, esconde a mensagem
                mensagemCompleto.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Erro ao verificar cardápio:', error);
            mensagemCompleto.style.display = 'none';
        });
}

// Função que é chamada sempre que um checkbox de ingrediente é alterado
document.addEventListener("DOMContentLoaded", function () {
    const quantidadeIngredientesContainer = document.getElementById("quantidade-ingredientes");

    // Função para atualizar os campos de quantidade
    const updateQuantidadeFields = () => {
        quantidadeIngredientesContainer.innerHTML = ''; // Limpar os campos anteriores

        // Buscar todos os ingredientes selecionados
        const ingredientesSelecionados = document.querySelectorAll('input[name="ingredientes"]:checked');

        // Para cada ingrediente selecionado, criar um campo de quantidade
        ingredientesSelecionados.forEach(checkbox => {
            const ingredienteId = checkbox.value;
            const unidade = checkbox.getAttribute('data-unidade');
            const ingredienteNome = checkbox.nextElementSibling.textContent;

            // Criar o campo de quantidade
            const div = document.createElement('div');
            div.classList.add('col-sm-4', 'mb-3', 'input-group', 'input-group-outline', 'is-filled');
            div.innerHTML = `
                <label class="form-label" for="quantidade_${ingredienteId}" style="width: 96.8%">${ingredienteNome} (${unidade})</label>
                <input type="number" name="quantidade_${ingredienteId}" id="quantidade_${ingredienteId}" class="form-control"  step="0.01" pattern="^\d+(\.\d{1,2})?$" required>
                <div class="invalid-feedback">Digite um numero. Exemplo: 0,15</div>
            `;
            quantidadeIngredientesContainer.appendChild(div);
        });
    };

    // Adicionar eventos de mudança nos checkboxes
    const checkboxes = document.querySelectorAll('input[name="ingredientes"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateQuantidadeFields);
    });
});