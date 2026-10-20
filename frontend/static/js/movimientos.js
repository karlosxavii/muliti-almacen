document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-movimiento-form]");
    if (!form) {
        return;
    }

    const tbody = document.getElementById("lineas");
    const template = document.getElementById("linea-template");
    const addButton = document.getElementById("add-linea");
    const tipo = document.getElementById("tipo-movimiento");
    const hint = document.getElementById("linea-hint");
    const totalLabel = document.getElementById("total-unidades");

    const recalcular = () => {
        let total = 0;
        tbody.querySelectorAll(".linea-cantidad").forEach((input) => {
            const value = Number.parseInt(input.value, 10);
            if (!Number.isNaN(value) && value > 0) {
                total += value;
            }
        });
        if (totalLabel) {
            totalLabel.textContent = total.toLocaleString("es");
        }
    };

    const actualizarTipo = () => {
        const esEntrada = tipo.value === "ENTRADA";
        if (hint) {
            hint.textContent = esEntrada
                ? "Entrada: selecciona el estante de destino."
                : "Salida: selecciona el estante de origen (el destino es opcional para transferencias).";
        }
        if (esEntrada) {
            tbody.querySelectorAll(".linea-origen").forEach((select) => {
                select.value = "";
            });
        }
    };

    const limpiarFila = (row) => {
        row.querySelectorAll("input").forEach((input) => {
            input.value = "";
        });
        row.querySelectorAll("select").forEach((select) => {
            select.value = "";
        });
    };

    if (addButton && template && tbody) {
        addButton.addEventListener("click", () => {
            tbody.appendChild(template.content.cloneNode(true));
            actualizarTipo();
            recalcular();
        });
    }

    if (tbody) {
        tbody.addEventListener("click", (event) => {
            const button = event.target.closest("[data-remove-linea]");
            if (!button) {
                return;
            }
            const row = button.closest("tr");
            const rows = tbody.querySelectorAll("tr");
            if (rows.length === 1) {
                limpiarFila(row);
            } else {
                row.remove();
            }
            recalcular();
        });

        tbody.addEventListener("input", (event) => {
            if (event.target.classList.contains("linea-cantidad")) {
                recalcular();
            }
        });
    }

    if (tipo) {
        tipo.addEventListener("change", actualizarTipo);
    }

    actualizarTipo();
    recalcular();
});
