/**
 * @file csrf_fetch.js * 
 * @description
 * Wrapper around fetch() that automatically injects
 * the Flask-WTF CSRF token into the X-CSRFToken header.
 */
export function csrfFetch(input, init = {}) {
  const token = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute('content');

  init.headers = init.headers || {};
  init.headers['X-CSRFToken'] = token;

  // If posting JSON, set Content-Type
  if (
    init.body != null &&
    !(init.body instanceof FormData) &&
    !init.headers['Content-Type']
  ) {
    init.headers['Content-Type'] = 'application/json';
  }

  return fetch(input, init);
}
