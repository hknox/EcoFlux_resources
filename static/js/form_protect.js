let dirty = false

function attachDirtyListeners(container) {
    container.querySelectorAll('input, textarea, select').forEach(function (el) {
        el.addEventListener('input', () => {
            dirty = true;
        });
        el.addEventListener('change', () => {
            dirty = true;
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form.track-unsaved');
    if (!form)
        return

    attachDirtyListeners(form);
    form.addEventListener('submit', () => { dirty = false; });

});

document.addEventListener('click', function(e) {
    if (!dirty) return;

    // Allow clicks that don't navigate
    // Get closest <a> or <button> to clicked element if any
    const target = e.target.closest('a, button');

    // If no link or button, do nothing
    if (!target) return;

    // If it's a delete button, let it handle its own confirmation
    if (target.classList.contains('btn-delete')) return;

    // If it's a link or cancel button, intercept it
    const href = target.getAttribute('href');
    const isNavigation = href && !href.startsWith('#') && !target.hasAttribute('download');
    if (isNavigation || target.classList.contains('btn-cancel')) {
        const confirmed = confirm("You have unsaved changes. Are you sure you want to leave?\n(Click OK to leave without saving changes or\n click Cancel to stay on this page.)");
        // alert("OK");
        if (!confirmed) {
            e.preventDefault();  // stop the navigation
        } else {
            dirty = false;  // suppress the upcoming beforeunload dialog
        };
    };
});

// This catches Back button, tab close, reload, etc.
window.addEventListener('beforeunload', function (e) {
    if (!dirty) return;
    e.preventDefault();   // Required for Firefox
    e.returnValue = '';   // Triggers the browser's confirmation prompt
});

// This is to protect formset row deletion when there is data:
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.remove-form-row').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      // Find the containing row
      var row = e.target.closest('.formset-row');
      // Check for any non-empty field in the row
      var hasData = false;
      row.querySelectorAll('input, select, textarea').forEach(function (field) {
        // You might want to check for checked checkboxes/radios too
        if (
          (field.type === 'checkbox' || field.type === 'radio') ? field.checked :
          field.value.trim() !== ''
        ) {
          hasData = true;
        }
      });
      // Prevent deletion or show warning
      if (hasData) {
        if (!confirm('This row has data. Are you sure you want to delete it?')) {
          e.preventDefault();
          return;
        }
      }
      // Mark the hidden DELETE input
      var deleteInput = row.querySelector('input[type="hidden"][name$="-DELETE"]');
        if (deleteInput) {
        deleteInput.value = "on";
      }
      // Hide the row instead of removing it
      row.style.display = "none";
    });
  });
});
