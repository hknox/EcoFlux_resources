// JavaScript to handle the modal + AJAX
document.addEventListener('DOMContentLoaded', function () {
  const modal = new bootstrap.Modal(document.getElementById('ajaxModal'));
  const modalBody = document.querySelector('#ajaxModal .modal-body');
  const modalTitle = document.querySelector('#ajaxModal .modal-title');

  // Intercept clicks
  document.body.addEventListener('click', function (e) {
    if (e.target.closest('.ajax-modal-link')) {
      e.preventDefault();
      const url = e.target.closest('.ajax-modal-link').getAttribute('href');

      fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
        .then(res => res.json())
        .then(data => {
            // HERE is where we insert the action label, (New or Edit) Equipment
          modalTitle.textContent = 'Hi there';
          modalBody.innerHTML = data.html;
          modal.show();
        });
    }
  });

  // Handle form submission inside modal
  modalBody.addEventListener('submit', function (e) {
    if (e.target.id === 'ajaxForm') {
      e.preventDefault();
      const form = e.target;
      const formData = new FormData(form);

      fetch(form.action || window.location.href, {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'}
      })
            .then(res => console.log(res.json())) //res.json())
      .then(data => {
        if (data.success) {
          modal.hide();
          // Replace or append row
          let row = document.querySelector(`#equip-row-${data.object_id}`);
          if (row) {
            row.outerHTML = data.row_html;
          } else {
            document.querySelector('#equipment-table tbody').insertAdjacentHTML('beforeend', data.row_html);
          }
        } else {
          modalBody.innerHTML = data.html; // re-render with errors
        }
      });
    }
  });
});
