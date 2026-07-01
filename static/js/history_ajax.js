document.addEventListener('DOMContentLoaded', function () {

  const HISTORY_FORM_NAME = 'history record';
  const HISTORY_DIRTY_MESSAGE = 'You have an unsaved history record. Please save or cancel it before navigating away.';

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
    window.formProtect?.setDirty(HISTORY_FORM_NAME, HISTORY_DIRTY_MESSAGE);
  }

  function clearDirty() {
    window.formProtect?.clearDirty();
  }

  const addBtn    = document.getElementById('history-add-btn');
  const addForm   = document.getElementById('history-add-form');
  const saveBtn   = document.getElementById('history-save-btn');
  const cancelBtn = document.getElementById('history-cancel-btn');
  const dateInput = document.getElementById('history-date-input');
  const noteInput = document.getElementById('history-note-input');
  const errorsDiv = document.getElementById('history-errors');
  const list      = document.getElementById('history-list');

  if (!addBtn) return;  // not on a page with the history section

  // Initialise flatpickr on the date input
  if (typeof flatpickr !== 'undefined' && dateInput) {
    flatpickr(dateInput, { dateFormat: 'Y-m-d', allowInput: true });
  }

  // Register a live dirty check at modal-open time
  const ajaxDirtyCheck = function () {
    const formVisible = addForm && addForm.style.display !== 'none';
    const hasContent = !!(dateInput?.value.trim() || noteInput?.value.trim());
    return formVisible && hasContent;
  };
  ajaxDirtyCheck.message = HISTORY_DIRTY_MESSAGE;
  window.formProtect?.registerAjaxDirtyCheck(ajaxDirtyCheck);

  // ── Mark dirty when user types in the Add form ───────────────────────────
  [dateInput, noteInput].forEach(input => {
    input?.addEventListener('input', function () {
      if (this.value.trim()) setDirty();
    });
  });

  // ── Intercept main form submit if history Add form has unsaved content ────
  const equipmentForm = document.querySelector('form[data-form-name]');
  equipmentForm?.addEventListener('submit', function (e) {
    const formVisible = addForm && addForm.style.display !== 'none';
    const hasContent = dateInput?.value.trim() || noteInput?.value.trim();
    if (formVisible && hasContent) {
      e.preventDefault();
      if (confirm('You have an unsaved history record. Save the equipment record anyway and discard the history entry?')) {
        clearDirty();
        equipmentForm.submit();
      }
    }
  });

  // ── Open accordion then show Add form ────────────────────────────────────
  addBtn.addEventListener('click', function () {
    const sectionId = this.dataset.sectionId;
    const accordion = document.getElementById(sectionId + 'Collapse');

    function showAddForm() {
      addForm.style.display = '';
      dateInput.focus();
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
    if (dateInput._flatpickr) dateInput._flatpickr.clear();
    else dateInput.value = '';
    noteInput.value = '';
    errorsDiv.innerHTML = '';
    clearDirty();
  });

  // ── Save history record ──────────────────────────────────────────────────
  saveBtn?.addEventListener('click', function () {
    errorsDiv.innerHTML = '';

    postJson(saveBtn.dataset.addUrl, {
      date: dateInput.value.trim(),
      note: noteInput.value.trim(),
    }).then(data => {
      if (data.ok) {
        document.getElementById('history-empty-msg')?.remove();

        if (!list.querySelector('.history-header')) {
          const header = document.createElement('div');
          header.className = 'row mb-1 text-muted small fw-semibold history-header';
          header.innerHTML = '<div class="col-3">Date</div><div class="col">Note</div>';
          list.prepend(header);
        }

        const row = document.createElement('div');
        row.className = 'row align-items-center mb-2 history-row';
        row.dataset.historyId = data.id;

        row.innerHTML = `
          <div class="col-3">
            <input type="text" class="form-control form-control-sm history-date"
                   value="${escapeHtml(data.date)}">
          </div>
          <div class="col">
            <textarea class="form-control form-control-sm history-note" rows="2">${escapeHtml(data.note)}</textarea>
          </div>
          <div class="col-auto">
            <button type="button" class="btn btn-primary btn-sm history-update-btn me-1"
                    data-update-url="${escapeHtml(data.update_url)}">
              <i class="bi bi-save"></i> Save
            </button>
            <button type="button" class="btn btn-danger btn-sm history-remove-btn"
                    data-history-id="${data.id}"
                    data-remove-url="${escapeHtml(data.remove_url)}">
              <i class="bi bi-trash"></i> Remove
            </button>
          </div>`;

        list.appendChild(row);

        addForm.style.display = 'none';
        if (dateInput._flatpickr) dateInput._flatpickr.clear();
        else dateInput.value = '';
        noteInput.value = '';
        clearDirty();
      } else {
        const msgs = Object.values(data.errors).join(' ');
        errorsDiv.innerHTML = `<div class="text-danger small">${escapeHtml(msgs)}</div>`;
      }
    }).catch(() => {
      errorsDiv.innerHTML = '<div class="text-danger small">Network error. Please try again.</div>';
    });
  });

  // ── Update (delegated to list) ────────────────────────────────────────────
  list?.addEventListener('click', function (e) {
    const btn = e.target.closest('.history-update-btn');
    if (!btn) return;

    const row = btn.closest('.history-row');
    const date = row.querySelector('.history-date').value.trim();
    const note = row.querySelector('.history-note').value.trim();

    postJson(btn.dataset.updateUrl, {
      date: date,
      note: note,
    }).then(data => {
      if (!data.ok) {
        const msgs = Object.values(data.errors).join(' ');
        alert(msgs);
      }
    }).catch(() => alert('Network error. Please try again.'));
  });

  // ── Remove (delegated to list) ────────────────────────────────────────────
  list?.addEventListener('click', function (e) {
    const btn = e.target.closest('.history-remove-btn');
    if (!btn) return;
    if (!confirm('Remove this history record?')) return;

    const row = btn.closest('.history-row');

    postJson(btn.dataset.removeUrl, {}).then(data => {
      if (data.ok) {
        row.remove();
        if (!list.querySelector('.history-row')) {
          list.querySelector('.history-header')?.remove();
          if (!list.querySelector('#history-empty-msg')) {
            const msg = document.createElement('p');
            msg.id = 'history-empty-msg';
            msg.className = 'text-muted';
            msg.textContent = 'No history records for this piece of equipment yet.';
            list.prepend(msg);
          }
        }
      } else {
        alert('Failed to remove history record. Please try again.');
      }
    }).catch(() => alert('Network error. Please try again.'));
  });

});
