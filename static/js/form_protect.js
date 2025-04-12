function confirmDelete() {
    return confirm("Are you sure you want to delete this location? This cannot be undone.");
}

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

function confirmCancel(event) {
  const form = event.target.closest('form.track-unsaved');
  if (form && hasFormChanged(form)) {
    const proceed = confirm("You have unsaved changes. Are you sure you want to cancel?");
    if (!proceed) {
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  }
  return true;
}

document.addEventListener('DOMContentLoaded', function () {
  const trackedForms = document.querySelectorAll('form.track-unsaved');
  trackedForms.forEach(form => {
    saveOriginalData(form);
  });

  document.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', function (e) {
      const href = link.getAttribute('href');
      if (!href || href.startsWith('#') || link.hasAttribute('data-skip-unsaved-check')) {
        return;
      }

      const dirtyForm = Array.from(trackedForms).find(form => hasFormChanged(form));
      if (dirtyForm) {
        const confirmLeave = confirm("You have unsaved changes. Are you sure you want to leave this page?");
        if (!confirmLeave) {
          e.preventDefault();
        }
      }
    });
  });
});
