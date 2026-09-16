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
  const imageSection = document.querySelector('[data-product-images]');
  if (imageSection) {
    const countSelect = imageSection.querySelector('[data-image-count]');
    const slots = [...imageSection.querySelectorAll('[data-image-slot-container]')];
    const dialog = imageSection.querySelector('[data-crop-dialog]');
    const canvas = imageSection.querySelector('[data-crop-canvas]');
    const zoomInput = imageSection.querySelector('[data-crop-zoom]');
    const context = canvas.getContext('2d');
    const sourceImage = new Image();
    sourceImage.crossOrigin = 'anonymous';
    let activeInput = null;
    let activeSlot = null;
    let temporaryUrl = '';
    let scale = 1;
    let x = 0;
    let y = 0;
    let dragging = false;
    let pointerX = 0;
    let pointerY = 0;

    const validImage = file => ['image/jpeg', 'image/png', 'image/webp'].includes(file.type) && file.size <= 5 * 1024 * 1024;
    const clampPosition = () => {
      const width = sourceImage.naturalWidth * scale;
      const height = sourceImage.naturalHeight * scale;
      x = Math.min(0, Math.max(canvas.width - width, x));
      y = Math.min(0, Math.max(canvas.height - height, y));
    };
    const drawCrop = () => {
      if (!sourceImage.complete || !sourceImage.naturalWidth) return;
      clampPosition();
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.drawImage(sourceImage, x, y, sourceImage.naturalWidth * scale, sourceImage.naturalHeight * scale);
    };
    const resetCrop = () => {
      const cover = Math.max(canvas.width / sourceImage.naturalWidth, canvas.height / sourceImage.naturalHeight);
      scale = cover * Number(zoomInput.value);
      x = (canvas.width - sourceImage.naturalWidth * scale) / 2;
      y = (canvas.height - sourceImage.naturalHeight * scale) / 2;
      drawCrop();
    };
    const closeCrop = ({ clearSelection = false } = {}) => {
      dialog.hidden = true;
      document.body.classList.remove('crop-dialog-open');
      if (clearSelection && activeInput && activeInput.files.length) {
        activeInput.value = '';
        const existing = activeInput.dataset.existingUrl;
        activeSlot.querySelector('[data-image-preview]').src = existing || '/static/images/product-placeholder.svg';
        activeSlot.querySelector('[data-crop-trigger]').disabled = !existing;
      }
      if (temporaryUrl) URL.revokeObjectURL(temporaryUrl);
      temporaryUrl = '';
      activeInput = null;
      activeSlot = null;
    };
    const openCrop = (input, slot) => {
      activeInput = input;
      activeSlot = slot;
      const file = input.files[0];
      const source = file ? URL.createObjectURL(file) : input.dataset.existingUrl;
      if (!source) return;
      if (temporaryUrl) URL.revokeObjectURL(temporaryUrl);
      temporaryUrl = file ? source : '';
      zoomInput.value = '1';
      sourceImage.onload = resetCrop;
      sourceImage.src = source;
      dialog.hidden = false;
      document.body.classList.add('crop-dialog-open');
    };
    const updateSlots = () => {
      const count = Number(countSelect.value);
      slots.forEach((slot, index) => {
        const input = slot.querySelector('[data-product-image-input]');
        const active = index < count;
        slot.hidden = !active;
        input.disabled = !active;
        input.required = active && !input.dataset.existingUrl;
      });
    };

    countSelect.addEventListener('change', updateSlots);
    slots.forEach(slot => {
      const input = slot.querySelector('[data-product-image-input]');
      const cropButton = slot.querySelector('[data-crop-trigger]');
      input.addEventListener('change', () => {
        const file = input.files[0];
        if (!file) return;
        if (!validImage(file)) {
          input.setCustomValidity('Choose a JPEG, PNG or WebP image up to 5 MB.');
          input.reportValidity();
          input.value = '';
          return;
        }
        input.setCustomValidity('');
        cropButton.disabled = false;
        openCrop(input, slot);
      });
      cropButton.addEventListener('click', () => openCrop(input, slot));
    });
    zoomInput.addEventListener('input', resetCrop);
    canvas.addEventListener('pointerdown', event => {
      dragging = true;
      pointerX = event.clientX;
      pointerY = event.clientY;
      canvas.setPointerCapture(event.pointerId);
    });
    canvas.addEventListener('pointermove', event => {
      if (!dragging) return;
      x += event.clientX - pointerX;
      y += event.clientY - pointerY;
      pointerX = event.clientX;
      pointerY = event.clientY;
      drawCrop();
    });
    canvas.addEventListener('pointerup', () => { dragging = false; });
    canvas.addEventListener('pointercancel', () => { dragging = false; });
    imageSection.querySelectorAll('[data-crop-cancel]').forEach(button => button.addEventListener('click', () => closeCrop({ clearSelection: Boolean(activeInput && activeInput.files.length) })));
    imageSection.querySelector('[data-crop-apply]').addEventListener('click', () => {
      const output = document.createElement('canvas');
      output.width = 600;
      output.height = 750;
      const ratio = output.width / canvas.width;
      output.getContext('2d').drawImage(sourceImage, x * ratio, y * ratio, sourceImage.naturalWidth * scale * ratio, sourceImage.naturalHeight * scale * ratio);
      output.toBlob(blob => {
        if (!blob || !activeInput) return;
        const files = new DataTransfer();
        const originalName = activeInput.files[0]?.name || `product-${activeInput.dataset.imageSlot}.jpg`;
        const baseName = originalName.replace(/\.[^.]+$/, '');
        files.items.add(new File([blob], `${baseName}-cropped.jpg`, { type: 'image/jpeg', lastModified: Date.now() }));
        activeInput.files = files.files;
        activeInput.setCustomValidity('');
        const preview = activeSlot.querySelector('[data-image-preview]');
        preview.src = URL.createObjectURL(blob);
        activeSlot.querySelector('[data-crop-trigger]').disabled = false;
        closeCrop();
      }, 'image/jpeg', 0.9);
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !dialog.hidden) closeCrop({ clearSelection: Boolean(activeInput && activeInput.files.length) });
    });
    updateSlots();
  }

  document.querySelectorAll('[data-gallery-thumbnail]').forEach(button => {
    button.addEventListener('click', () => {
      const mainImage = document.querySelector('[data-gallery-main]');
      if (!mainImage) return;
      mainImage.src = button.dataset.src;
      document.querySelectorAll('[data-gallery-thumbnail]').forEach(item => item.removeAttribute('aria-current'));
      button.setAttribute('aria-current', 'true');
    });
  });
  document.querySelectorAll('[data-submit-once]').forEach(button => {
    button.form.addEventListener('submit', () => {
      button.disabled = true;
      button.textContent = 'Placing your order…';
    });
  });
});
