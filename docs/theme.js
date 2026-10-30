/* Apply the saved theme before the stylesheet paints. */
(() => {
  "use strict";
  const key = "intent-translation-theme";
  const choices = ["system", "light", "dark"];
  const labels = { system: "System", light: "Light", dark: "Dark" };
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  let preference = "system";
  try {
    const saved = localStorage.getItem(key);
    if (choices.includes(saved)) preference = saved;
  } catch { /* Theme selection also works when browser storage is unavailable. */ }

  function apply() {
    const resolved = preference === "system" ? (system.matches ? "dark" : "light") : preference;
    document.documentElement.dataset.theme = resolved;
    document.documentElement.style.colorScheme = resolved;
    const button = document.querySelector("#theme-toggle");
    if (!button) return;
    const next = choices[(choices.indexOf(preference) + 1) % choices.length];
    const description = `Theme: ${labels[preference]}. Switch to ${labels[next]}.`;
    button.setAttribute("aria-label", description);
    button.title = description;
    button.querySelectorAll("[data-theme-icon]").forEach((icon) => {
      icon.toggleAttribute("hidden", icon.dataset.themeIcon !== preference);
    });
  }

  apply();
  system.addEventListener("change", apply);
  document.addEventListener("DOMContentLoaded", apply);
  document.addEventListener("click", (event) => {
    if (!event.target.closest("#theme-toggle")) return;
    preference = choices[(choices.indexOf(preference) + 1) % choices.length];
    try { localStorage.setItem(key, preference); } catch { /* Keep the selection for this page. */ }
    apply();
  });
  window.addEventListener("storage", (event) => {
    if (event.key !== key && event.key !== null) return;
    preference = choices.includes(event.newValue) ? event.newValue : "system";
    apply();
  });
})();
