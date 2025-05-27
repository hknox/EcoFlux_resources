// Modular add/remove form row script for Django formsets
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.add-form-row').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const prefix = btn.getAttribute('data-formset-prefix');
      const formsetDiv = document.getElementById(prefix + '-formset');
      const totalForms = formsetDiv.querySelector('input[name$="-TOTAL_FORMS"]');
      const currentCount = parseInt(totalForms.value, 10);
      const formRows = formsetDiv.querySelectorAll('.formset-row');
      if (formRows.length === 0) return; // Defensive
      const newRow = formRows[0].cloneNode(true);

      // Clear values for all inputs/selects
      newRow.querySelectorAll('input,textarea,select').forEach(function(input) {
        if (input.type === 'checkbox' || input.type === 'radio') {
          input.checked = false;
        } else if (input.type === 'file') {
          input.value = '';
        } else {
          input.value = '';
        }
        // Update name and id with new index
        if (input.name) {
          input.name = input.name.replace(/-\d+-/, '-' + currentCount + '-');
        }
        if (input.id) {
          input.id = input.id.replace(/-\d+-/, '-' + currentCount + '-');
        }
      });

      // Hide any error messages
      newRow.querySelectorAll('.invalid-feedback, .help-block, .errorlist').forEach(function(el) {
        el.innerHTML = '';
        el.style.display = 'none';
      });

      formsetDiv.insertBefore(newRow, btn);
      totalForms.value = currentCount + 1;
    });
  });

  document.addEventListener('click', function(event) {
    if (event.target.classList.contains('remove-form-row')) {
      const formRow = event.target.closest('.formset-row');
      const deleteCheckbox = formRow.querySelector('input[type="checkbox"][name$="DELETE"]');
      if (deleteCheckbox) {
        deleteCheckbox.checked = true;
        formRow.style.display = 'none';
      } else {
        formRow.remove();
      }
    }
  });
});
