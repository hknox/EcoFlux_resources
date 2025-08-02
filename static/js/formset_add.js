// Modular add/remove form row script for Django formsets
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.add-form-row').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const prefix = btn.getAttribute('data-formset-prefix');
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
                // Find and scroll to the first empty visible row
                formRows.forEach(function (row) {
                    if (row.style.display === 'none') return;

                    const inputs = row.querySelectorAll('input, select, textarea');
                    let hasData = false;

                    // inputs.forEach(function (field) {
                    for (const field of inputs) {
                        if (
                            (field.type === 'checkbox' || field.type === 'radio') ? field.checked :
                                field.value.trim() !== ''
                        ) {
                            hasData = true;
                            break;
                        }
                    };

                    if (!hasData) {
                        // Scroll to it
                        row.scrollIntoView({ behavior: 'smooth', block: 'center' });

                        // Flash it with a highlight
                        row.classList.add('border', 'border-warning', 'rounded');
                        row.style.transition = 'background-color 0.6s ease-in-out';
                        row.style.backgroundColor = '#fff3cd'; // light yellow

                        const firstInput = row.querySelector('input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])');

                        if (firstInput) {
                            firstInput.focus();
                        }
                        setTimeout(() => {
                            row.style.backgroundColor = '';
                            row.classList.remove('border', 'border-warning', 'rounded');
                        }, 4000);
                    }
                });

                return;
            }


            // if (hasVisibleEmptyRow) {
            //     const toast = new bootstrap.Toast(document.getElementById('formset-toast'));
            //     toast.show();
            //     return
            // }


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
            // Re-initialize flatpickr on new date fields in the added row only
            if (typeof flatpickr !== 'undefined') {
                newRow.querySelectorAll('.datepicker').forEach(function(input) {
                    if (input._flatpickr) {
                        input._flatpickr.destroy();  // Clean up previous instance if any
                    }
                    flatpickr(input, { dateFormat: "Y-m-d" });  // Apply fresh flatpickr
                });
            }
            // Hook up dirty form tracking
            if (typeof attachDirtyListeners === 'function') {
                attachDirtyListeners(newRow);
            }
        });
    });
});
