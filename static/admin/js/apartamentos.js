// static/admin/js/apartamentos.js
document.addEventListener('DOMContentLoaded', function() {
  const container = document.getElementById('apartamentos-container');
  const qtdInput = document.getElementById('id_quantidade_apartamentos');

  if (qtdInput) {
      qtdInput.addEventListener('change', updateApartamentosFields);
      updateApartamentosFields();
  }

  function updateApartamentosFields() {
      if (!container) return;

      container.innerHTML = '';
      const qtd = parseInt(qtdInput.value) || 0;

      for (let i = 1; i <= qtd; i++) {
          const fieldGroup = document.createElement('div');
          fieldGroup.className = 'form-row field-apartamento';
          fieldGroup.innerHTML = `
              <div>
                  <label for="id_apartamento_numero_${i}">Apartamento ${i} - Número:</label>
                  <input type="text" name="apartamento_numero_${i}" id="id_apartamento_numero_${i}">
              </div>
              <div>
                  <label for="id_apartamento_bloco_${i}">Apartamento ${i} - Bloco:</label>
                  <input type="text" name="apartamento_bloco_${i}" id="id_apartamento_bloco_${i}">
              </div>
          `;
          container.appendChild(fieldGroup);
      }
  }
});
