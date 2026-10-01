"use strict";

(function () {
    var KEY = "gff_reg";

    function readReg() {
        try {
            var data = JSON.parse(localStorage.getItem(KEY) || "null");
            if (data && data.email && data.ads === true) return data;
        } catch (e) {}
        return null;
    }

    function isReg() {
        return document.body.classList.contains("reg-ok") || !!readReg();
    }

    function openGate() {
        document.body.classList.add("reg-open");
        var input = document.getElementById("regName");
        if (input) setTimeout(function () { input.focus(); }, 50);
    }

    function closeGate() {
        document.body.classList.remove("reg-open");
    }

    function unlock() {
        document.body.classList.add("reg-ok");
        closeGate();
        var hash = location.hash;
        if (hash) {
            var el = document.querySelector(hash);
            if (el) setTimeout(function () { el.scrollIntoView({ behavior: "smooth", block: "start" }); }, 50);
        }
        document.dispatchEvent(new Event("gff-reg-ok"));
    }

    window.gffIsReg = isReg;
    window.gffNeedReg = function () {
        if (isReg()) return false;
        openGate();
        return true;
    };

    if (readReg()) unlock();

    function bind() {
        var form = document.getElementById("regForm");
        if (!form || form.getAttribute("data-bound")) return;
        form.setAttribute("data-bound", "1");

        document.querySelectorAll("[data-open-reg]").forEach(function (btn) {
            btn.addEventListener("click", function (ev) {
                ev.preventDefault();
                openGate();
            });
        });
        var closer = document.getElementById("regClose");
        if (closer) closer.addEventListener("click", closeGate);
        var gate = document.getElementById("regGate");
        if (gate) {
            gate.addEventListener("click", function (e) {
                if (e.target.id === "regGate") closeGate();
            });
        }
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") closeGate();
        });

        form.addEventListener("submit", async function (ev) {
            ev.preventDefault();
            var err = document.getElementById("regError");
            var btn = document.getElementById("regSubmit");
            var ads = document.getElementById("regAds");
            if (err) err.classList.remove("show");
            if (!ads || !ads.checked) {
                if (err) {
                    err.textContent = "Hay que marcar la autorización de publicidad. No viene marcada a propósito.";
                    err.classList.add("show");
                }
                return;
            }
            var payload = {
                name: (document.getElementById("regName") || {}).value || "",
                email: (document.getElementById("regEmail") || {}).value || "",
                phone: (document.getElementById("regPhone") || {}).value || "",
                ads_consent: true,
                source: document.body.getAttribute("data-reg-source") || "herramientas"
            };
            if (btn) btn.disabled = true;
            try {
                var res = await fetch("/api/registro", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                var data = await res.json().catch(function () { return {}; });
                if (!res.ok || !data.ok) {
                    if (err) {
                        err.textContent = data.error || "No se pudo registrar.";
                        err.classList.add("show");
                    }
                    if (btn) btn.disabled = false;
                    return;
                }
                try {
                    localStorage.setItem(KEY, JSON.stringify({
                        name: payload.name.trim(),
                        email: (data.email || payload.email).trim(),
                        ads: true,
                        at: new Date().toISOString()
                    }));
                } catch (e) {}
                unlock();
            } catch (e) {
                if (err) {
                    err.textContent = "Sin conexión con el servidor. Prueba de nuevo en un momento.";
                    err.classList.add("show");
                }
                if (btn) btn.disabled = false;
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bind);
    } else {
        bind();
    }
})();
