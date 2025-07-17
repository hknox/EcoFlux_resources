// Modular add/remove form row script for Django formsets
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.add-form-row').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const prefix = btn.getAttribute('data-formset-prefix');
            console.log("Prefix ",prefix)
            const formsetDiv = document.getElementById(prefix + '-formset');
            const totalForms = formsetDiv.querySelector('input[name$="-TOTAL_FORMS"]');
            const currentCount = parseInt(totalForms.value, 10);

            // Check for existing visible empty row
            const formRows = formsetDiv.querySelectorAll('.formset-row');
            let hasVisibleEmptyRow = false;

            formRows.forEach(function (row) {
                if (row.style.display === 'none') return;

                const inputs = row.querySelectorAll('input, select, textarea');
                let hasData = false;

                inputs.forEach(function (field) {
                    if (
                        (field.type === 'checkbox' || field.type === 'radio') ? field.checked :
                            field.value.trim() !== ''
                    ) {
                        hasData = true;
                    }
                });

                if (!hasData) {
                    hasVisibleEmptyRow = true;
                }
            });

            if (hasVisibleEmptyRow) {
                const toast = new bootstrap.Toast(document.getElementById('formset-toast'));
                toast.show();
                return
            }


            // Clone and insert row as before...
            const emptyForm = document.getElementById(`${prefix}-empty-form`);
            if (!emptyForm) return;

            const newRow = emptyForm.cloneNode(true);
            newRow.id = '';  // remove the ID so it's not duplicated
            newRow.style.display = '';  // make it visible

            // Update all input/select/textarea fields
            newRow.querySelectorAll('input,textarea,select').forEach(function(input) {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = false;
                } else if (input.type === 'file') {
                    input.value = '';
                } else {
                    input.value = '';
                }
                // Update name and id with new index (handles __prefix__ and existing indices)
                if (input.name) {
                    input.name = input.name.replace(/(__prefix__|\d+)/g, currentCount);
                }
                if (input.id) {
                    input.id = input.id.replace(/(__prefix__|\d+)/g, currentCount);
                }
            });
            // Hide any error messages
            newRow.querySelectorAll('.invalid-feedback, .help-block, .errorlist').forEach(function(el) {
                el.innerHTML = '';
                el.style.display = 'none';
            });

            // Add the row before the empty-form template
            formsetDiv.insertBefore(newRow, emptyForm);
            totalForms.value = currentCount + 1;
            if (typeof attachDirtyListeners === 'function') {
                attachDirtyListeners(newRow);
}
        });
    });
});
