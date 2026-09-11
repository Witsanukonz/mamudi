document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('[data-menu-toggle]');
  const menu = document.getElementById('mobile-menu');
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      menu.hidden = !menu.hidden;
      toggle.setAttribute('aria-expanded', String(!menu.hidden));
      toggle.setAttribute('aria-label', menu.hidden ? 'Open navigation' : 'Close navigation');
    });
  }
  const input = document.querySelector('[data-image-input]');
  const preview = document.querySelector('[data-image-preview]');
  let previewUrl;
  if (input && preview) {
    input.addEventListener('change', () => {
      const file = input.files[0];
      if (!file) return;
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
        input.setCustomValidity('Choose a JPEG, PNG or WebP image up to 5 MB.');
        input.reportValidity();
        return;
      }
      input.setCustomValidity('');
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrl = URL.createObjectURL(file);
      preview.src = previewUrl;
    });
  }
  document.querySelectorAll('[data-submit-once]').forEach(button => {
    button.form.addEventListener('submit', () => {
      button.disabled = true;
      button.textContent = 'Placing your order…';
    });
  });
});

