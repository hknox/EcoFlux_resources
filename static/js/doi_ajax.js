document.addEventListener('DOMContentLoaded', function () {
  const DOI_FORM_NAME = 'DOI record';
  const DOI_DIRTY_MESSAGE = 'You have an unsaved DOI record. Please save or cancel it before navigating away.';

  function getCsrfToken() {
    return document.cookie.split(';')
      .map(c => c.trim())
      .find(c => c.startsWith('csrftoken='))
      ?.split('=')[1];
  }

  function postJson(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams(data),
    }).then(r => r.json());
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function setDirty() {
    window.formProtect?.setDirty(DOI_FORM_NAME, DOI_DIRTY_MESSAGE);
  }

  function clearDirty() {
    window.formProtect?.clearDirty();
  }

  const addBtn     = document.getElementById('doi-add-btn');
  const addForm    = document.getElementById('doi-add-form');
  const saveBtn    = document.getElementById('doi-save-btn');
  const cancelBtn  = document.getElementById('doi-cancel-btn');
  const labelInput = document.getElementById('doi-label-input');
  const linkInput  = document.getElementById('doi-link-input');
  const errorsDiv  = document.getElementById('doi-errors');
  const list       = document.getElementById('doi-list');

  if (!addBtn) return;  // not on a page with the DOI section

  // Register a live dirty check — called at modal-open time, not at input time.
  // This avoids relying on a flag that can be stomped by unrelated input events
  // on the main form.
  const ajaxDirtyCheck = function () {
    const formVisible = addForm && addForm.style.display !== 'none';
    const hasContent = !!(labelInput?.value.trim() || linkInput?.value.trim());
    return formVisible && hasContent;
  };
  ajaxDirtyCheck.message = DOI_DIRTY_MESSAGE;
  window.formProtect?.registerAjaxDirtyCheck(ajaxDirtyCheck);


  // ── Mark dirty when user types in the Add form ───────────────────────────
  [labelInput, linkInput].forEach(input => {
    input?.addEventListener('input', function () {
      if (this.value.trim()) setDirty();
    });
  });

  // ── Intercept main form submit if DOI Add form has unsaved content ────────
  const siteForm = document.querySelector('form[data-form-name]');
  siteForm?.addEventListener('submit', function (e) {
    const formVisible = addForm && addForm.style.display !== 'none';
    const hasContent = labelInput?.value.trim() || linkInput?.value.trim();
    if (formVisible && hasContent) {
      e.preventDefault();
      if (confirm('You have an unsaved DOI record. Save the site anyway and discard the DOI entry?')) {
        clearDirty();
        siteForm.submit();
      }
      // If they cancel, they stay on the page with the DOI form still open
    }
  });

  // ── Open accordion then show Add form ────────────────────────────────────
  addBtn.addEventListener('click', function () {
    const sectionId = this.dataset.sectionId;
    const accordion = document.getElementById(sectionId + 'Collapse');

    function showAddForm() {
      addForm.style.display = '';
      labelInput.focus();
    }

    if (accordion && !accordion.classList.contains('show')) {
      let bsCollapse = bootstrap.Collapse.getInstance(accordion);
      if (!bsCollapse) {
        bsCollapse = new bootstrap.Collapse(accordion, { toggle: false });
      }
      accordion.addEventListener('shown.bs.collapse', showAddForm, { once: true });
      bsCollapse.show();
    } else {
      showAddForm();
    }
  });

  // ── Cancel ───────────────────────────────────────────────────────────────
  cancelBtn?.addEventListener('click', function () {
    addForm.style.display = 'none';
    labelInput.value = '';
    linkInput.value = '';
    errorsDiv.innerHTML = '';
    clearDirty();
  });

  // ── Save DOI ─────────────────────────────────────────────────────────────
  saveBtn?.addEventListener('click', function () {
    errorsDiv.innerHTML = '';

    postJson(saveBtn.dataset.addUrl, {
      label: labelInput.value.trim(),
      doi_link: linkInput.value.trim(),
    }).then(data => {
      if (data.ok) {
        document.getElementById('doi-empty-msg')?.remove();

        if (!list.querySelector('.doi-header')) {
          const header = document.createElement('div');
          header.className = 'row mb-1 text-muted small fw-semibold doi-header';
          header.innerHTML = '<div class="col-3">Label</div><div class="col-7">DOI link</div>';
          list.prepend(header);
        }

        const row = document.createElement('div');
        row.className = 'row align-items-center mb-2 doi-row';
        row.dataset.doiId = data.id;
        row.innerHTML = `
          <div class="col-3">
            <input type="text" class="form-control form-control-sm"
                   value="${escapeHtml(data.label)}" disabled>
          </div>
          <div class="col-7">
            <input type="url" class="form-control form-control-sm"
                   value="${escapeHtml(data.doi_link)}" disabled>
          </div>
          <div class="col-auto">
            <button type="button" class="btn btn-danger btn-sm doi-remove-btn"
                    data-doi-id="${data.id}"
                    data-remove-url="${escapeHtml(data.remove_url)}">
              <i class="bi bi-trash"></i> Remove
            </button>
          </div>`;
        list.appendChild(row);

        addForm.style.display = 'none';
        labelInput.value = '';
        linkInput.value = '';
        clearDirty();
      } else {
        // Show field errors but stay dirty — user still has unsaved input
        const msgs = Object.values(data.errors).join(' ');
        errorsDiv.innerHTML = `<div class="text-danger small">${escapeHtml(msgs)}</div>`;
      }
    }).catch(() => {
      // Stay dirty on network error
      errorsDiv.innerHTML = '<div class="text-danger small">Network error. Please try again.</div>';
    });
  });

  // ── Remove (delegated to list) ────────────────────────────────────────────
  list?.addEventListener('click', function (e) {
    const btn = e.target.closest('.doi-remove-btn');
    if (!btn) return;
    if (!confirm('Remove this DOI record?')) return;

    const row = btn.closest('.doi-row');

    postJson(btn.dataset.removeUrl, {}).then(data => {
      if (data.ok) {
        row.remove();
        if (!list.querySelector('.doi-row')) {
          list.querySelector('.doi-header')?.remove();
          if (!list.querySelector('#doi-empty-msg')) {
            const msg = document.createElement('p');
            msg.id = 'doi-empty-msg';
            msg.className = 'text-muted';
            msg.textContent = 'No DOI records for this site yet.';
            list.prepend(msg);
          }
        }
        // Remove is already persisted — no dirty state to set or clear
      } else {
        alert('Failed to remove DOI record. Please try again.');
      }
    }).catch(() => alert('Network error. Please try again.'));
  });

});
