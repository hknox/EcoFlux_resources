function confirmDelete() {
  return confirm("Are you sure you want to delete this item? This cannot be undone.");
}

document.addEventListener('DOMContentLoaded', function() {
  const form = document.querySelector('form.track-unsaved');
  if (!form) return;
  let dirty = false;

  form.addEventListener('input', e => {
    dirty = true;
    console.log('[input] Detected:', e.target, 'Value:', e.target.value);
  });
  form.addEventListener('change', e => {
    dirty = true;
    console.log('[change] Detected:', e.target, 'Value:', e.target.value);
  });

  window.addEventListener('beforeunload', function(e) {
    if (dirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  // Any element with class btn-cancel will trigger the check
  const cancelBtns = form.querySelectorAll('.btn-cancel');
  cancelBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
      if (dirty && !confirm('You have unsaved changes. Are you sure you want to leave?')) {
        e.preventDefault();
      }
    });
  });

  form.addEventListener('submit', () => { dirty = false; });
});
