/**
 * @file state.js
 * @description
 * Handles logical dependencies between form fields.
 * Includes toggling, enabling/disabling, and value adjustments.
 */

/**
 * Bind dependency between #is_active and #is_member checkboxes.
 * If #is_active is unchecked:
 * - disables #is_member
 * - unchecks #is_member
 * 
 * When #is_active is checked again:
 * - re-enables #is_member
 */
export function bindActiveMemberDependency() {
  const activeCheckbox = document.getElementById("is_active");
  const memberCheckbox = document.getElementById("is_member");

  if (!activeCheckbox || !memberCheckbox) return;

  const updateMemberState = () => {
    if (!activeCheckbox.checked) {
      memberCheckbox.checked = false;
      memberCheckbox.disabled = true;
    } else {
      memberCheckbox.disabled = false;
    }
  };

  activeCheckbox.addEventListener("change", updateMemberState);
  updateMemberState(); // initial state
}
