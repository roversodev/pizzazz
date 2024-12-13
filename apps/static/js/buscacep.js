function buscaCep() {
    let cep = document.getElementById("txtCep").value.trim();
    if (cep !== "") {
        let url = "https://viacep.com.br/ws/" + cep + "/json";
        let req = new XMLHttpRequest();
        req.open("GET", url);
        req.send();

        req.onload = function () {
            if (req.status == 200) {
                let endereco = JSON.parse(req.response);
                if (endereco.erro) {
                    alert("CEP não encontrado!");
                } else {
                    // Preenche os campos com os dados do CEP
                    document.getElementById("endereco").value = endereco.logradouro || "";
                    document.getElementById("bairro").value = endereco.bairro || "";
                    document.getElementById("estado").value = endereco.estado || "";
                    document.getElementById("municipio").value = endereco.uf || "";

                    // Adiciona a classe 'is-filled' nos campos preenchidos
                    setFieldAsFilled("endereco");
                    setFieldAsFilled("bairro");
                    setFieldAsFilled("estado");
                    setFieldAsFilled("municipio");
                }
            } else {
                alert("Erro ao fazer a requisição");
            }
        };

        req.onerror = function () {
            alert("Erro de rede, não foi possível acessar o serviço ViaCEP.");
        };
    }
}

// Função para adicionar a classe 'is-filled' se o campo estiver preenchido
function setFieldAsFilled(fieldId) {
    let field = document.getElementById(fieldId);
    if (field.value.trim() !== "") {
        field.closest('.input-group').classList.add('is-filled');
    } else {
        field.closest('.input-group').classList.remove('is-filled');
    }
}

window.onload = function () {
    let cep = document.getElementById("txtCep");
    let fields = document.querySelectorAll('.form-control');

    fields.forEach(function (field) {
        // Adiciona a classe 'is-focused' quando o campo recebe foco
        field.addEventListener('focus', function () {
            field.closest('.input-group').classList.add('is-focused');
        });

        // Remove a classe 'is-focused' quando o campo perde o foco
        field.addEventListener('blur', function () {
            if (field.value === '') {
                field.closest('.input-group').classList.remove('is-focused');
            }
        });

        // Adiciona a classe 'is-filled' quando o campo tem valor
        field.addEventListener('input', function () {
            if (field.value !== '') {
                field.closest('.input-group').classList.add('is-filled');
            } else {
                field.closest('.input-group').classList.remove('is-filled');
            }
        });
    });

    // Adicionar máscara ao CEP
    cep.addEventListener("blur", buscaCep);
};