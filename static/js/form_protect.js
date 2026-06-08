document.addEventListener('DOMContentLoaded', function () {
    let isFormDirty = false;
    let isMainFormDirty = false;
    let mainFormName = null;
    let pendingNavigationUrl = null;
    let activeFormName = null;
    let activeFormMessage = null;
    let isAjaxDirtyFn = null;

    // All forms with data-form-name
    const forms = document.querySelectorAll('form[data-form-name]');
    const modal = document.getElementById('unsavedChangesModal');
    const stayBtn = modal.querySelector('#stayOnPageBtn');
    const leaveBtn = modal.querySelector('#leaveWithoutSavingBtn');
    const saveBtn = modal.querySelector('#saveAndContinueBtn');
    const modalMessage = modal.querySelector('#unsavedChangesMessage');

    // Shared state so other scripts (doi_ajax.js etc.) can set dirty flag
    window.formProtect = {
        setDirty(formName, message) {
            isFormDirty = true;
            activeFormName = formName;
            activeFormMessage = message || null;
        },
        clearDirty() {
            // Only clears AJAX dirty state — main form dirt is tracked separately.
            // If the main form was also dirty, restore that state.
            if (isMainFormDirty) {
                isFormDirty = true;
                activeFormName = mainFormName;
                activeFormMessage = null;
            } else {
                isFormDirty = false;
                activeFormName = null;
                activeFormMessage = null;
            }
        },
        registerAjaxDirtyCheck(fn) {
            // fn should return true if an AJAX widget has unsaved content
            isAjaxDirtyFn = fn;
        },
    };

    // Track changes on all forms
    forms.forEach(form => {
        const formName = form.getAttribute('data-form-name');

        form.addEventListener('input', () => {
            isFormDirty = true;
            isMainFormDirty = true;
            activeFormName = formName;
            mainFormName = formName;
            activeFormMessage = null;
        });

        form.addEventListener('submit', () => {
            isFormDirty = false;
            isMainFormDirty = false;
        });
    });

    // Track changes in TinyMCE editors
    if (window.tinymce) {
        tinymce.get().forEach(function(editor) {
            editor.on('change', function() {
                isFormDirty = true;
                isMainFormDirty = true;
                activeFormMessage = null;
                const textarea = editor.getElement();
                const form = textarea.closest('form[data-form-name]');
                if (form) {
                    activeFormName = form.getAttribute('data-form-name');
                    mainFormName = activeFormName;
                }
            });
        });

        tinymce.on('addeditor', function(e) {
            const editor = e.editor;
            editor.on('change', function() {
                isFormDirty = true;
                isMainFormDirty = true;
                activeFormMessage = null;
                const textarea = editor.getElement();
                const form = textarea.closest('form[data-form-name]');
                if (form) {
                    activeFormName = form.getAttribute('data-form-name');
                    mainFormName = activeFormName;
                }
            });
        });
    }

    // Intercept clicks on links and buttons that navigate away
    document.querySelectorAll('a, button').forEach(link => {
        link.addEventListener('click', function (e) {
            const href = link.getAttribute('href');
            const isNavigation = href && !href.startsWith('#') && !link.hasAttribute('download');
            if (!isNavigation && !link.classList.contains('btn-cancel')) return;

            if (isFormDirty && !link.hasAttribute('data-bypass-protect')) {
                e.preventDefault();
                pendingNavigationUrl = href;
                // Prevent beforeunload from also firing a browser dialogue
                isFormDirty = false;
                showModal();
            }
        });
    });

    // Stay on page
    stayBtn.addEventListener('click', function () {
        // Restore dirty state — user chose to stay
        isFormDirty = isMainFormDirty || (isAjaxDirtyFn ? isAjaxDirtyFn() : false);
        hideModal();
    });

    // Leave without saving
    leaveBtn.addEventListener('click', function () {
        isFormDirty = false;
        isMainFormDirty = false;
        hideModal();
        if (pendingNavigationUrl) {
            window.location.href = pendingNavigationUrl;
        }
    });

    // Save and continue (only shown when dirty source is an HTML form)
    saveBtn.addEventListener('click', function () {
        if (!activeFormName) return;
        const formToSave = [...forms].find(f => f.getAttribute('data-form-name') === activeFormName);
        if (!formToSave) return;

        const nextInput = formToSave.querySelector('input[name="next"]');
        nextInput.value = pendingNavigationUrl;

        isFormDirty = false;
        isMainFormDirty = false;
        hideModal();
        formToSave.submit();
    });

    // Show modal — check AJAX dirty state fresh at open time
    function showModal() {
        const isAjax = isAjaxDirtyFn ? isAjaxDirtyFn() : false;
        saveBtn.toggleAttribute('hidden', isAjax);
        modalMessage.textContent = isAjax
            ? isAjaxDirtyFn.message
            : (activeFormMessage || `You have unsaved changes in the ${activeFormName}.`);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    function hideModal() {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) bsModal.hide();
    }

    // Warn on browser tab close/refresh
    window.addEventListener('beforeunload', function (e) {
        if (isFormDirty) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    // Protect file input widgets too (for photo uploading)
    forms.forEach(form => {
        const formName = form.getAttribute('data-form-name');

        form.addEventListener('input', () => {
            isFormDirty = true;
            isMainFormDirty = true;
            activeFormName = formName;
            mainFormName = formName;
            activeFormMessage = null;
        });

        const fileInputs = form.querySelectorAll('input[type="file"]');
        fileInputs.forEach(fInput => {
            fInput.addEventListener('change', () => {
                if (fInput.files.length > 0) {
                    isFormDirty = true;
                    isMainFormDirty = true;
                    activeFormName = formName;
                    mainFormName = formName;
                    activeFormMessage = null;
                }
            });
        });

        form.addEventListener('submit', () => {
            isFormDirty = false;
            isMainFormDirty = false;
        });
    });
});
