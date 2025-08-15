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
});
