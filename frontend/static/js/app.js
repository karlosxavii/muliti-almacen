document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    if (sidebar && toggle) {
        toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    }

    document.querySelectorAll("[data-alert-close]").forEach((button) => {
        button.addEventListener("click", () => {
            const alert = button.closest("[data-alert]");
            if (alert) {
                alert.remove();
            }
        });
    });

    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.getAttribute("data-confirm") || "¿Confirmas esta acción?";
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
