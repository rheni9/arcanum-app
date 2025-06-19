/**
 * @file auth.js
 * @description
 * Handles user logout via AJAX with CSRF protection.
 * Ensures graceful fallback and redirect handling.
 */

import { csrfFetch } from "./utils/csrf_fetch.js";

/**
 * Binds AJAX-based logout to logout link.
 * Prevents default navigation and sends a POST request with CSRF token.
 * Redirects to the URL provided in JSON response or falls back to "/".
 */
export function bindAuth() {
  const logoutLink = document.querySelector(".logout-link");

  if (!logoutLink) return;

  logoutLink.addEventListener("click", async (event) => {
    event.preventDefault();

    try {
      const response = await csrfFetch(logoutLink.href, {
        method: "POST",
      });

      if (response.ok) {
        const data = await response.json();
        const target = data.redirect || "/";
        window.location.href = target;
      } else {
        console.error(`Logout failed: HTTP ${response.status} ${response.statusText}`);
        window.location.href = "/";
      }
    } catch (error) {
      console.error("Logout AJAX error:", error);
      window.location.href = "/";
    }
  });
}
