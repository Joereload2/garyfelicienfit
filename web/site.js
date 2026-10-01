"use strict";

function bindOfferForm() {
    if (document.getElementById("offerModal")) {
        wireOfferModal();
        return;
    }
    var html = ""
        + '<div class="modal" id="offerModal">'
        + '<form class="card" id="offerForm">'
        + "<h3>¿Quieres 50% de descuento?</h3>"
        + '<p class="muted">Déjanos tu correo y te enviamos el código. El precio con descuento es $225.000 CLP por 3 meses (lista $450.000).</p>'
        + '<div id="offerError" class="error"></div>'
        + '<div id="offerOk" class="ok"></div>'
        + '<label for="offerEmail">Correo electrónico</label>'
        + '<input id="offerEmail" type="email" required autocomplete="email" placeholder="tucorreo@email.com">'
        + '<div class="actions">'
        + '<button type="button" class="btn btn-ghost" id="offerClose">Ahora no</button>'
        + '<button type="submit" class="btn btn-gold" id="offerSubmit">Enviarme el código</button>'
        + "</div>"
        + '<p class="note">Revisa bandeja de entrada y spam. El código no se muestra aquí.</p>'
        + "</form></div>";
    document.body.insertAdjacentHTML("beforeend", html);
    wireOfferModal();
}

function wireOfferModal() {
    var modal = document.getElementById("offerModal");
    var form = document.getElementById("offerForm");
    if (!modal || !form || form.getAttribute("data-bound")) return;
    form.setAttribute("data-bound", "1");
    function openOffer() {
        modal.classList.add("open");
        var input = document.getElementById("offerEmail");
        if (input) setTimeout(function () { input.focus(); }, 50);
    }
    function closeOffer() {
        modal.classList.remove("open");
    }
    document.querySelectorAll("[data-open-offer]").forEach(function (btn) {
        btn.addEventListener("click", openOffer);
    });
    var closer = document.getElementById("offerClose");
    if (closer) closer.addEventListener("click", closeOffer);
    modal.addEventListener("click", function (e) {
        if (e.target.id === "offerModal") closeOffer();
    });
    form.addEventListener("submit", async function (ev) {
        ev.preventDefault();
        var err = document.getElementById("offerError");
        var ok = document.getElementById("offerOk");
        var btn = document.getElementById("offerSubmit");
        if (err) err.classList.remove("show");
        if (ok) ok.classList.remove("show");
        var email = document.getElementById("offerEmail").value.trim();
        if (btn) btn.disabled = true;
        try {
            var res = await fetch("/api/oferta-3meses", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email }),
            });
            var data = await res.json().catch(function () { return {}; });
            if (!res.ok || !data.ok) {
                if (err) {
                    err.textContent = data.error || "No se pudo enviar el código.";
                    err.classList.add("show");
                }
                if (btn) btn.disabled = false;
                return;
            }
            if (ok) {
                ok.textContent = data.message || "Revisa tu correo. Ahí va el código.";
                ok.classList.add("show");
            }
            form.querySelectorAll("input, button[type=submit]").forEach(function (el) {
                el.disabled = true;
            });
        } catch (e) {
            if (err) {
                err.textContent = "Sin conexión con el servidor.";
                err.classList.add("show");
            }
            if (btn) btn.disabled = false;
        }
    });
    if (location.pathname.indexOf("3meses") >= 0 && !sessionStorage.getItem("gff_offer_seen")) {
        sessionStorage.setItem("gff_offer_seen", "1");
        setTimeout(openOffer, 1200);
    }
}

function imcClass(imc) {
    if (imc < 18.5) return { label: "Bajo peso", cls: "calc-imc-bajo" };
    if (imc < 25) return { label: "Peso normal", cls: "calc-imc-ok" };
    if (imc < 30) return { label: "Sobrepeso", cls: "calc-imc-sobre" };
    if (imc < 35) return { label: "Obesidad grado I", cls: "calc-imc-obe" };
    if (imc < 40) return { label: "Obesidad grado II", cls: "calc-imc-obe" };
    return { label: "Obesidad grado III", cls: "calc-imc-obe" };
}

function runCalculator(ev) {
    ev.preventDefault();
    const err = document.getElementById("calcError");
    const results = document.getElementById("calcResults");
    err.classList.remove("show");
    results.hidden = true;

    const sex = document.getElementById("calcSex").value;
    const age = Number(document.getElementById("calcAge").value);
    const height = Number(document.getElementById("calcHeight").value);
    const weight = Number(document.getElementById("calcWeight").value);
    const act = Number(document.getElementById("calcActivity").value);

    function fail(msg) {
        err.textContent = msg;
        err.classList.add("show");
    }

    if (!sex || !age || !height || !weight || !act) {
        fail("Completa todos los campos.");
        return;
    }
    if (age < 15 || age > 80 || age !== Math.floor(age)) {
        fail("La edad debe ser un número entero entre 15 y 80 años.");
        return;
    }
    if (height > 0 && height < 3) {
        fail("¿Quisiste decir " + Math.round(height * 100) + " cm? La altura va en centímetros, no en metros.");
        return;
    }
    if (height < 120 || height > 230) {
        fail("La altura debe estar entre 120 y 230 cm.");
        return;
    }
    if (weight < 30 || weight > 250) {
        fail("El peso debe estar entre 30 y 250 kg.");
        return;
    }

    const imc = weight / Math.pow(height / 100, 2);
    const tmb = (10 * weight) + (6.25 * height) - (5 * age) + (sex === "m" ? 5 : -161);
    const get = tmb * act;
    const cat = imcClass(imc);

    document.getElementById("calcImcN").textContent = (Math.round(imc * 10) / 10).toString();
    const badge = document.getElementById("calcImcBadge");
    badge.textContent = cat.label;
    badge.className = "calc-badge " + cat.cls;
    document.getElementById("calcTmbN").textContent = Math.round(tmb) + " kcal/día";
    document.getElementById("calcGetN").textContent = Math.round(get) + " kcal/día";
    document.getElementById("calcCut").textContent = Math.round(get - 500) + "–" + Math.round(get - 300) + " kcal";
    document.getElementById("calcHold").textContent = Math.round(get) + " kcal/día";
    document.getElementById("calcGain").textContent = Math.round(get + 300) + "–" + Math.round(get + 500) + " kcal";
    document.getElementById("calcSuggest").textContent = imc >= 25
        ? "Con este IMC, bajar de peso suele ser el foco. El acompañamiento de 3 meses adapta comida y rutina a esa meta; no es otro producto."
        : "Si quieres ganar músculo o verte más firme, el mismo acompañamiento de 3 meses se adapta: cambia la comida y la rutina, no el servicio.";
    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

var calcForm = document.getElementById("calcForm");
if (calcForm) calcForm.addEventListener("submit", runCalculator);
if (document.querySelector("[data-open-offer]")) bindOfferForm();
