"use strict";

document.getElementById("ingresoForm").addEventListener("submit", async function (ev) {
    ev.preventDefault();
    var err = document.getElementById("ingresoError");
    err.classList.remove("show");
    try {
        var res = await fetch("/api/ingreso", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: document.getElementById("inEmail").value,
                pin: document.getElementById("inPin").value
            })
        });
        var data = await res.json().catch(function () { return {}; });
        if (!res.ok || !data.ok) {
            err.textContent = data.error || "No se pudo entrar.";
            err.classList.add("show");
            return;
        }
        if (data.role === "admin") {
            localStorage.setItem("gff_admin_session", data.session);
            location.href = "/ingreso/panel";
            return;
        }
        localStorage.setItem("gff_alumno_session", data.session);
        location.href = "/alumno";
    } catch (e) {
        err.textContent = "Sin conexión.";
        err.classList.add("show");
    }
});
