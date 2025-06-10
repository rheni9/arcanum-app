export function bindActiveMemberPublicDependency() {
  const activeCheckbox = document.getElementById("is_active");
  const memberCheckbox = document.getElementById("is_member");
  const publicCheckbox = document.getElementById("is_public");

  if (!activeCheckbox) return;

  const update = () => {
    const enabled = activeCheckbox.checked;

    if (memberCheckbox) {
      memberCheckbox.disabled = !enabled;
      if (!enabled) memberCheckbox.checked = false;
    }

    if (publicCheckbox) {
      publicCheckbox.disabled = !enabled;
      if (!enabled) publicCheckbox.checked = false;
    }
  };

  activeCheckbox.addEventListener("change", update);
  update();
}
