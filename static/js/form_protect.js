document.addEventListener('DOMContentLoaded', function () {
    let isFormDirty = false;
    let pendingNavigationUrl = null;
    let activeFormName = null;

    // All forms with data-form-name
    const forms = document.querySelectorAll('form[data-form-name]');
    const modal = document.getElementById('unsavedChangesModal');
    const stayBtn = modal.querySelector('#stayOnPageBtn');
    const leaveBtn = modal.querySelector('#leaveWithoutSavingBtn');
    const saveBtn = modal.querySelector('#saveAndContinueBtn');
    const modalMessage = modal.querySelector('#unsavedChangesMessage');

    // Track changes on all forms
    forms.forEach(form => {
        const formName = form.getAttribute('data-form-name');

        form.addEventListener('input', () => {
            isFormDirty = true;
            activeFormName = formName;
        });

        form.addEventListener('submit', () => {
            isFormDirty = false;
        });
    });

  // Track changes in TinyMCE editors
  // console.log('form_protect.js loaded');
  // console.log('Checking for tinymce:', window.tinymce);

  if (window.tinymce) {
    // console.log('TinyMCE found');

    // Handle editors that are already initialized
    tinymce.get().forEach(function(editor) {
      // console.log('Found existing editor:', editor.id);
      editor.on('change', function() {
        // console.log('TinyMCE content changed:', editor.id);
        isFormDirty = true;
        const textarea = editor.getElement();
        const form = textarea.closest('form[data-form-name]');
        if (form) {
          activeFormName = form.getAttribute('data-form-name');
        }
      });
    });

    // Also handle editors that get added later
    tinymce.on('addeditor', function(e) {
      // console.log('TinyMCE editor added:', e.editor.id);
      const editor = e.editor;
      editor.on('change', function() {
        // console.log('TinyMCE content changed:', editor.id);
        isFormDirty = true;
        const textarea = editor.getElement();
        const form = textarea.closest('form[data-form-name]');
        if (form) {
          activeFormName = form.getAttribute('data-form-name');
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
                modalMessage.textContent = `You have unsaved changes in the ${activeFormName}.`;
                showModal();
            }
        });
    });

    // Stay on page
    stayBtn.addEventListener('click', function () {
        hideModal();
    });

    // Leave without saving
    leaveBtn.addEventListener('click', function () {
        isFormDirty = false;
        hideModal();
        if (pendingNavigationUrl) {
            window.location.href = pendingNavigationUrl;
        }
    });

    // Save and continue
    saveBtn.addEventListener('click', function () {
        if (!activeFormName) return;
        const formToSave = [...forms].find(f => f.getAttribute('data-form-name') === activeFormName);
        if (!formToSave) return;

        // Update the hidden 'next' input so the view redirects correctly
        const nextInput = formToSave.querySelector('input[name="next"]');
        nextInput.value = pendingNavigationUrl;
        // if (nextInput && pendingNavigationUrl) {
        //     nextInput.value = pendingNavigationUrl;
        // }

        isFormDirty = false;
        hideModal();
        formToSave.submit();
    });

    // Modal show/hide helpers
    function showModal() {
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

        // Mark dirty when text inputs change
        form.addEventListener('input', () => {
            isFormDirty = true;
            activeFormName = formName;
        });

        // Mark dirty when files are selected
        const fileInputs = form.querySelectorAll('input[type="file"]');
        fileInputs.forEach(fInput => {
            fInput.addEventListener('change', () => {
                if (fInput.files.length > 0) {
                    isFormDirty = true;
                    activeFormName = formName;
                }
            });
        });

        // Reset dirty flag on submit
        form.addEventListener('submit', () => {
            isFormDirty = false;
        });
    });
});
