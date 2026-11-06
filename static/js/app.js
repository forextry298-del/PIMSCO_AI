document.addEventListener('click', function (event) {
  const toggle = event.target.closest('[data-toggle-password]');
  if (toggle) {
    const input = document.getElementById(toggle.dataset.togglePassword);
    if (input) {
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      toggle.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
      toggle.innerHTML = show ? '<i data-lucide="eye-off" aria-hidden="true"></i>' : '<i data-lucide="eye" aria-hidden="true"></i>';
      if (window.lucide) window.lucide.createIcons();
    }
  }

  const copyButton = event.target.closest('[data-copy]');
  if (copyButton) {
    const target = document.getElementById(copyButton.dataset.copy);
    if (target && navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(target.textContent.trim()).then(() => {
        copyButton.textContent = 'Copied';
        setTimeout(() => { copyButton.textContent = 'Copy'; }, 1400);
      }).catch(() => { copyButton.textContent = target.textContent.trim(); });
    } else if (target) {
      const range = document.createRange();
      range.selectNodeContents(target);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      copyButton.textContent = 'Select code';
    }
  }
});


document.addEventListener('DOMContentLoaded', function () {
  if (window.lucide) window.lucide.createIcons();
});
