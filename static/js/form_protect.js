function confirmDelete() {
  return confirm("Are you sure you want to delete this item? This cannot be undone.");
}

// Store the original data of tracked forms using a WeakMap (to avoid memory leaks)
const formDataMap = new WeakMap();

function saveOriginalData(form) {
  const originalData = {};
  const inputs = form.querySelectorAll('input, textarea, select');
  inputs.forEach(input => {
    if (input.name) {
      originalData[input.name] = input.value;
    }
  });
  formDataMap.set(form, originalData);
}

function hasFormChanged(form) {
  const originalData = formDataMap.get(form);
  if (!originalData) return false;

  const inputs = form.querySelectorAll('input, textarea, select');
  for (let input of inputs) {
    if (input.name && input.value !== originalData[input.name]) {
      return true;
    }
  }
  return false;
}

document.addEventListener('DOMContentLoaded', function () {
  const trackedForms = document.querySelectorAll('form.track-unsaved');

  // Store the original data for all tracked forms
  trackedForms.forEach(form => {
    saveOriginalData(form);
  });

  // Handle all <a> links globally
  document.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', function (e) {
      const href = link.getAttribute('href');

      // Skip external links, anchors, and explicitly marked safe links
      if (!href || href.startsWith('#') || link.hasAttribute('data-skip-unsaved-check')) {
        return;
      }

      // Check if any tracked form is dirty
      const dirtyForm = Array.from(trackedForms).find(form => hasFormChanged(form));
      if (dirtyForm) {
        const confirmLeave = confirm("You have unsaved changes. Are you sure you want to leave this page?");
        if (!confirmLeave) {
          e.preventDefault();
          e.stopPropagation();
        }
      }
    });
  });
});
