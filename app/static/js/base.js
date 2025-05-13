/**
 * @file base.js
 * @description
 * Entry point for Arcanum frontend behavior.
 * Initializes all core UI features and event bindings.
 */

import { bindFilterForms } from "./forms/filters.js";
import { bindActiveMemberDependency } from "./forms/state.js";
import { bindDeleteConfirmations } from "./ui/confirmations.js";
import { bindClickableRows } from "./ui/clickables.js";
import { rebindAfterAjax } from "./bindings.js";
import { csrfFetch } from './csrf_fetch.js';

/**
 * Initialize all global UI behaviors after DOM is ready.
 */
document.addEventListener("DOMContentLoaded", () => {
  // AJAX-login handler (if on login page)
  const loginForm = document.querySelector('.login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async e => {
      e.preventDefault();
      const pw = loginForm.querySelector('input[name="password"]').value;
      try {
        const resp = await csrfFetch('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ password: pw })
        });
        if (resp.redirected) {
          window.location = resp.url;
        } else {
          document.body.innerHTML = await resp.text();
        }
      } catch (err) {
        console.error('Login failed', err);
      }
    });
  }

  bindFilterForms();
  bindActiveMemberDependency();
  bindDeleteConfirmations();  
  bindClickableRows();
  rebindAfterAjax();
});
