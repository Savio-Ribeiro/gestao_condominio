document.addEventListener('DOMContentLoaded', function() {
    const tipoUsuarioField = document.getElementById('id_tipo_usuario');
    const quantidadeField = document.getElementById('id_quantidade_apartamentos').parentNode.parentNode;

    function toggleApartamentos() {
        if (tipoUsuarioField.value === 'proprietario' || tipoUsuarioField.value === 'imobiliaria') {
            quantidadeField.style.display = 'block';
        } else {
            quantidadeField.style.display = 'none';
        }
    }

    if (tipoUsuarioField) {
        tipoUsuarioField.addEventListener('change', toggleApartamentos);
        toggleApartamentos(); // Executa ao carregar
    }

    // Atualiza dinamicamente os inlines
    const quantidadeInput = document.getElementById('id_quantidade_apartamentos');
    if (quantidadeInput) {
        quantidadeInput.addEventListener('change', function() {
            const qtd = parseInt(this.value) || 0;
            const inlineGroup = document.getElementById('apartamento_set-group');
            const existingRows = inlineGroup.querySelectorAll('.dynamic-apartamento_set');

            // Remove linhas extras
            for (let i = qtd; i < existingRows.length; i++) {
                existingRows[i].querySelector('input[name$="-DELETE"]').checked = true;
                existingRows[i].style.display = 'none';
            }

            // Adiciona novas linhas se necessário
            if (qtd > existingRows.length) {
                const addButton = inlineGroup.querySelector('.add-row a');
                for (let i = existingRows.length; i < qtd; i++) {
                    addButton.click();
                }
            }
        });
    }
});
