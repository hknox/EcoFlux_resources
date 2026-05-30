document.addEventListener('DOMContentLoaded', function() {

  // Handle Remove row
  function handleRemoveRow(row) {
    console.log("remove row")
    const deleteInput = row.querySelector('input[type="hidden"][name$="-DELETE"]');
    if (deleteInput) deleteInput.value = 'on';
    row.style.display = 'none';

    // Refresh the Bootstrap5 accordion (same as Add button)
    const accordion = formsetDiv.closest('.accordion-collapse');
    if (accordion) {
      const bootstrapCollapse = bootstrap.Collapse.getInstance(accordion);
      if (bootstrapCollapse && bootstrapCollapse._isShown) {
        accordion.addEventListener('hidden.bs.collapse', function() {
          bootstrapCollapse.show();
        }, { once: true });
        bootstrapCollapse.hide();
      }
    }
  }

  // Attach Remove listener for EXISTING rows (rendered from server)
  document.querySelectorAll('.formset-row .remove-form-row').forEach(function(btn) {
    const row = btn.closest('.formset-row');
    btn.addEventListener('click', function() {
      handleRemoveRow(row);
    });
  });

  // Handle Add row
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

      // Refresh the Bootstrap5 accordion - open it if closed
      const sectionId = addBtn.dataset.sectionId;
      const accordionId = sectionId + 'Collapse';
      const accordion = document.getElementById(accordionId);

      if (accordion) {
        let bootstrapCollapse = bootstrap.Collapse.getInstance(accordion);

        if (!bootstrapCollapse) {
          bootstrapCollapse = new bootstrap.Collapse(accordion, { toggle: false });
        }

        // Check if accordion has the 'show' class (means it's visually open)
        const isActuallyShown = accordion.classList.contains('show');

        if (isActuallyShown) {
          accordion.addEventListener('hidden.bs.collapse', function() {
            bootstrapCollapse.show();
          }, { once: true });
          bootstrapCollapse.hide();
        } else {
          bootstrapCollapse.show();
        }
      }

      // Initialize flatpickr on date fields
      if (typeof flatpickr !== 'undefined') {
        newRow.querySelectorAll('.datepicker').forEach(function(input) {
          if (input._flatpickr) input._flatpickr.destroy();
          flatpickr(input, { dateFormat: "Y-m-d" });
        });
      }
    }); // ← Closes the addEventListener click handler
  }); // ← Closes the forEach for add-form-row

});
