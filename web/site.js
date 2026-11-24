"use strict";

// ---------- Planes y compra ----------
// Los dos planes duran 3 meses (12 semanas). La diferencia es el contacto 1 a 1.
var PLANES = {
    personalizado: {
        nombre: "Plan personalizado · 3 meses",
        precio: "USD $30",
        wa: "Hola Gary, quiero el plan personalizado de 3 meses (USD 30)",
    },
    acompanamiento: {
        nombre: "Acompañamiento 1 a 1 · 3 meses",
        precio: "USD $150 (antes USD $400)",
        wa: "Hola Gary, quiero el acompañamiento 1 a 1 de 3 meses (promo USD 150)",
    },
};
var WA_NUM = "56959128603";

function waLink(text) {
    return "https://wa.me/" + WA_NUM + "?text=" + encodeURIComponent(text);
}

function buildBuyModal() {
    if (document.getElementById("buyModal")) return;
    var html = ""
        + '<div class="modal" id="buyModal">'
        + '<form class="card" id="buyForm">'
        + '<h3 id="buyTitle">Plan</h3>'
        + '<p class="muted" id="buyLead">Deja tu correo y pasas a Mercado Pago (cobra en pesos chilenos). Al aprobarse, te llega por correo el enlace al cuestionario.</p>'
        + '<div id="buyError" class="error"></div>'
        + '<label for="buyEmail">Correo electrónico</label>'
        + '<input id="buyEmail" type="email" required autocomplete="email" placeholder="tucorreo@email.com">'
        + '<div class="actions">'
        + '<button type="button" class="btn btn-ghost" id="buyClose">Cancelar</button>'
        + '<button type="submit" class="btn btn-gold" id="buySubmit">Ir a pagar</button>'
        + "</div>"
        + '<p class="note">¿Prefieres hablar antes? <a id="buyWa" href="#" target="_blank" rel="noopener noreferrer">Escríbenos por WhatsApp</a>.</p>'
        + "</form></div>";
    document.body.insertAdjacentHTML("beforeend", html);
}

function wireBuy() {
    var buttons = document.querySelectorAll("[data-buy]");
    if (!buttons.length) return;
    // Quita un modal viejo que venga escrito en la página para usar el de aquí.
    var old = document.getElementById("buyModal");
    if (old && !old.hasAttribute("data-gff")) old.remove();
    buildBuyModal();
    var modal = document.getElementById("buyModal");
    modal.setAttribute("data-gff", "1");
    var form = document.getElementById("buyForm");
    var current = "personalizado";

    function open(plan) {
        current = PLANES[plan] ? plan : "personalizado";
        var p = PLANES[current];
        document.getElementById("buyTitle").textContent = p.nombre + " · " + p.precio;
        document.getElementById("buyWa").href = waLink(p.wa);
        var err = document.getElementById("buyError");
        err.classList.remove("show");
        document.getElementById("buySubmit").disabled = false;
        modal.classList.add("open");
        setTimeout(function () { document.getElementById("buyEmail").focus(); }, 50);
    }
    function close() { modal.classList.remove("open"); }

    buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
            var plan = btn.getAttribute("data-buy");
            // Páginas viejas usan data-buy="bajar" / "recomposicion": son el plan personalizado.
            if (plan !== "acompanamiento") plan = "personalizado";
            open(plan);
        });
    });
    document.getElementById("buyClose").addEventListener("click", close);
    modal.addEventListener("click", function (e) { if (e.target === modal) close(); });

    form.addEventListener("submit", async function (ev) {
        ev.preventDefault();
        var err = document.getElementById("buyError");
        var btn = document.getElementById("buySubmit");
        err.classList.remove("show");
        var email = document.getElementById("buyEmail").value.trim();
        btn.disabled = true;
        try {
            var res = await fetch("/api/checkout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email, plan: current }),
            });
            var data = await res.json().catch(function () { return {}; });
            if (res.ok && data.url) {
                window.location.href = data.url;
                return;
            }
            err.innerHTML = (data.error || "No se pudo abrir el pago.")
                + ' <a href="' + waLink(PLANES[current].wa + ". Mi correo: " + email) + '" target="_blank" rel="noopener noreferrer">Abrir WhatsApp</a>';
            err.classList.add("show");
        } catch (e) {
            err.textContent = "Sin conexión con el servidor.";
            err.classList.add("show");
        }
        btn.disabled = false;
    });
}

// ---------- Calculadora de /herramientas (pide registro) ----------
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

    if (typeof window.gffNeedReg === "function" && window.gffNeedReg()) {
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
        ? "Con este IMC, bajar de peso suele ser el foco. Los dos planes de 3 meses se adaptan a esa meta."
        : "Si quieres ganar músculo o verte más firme, los dos planes de 3 meses se adaptan: cambia la comida y la rutina.";
    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

var calcForm = document.getElementById("calcForm");
if (calcForm) {
    calcForm.addEventListener("submit", runCalculator);
    document.addEventListener("gff-reg-ok", function () {
        if (document.getElementById("calcSex").value) calcForm.requestSubmit();
    });
}

// ---------- Calculadoras libres del inicio (IMC y calorías) ----------
function bindHomeImc() {
    var f = document.getElementById("imcForm");
    if (!f) return;
    f.addEventListener("submit", function (ev) {
        ev.preventDefault();
        var out = document.getElementById("imcOut");
        var h = Number(document.getElementById("imcHeight").value);
        var w = Number(document.getElementById("imcWeight").value);
        if (h > 0 && h < 3) h = h * 100;
        if (!(h >= 120 && h <= 230) || !(w >= 30 && w <= 250)) {
            out.innerHTML = '<p class="error show">Revisa los datos: altura entre 120 y 230 cm, peso entre 30 y 250 kg.</p>';
            return;
        }
        var imc = w / Math.pow(h / 100, 2);
        var cat = imcClass(imc);
        var min = 18.5 * Math.pow(h / 100, 2), max = 24.9 * Math.pow(h / 100, 2);
        out.innerHTML = '<div class="calc-big">' + (Math.round(imc * 10) / 10).toFixed(1)
            + ' <span class="calc-badge ' + cat.cls + '">' + cat.label + "</span></div>"
            + '<p class="muted">Rango de peso saludable para tu altura: <b>' + Math.round(min) + "–" + Math.round(max) + " kg</b>.</p>";
    });
}

function bindHomeKcal() {
    var f = document.getElementById("kcalForm");
    if (!f) return;
    f.addEventListener("submit", function (ev) {
        ev.preventDefault();
        var out = document.getElementById("kcalOut");
        var sex = document.getElementById("kcalSex").value;
        var age = Number(document.getElementById("kcalAge").value);
        var h = Number(document.getElementById("kcalHeight").value);
        var w = Number(document.getElementById("kcalWeight").value);
        var act = Number(document.getElementById("kcalActivity").value);
        if (h > 0 && h < 3) h = h * 100;
        if (!sex || !(age >= 15 && age <= 80) || !(h >= 120 && h <= 230) || !(w >= 30 && w <= 250) || !act) {
            out.innerHTML = '<p class="error show">Completa todo: edad 15–80, altura 120–230 cm, peso 30–250 kg.</p>';
            return;
        }
        var tmb = (10 * w) + (6.25 * h) - (5 * age) + (sex === "m" ? 5 : -161);
        var get = tmb * act;
        out.innerHTML = '<div class="calc-rows">'
            + "<div><span>En reposo</span><b>" + Math.round(tmb) + " kcal</b></div>"
            + "<div><span>Para mantener</span><b>" + Math.round(get) + " kcal</b></div>"
            + "<div><span>Para bajar de peso</span><b>" + Math.round(get - 500) + "–" + Math.round(get - 300) + " kcal</b></div>"
            + "<div><span>Para ganar músculo</span><b>" + Math.round(get + 300) + "–" + Math.round(get + 500) + " kcal</b></div>"
            + "</div>"
            + '<p class="note">Son estimaciones (fórmula de Mifflin-St Jeor). Tu plan ajusta estos números a ti.</p>';
    });
}

wireBuy();
bindHomeImc();
bindHomeKcal();
