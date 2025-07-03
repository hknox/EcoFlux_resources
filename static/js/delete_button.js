document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.btn-delete').forEach(function (button) {
    button.addEventListener('click', function () {
      const url = button.dataset.deleteUrl;
      const csrfToken = button.dataset.csrfToken;

      if (!confirm("Are you sure you want to delete this item?")) return;

      const form = document.createElement('form');
      form.method = 'POST';
      form.action = url;

      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'csrfmiddlewaretoken';
      input.value = csrfToken;
      form.appendChild(input);

      document.body.appendChild(form);
      form.submit();
    });
  });
});
