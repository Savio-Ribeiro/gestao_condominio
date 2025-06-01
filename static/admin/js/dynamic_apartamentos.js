document.addEventListener('DOMContentLoaded', function () {
  const quantidadeInput = document.getElementById('id_quantidade_apartamentos');
  const formContainer = document.querySelector('.form-row');  // ou localize onde inserir os campos
  const tipoUsuario = document.getElementById('id_tipo_usuario');

  function createField(id, label, required = true) {
      const div = document.createElement('div');
      div.className = 'form-row field-custom-apto';

      const labelEl = document.createElement('label');
      labelEl.setAttribute('for', id);
      labelEl.textContent = label;

      const inputEl = document.createElement('input');
      inputEl.setAttribute('type', 'text');
      inputEl.setAttribute('id', id);
      inputEl.setAttribute('name', id);
      inputEl.className = 'vTextField';
      if (required) {
          inputEl.setAttribute('required', 'required');
      }

      div.appendChild(labelEl);
      div.appendChild(inputEl);
      return div;
  }

  function renderApartmentFields() {
      // Remove antigos
      document.querySelectorAll('.field-custom-apto').forEach(el => el.remove());

      const qtd = parseInt(quantidadeInput.value);
      if (!qtd || qtd < 1) return;

      const insertAfter = document.getElementById('id_quantidade_apartamentos').closest('.form-row');

      for (let i = 1; i <= qtd; i++) {
          const numField = createField(`id_apartamento_numero_${i}`, `Apartamento ${i} - Número`);
          const blocoField = createField(`id_apartamento_bloco_${i}`, `Apartamento ${i} - Bloco (opcional)`, false);

          insertAfter.parentNode.insertBefore(numField, insertAfter.nextSibling);
          insertAfter.parentNode.insertBefore(blocoField, numField.nextSibling);
      }
  }

  if (quantidadeInput) {
      quantidadeInput.addEventListener('change', renderApartmentFields);
      renderApartmentFields();  // Inicializar
  }
});
