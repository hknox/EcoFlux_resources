function openDeleteModal(btn) {
  const url     = btn.dataset.deleteUrl;
  const type    = btn.dataset.recordType || 'Record';
  const blocked = btn.dataset.blocked === 'true';
  const reason  = btn.dataset.blockedReason || '';
  const cascade = JSON.parse(btn.dataset.cascade || '[]');

  const header       = document.getElementById('deleteModalHeader');
  const title        = document.getElementById('deleteModalTitle');
  const message      = document.getElementById('deleteModalMessage');
  const cascadeBlock = document.getElementById('deleteModalCascade');
  const cascadeIntro = document.getElementById('deleteModalCascadeIntro');
  const cascadeList  = document.getElementById('deleteModalCascadeList');
  const blockedBlock = document.getElementById('deleteModalBlocked');
  const blockedMsg   = document.getElementById('deleteModalBlockedReason');
  const form         = document.getElementById('deleteModalForm');
  const confirmBtn   = document.getElementById('deleteModalConfirmBtn');
  const cancelBtn    = document.getElementById('deleteModalCancelBtn');

  // Reset state
  cascadeBlock.classList.add('d-none');
  blockedBlock.classList.add('d-none');
  header.className = 'modal-header';

  if (blocked) {
    header.classList.add('bg-warning');
    title.textContent = `Cannot Delete ${type}`;
    message.textContent = `This ${type} cannot be deleted while it still contains Equipment records.`;
    blockedMsg.textContent = reason;
    blockedBlock.classList.remove('d-none');
    form.classList.add('d-none');
    cancelBtn.textContent = 'OK';
  } else {
    header.classList.add('bg-danger', 'text-white');
    title.textContent = `Delete ${type}`;
    message.textContent = `Are you sure you want to delete this ${type}? This action cannot be undone!`;
    form.action = url;
    form.classList.remove('d-none');
    cancelBtn.textContent = 'Cancel';

    if (cascade.length > 0) {
      cascadeIntro.textContent = `Deleting this ${type} will also permanently remove:`;
      cascadeList.innerHTML = cascade
        .map(c => `<li>${c.count} ${c.label}</li>`)
        .join('');
      cascadeBlock.classList.remove('d-none');
    }
  }

  new bootstrap.Modal(document.getElementById('deleteModal')).show();
}
