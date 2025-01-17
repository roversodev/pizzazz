document.querySelectorAll('.categoria-ativo').forEach(function (checkbox) {
    checkbox.addEventListener('change', function () {
        let itemId = this.getAttribute('data-item-id');
        fetch(`/empresas/{{empresa.cnpj|remove_mask}}/cardapio/categoria/${itemId}/toggle-ativo`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showSweetAlert("Sucesso", "Status de ativo alterado com sucesso", "success");
                }
            });
    });
});

document.querySelectorAll('.item-ativo-vende').forEach(function (checkbox) {
    checkbox.addEventListener('change', function () {
        let itemId = this.getAttribute('data-item-id');
        fetch(`/empresas/{{empresa.cnpj|remove_mask}}/cardapio/item/${itemId}/toggle-ativo`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showSweetAlert("Sucesso", "Status de ativo alterado com sucesso", "success");
                }
            });
    });
});

// Script para configurar o formulário de deletação
document.addEventListener("DOMContentLoaded", function () {
    const deleteLinks = document.querySelectorAll('.dele-link');

    deleteLinks.forEach(function (link) {
        link.addEventListener('click', function (event) {
            // Impedir o comportamento padrão do link
            event.preventDefault();

            // Pega a URL de deleção e o ID do ingrediente
            const url = link.getAttribute('data-url');

            // Atualiza a ação do formulário
            const formDeletar = document.getElementById('formDeletar');
            formDeletar.setAttribute('action', url);
        });
    });
});