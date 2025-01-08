function showSweetAlert(title, text, icon) {
    Swal.fire({
        title: title || 'Atenção',
        text: text || 'Mensagem não especificada',
        icon: icon || 'info',
        showConfirmButton: true,
        confirmButtonText: 'Ok',
        customClass: {
            confirmButton: 'btn bg-gradient-dark',
            cancelButton: 'btn btn-danger'
        },
        didOpen: () => {
            // Removendo a classe 'swal2-styled' dos botões
            const confirmButton = document.querySelector('.swal2-confirm');
            const cancelButton = document.querySelector('.swal2-cancel');
    
            if (confirmButton) confirmButton.classList.remove('swal2-styled');
            if (cancelButton) cancelButton.classList.remove('swal2-styled');
        }
    });
}
