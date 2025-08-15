document.addEventListener('DOMContentLoaded', function() {

  // Handle Remove row
  function handleRemoveRow(row) {
    const deleteInput = row.querySelector('input[type="hidden"][name$="-DELETE"]');
    if (deleteInput) deleteInput.value = 'on';
    row.style.display = 'none';
  }

  // Attach Remove listener for existing rows
  document.querySelectorAll('.formset-row .remove-form-row').forEach(function(btn) {
    const row = btn.closest('.formset-row');
    btn.addEventListener('click', function() {
      handleRemoveRow(row);
    });
  });

  // Add new row
  document.querySelectorAll('.add-form-row').forEach(function(addBtn) {
    addBtn.addEventListener('click', function() {
      const prefix = addBtn.dataset.formsetPrefix;
      const formsetDiv = document.getElementById(prefix + '-formset');
      const emptyForm = document.getElementById(prefix + '-empty-form');
      if (!emptyForm) return;

      const totalFormsInput = formsetDiv.querySelector('input[name$="-TOTAL_FORMS"]');
      const currentCount = parseInt(totalFormsInput.value, 10);

      const newRow = emptyForm.cloneNode(true);
      newRow.style.display = '';
      newRow.id = '';

      // Update input names/ids
      newRow.querySelectorAll('input, select, textarea').forEach(function(input) {
        if (input.name) input.name = input.name.replace(/__prefix__|\d+/g, currentCount);
        if (input.id) input.id = input.id.replace(/__prefix__|\d+/g, currentCount);
        if (input.type === 'checkbox' || input.type === 'radio') input.checked = false;
        else if (input.type !== 'file') input.value = '';
      });

      // Attach Remove listener to cloned button
      const removeBtn = newRow.querySelector('.remove-form-row');
      if (removeBtn) {
        removeBtn.addEventListener('click', function() {
          handleRemoveRow(newRow);
        });
      }

      // Insert row
      formsetDiv.insertBefore(newRow, emptyForm);
      totalFormsInput.value = currentCount + 1;

      // Initialize flatpickr on date fields
      if (typeof flatpickr !== 'undefined') {
        newRow.querySelectorAll('.datepicker').forEach(function(input) {
          if (input._flatpickr) input._flatpickr.destroy();
          flatpickr(input, { dateFormat: "Y-m-d" });
        });
      }
    });
  });

});
