function confirmDelete() {
  return confirm("Are you sure you want to delete this item?\nThis action cannot be undone.");
}
let dirty = false

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form.track-unsaved');
    if (!form)
        return
    console.log('2', form);

    form.addEventListener('input', () => { console.log("input->dirty"); dirty = true });
    form.addEventListener('change', () => { console.log("change->dirty"); dirty = true });
    form.addEventListener('submit', () => { dirty = false; });

});

document.addEventListener('click', function(e) {
    if (!dirty) return;
    console.log("dirty as sin!");

    // Allow clicks that don't navigate
    // Get closest <a> or <button> to clicked element if any
    const target = e.target.closest('a, button');
    console.log(target);

    // If no link or button, do nothing
    if (!target) return;

    // If it's a delete button, let it handle its own confirmation
    if (target.classList.contains('btn-delete')) return;

    // If it's a link or cancel button, intercept it
    const href = target.getAttribute('href');
    const isNavigation = href && !href.startsWith('#') && !target.hasAttribute('download');
    console.log("href", href);
    console.log("isNav", isNavigation);
    console.log("iscancel", target.classList);
    if (isNavigation || target.classList.contains('btn-cancel')) {
        const confirmed = confirm("You have unsaved changes. Are you sure you want to leave?");
        console.log("confirmed", confirmed);
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
