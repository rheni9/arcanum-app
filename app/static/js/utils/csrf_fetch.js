/**
 * @file csrf_fetch.js
 * @description
 * Wraps fetch() and injects the Flask-WTF CSRF token into request headers.
 * Automatically sets the correct Content-Type for JSON payloads.
 */

/**
 * Performs a secure fetch with automatic CSRF header injection.
 *
 * @param {RequestInfo} input - The URL or Request object.
 * @param {RequestInit} [init={}] - Additional fetch options.
 * @returns {Promise<Response>} - The fetch response promise.
 */
export function csrfFetch(input, init = {}) {
  const token = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");

  init.headers = init.headers || {};
  init.headers["X-CSRFToken"] = token;

  // Automatically set JSON content type if needed
  if (
    init.body != null &&
    !(init.body instanceof FormData) &&
    !init.headers["Content-Type"]
  ) {
    init.headers["Content-Type"] = "application/json";
  }

  return fetch(input, init);
}
