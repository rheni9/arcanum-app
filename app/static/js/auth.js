/**
 * @file auth.js
 * @description
 * Handles logout via AJAX with CSRF protection.
 */

import { csrfFetch } from "./utils/csrf_fetch.js";

export function bindAuth() {
  // LOGOUT
  const logoutLink = document.querySelector(".logout-link");
  if (logoutLink) {
    logoutLink.addEventListener("click", async (e) => {
      e.preventDefault();

      try {
        const resp = await csrfFetch(logoutLink.href, {
          method: "POST",
          redirect: "manual"
        });
        const location = resp.headers.get("Location") || "/";
        window.location = location;
      } catch (err) {
        console.error("Logout AJAX error:", err);
        window.location = "/";
      }
    });
  }
}
