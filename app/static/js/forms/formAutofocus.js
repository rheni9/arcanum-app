// static/js/forms/formAutofocus.js

export function autoFocusFirstField() {
  const forms = document.querySelectorAll("form");
  forms.forEach(form => {
    const first = form.querySelector("input:not([type=hidden]):not([disabled]), textarea:not([disabled]), select:not([disabled])");
    if (first) first.focus();
  });
}

autoFocusFirstField();
