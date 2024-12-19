
(function () {
    'use strict'

    var forms = document.querySelectorAll('.needs-validation')

    Array.prototype.slice.call(forms)
        .forEach(function (form) {
            form.addEventListener('submit', function (event) {
                var inputs = form.querySelectorAll('.form-control');
                var isValid = true;

                inputs.forEach(function (input) {
                    var inputGroup = input.closest('.input-group');
                    if (input.checkValidity()) {
                        inputGroup.classList.remove('is-invalid');
                        inputGroup.classList.add('is-valid');
                        inputGroup.classList.add('is-filled');
                    } else {
                        inputGroup.classList.remove('is-valid');
                        inputGroup.classList.add('is-invalid');
                        inputGroup.classList.add('is-filled');
                        isValid = false;
                    }
                });

                if (!isValid) {
                    event.preventDefault();
                    event.stopPropagation();
                }

                form.classList.add('was-validated');

                if (isValid) {
                    // Desabilitar o botão e adicionar o ícone de loading
                    var submitBtn = document.getElementById('submitBtn');
                    submitBtn.disabled = true;  // Desabilita o botão

                    // Adicionar o ícone de loading dentro do botão
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Carregando...';

                    form.submit();
                }
            }, false);
        });
})()