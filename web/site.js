"use strict";

var OFFER_KEY = "gff_offer_v1";
var offerTick = null;
var offerState = null;

function clpLabel(n) {
    return "$" + Number(n || 0).toLocaleString("es-CL");
}

function clockLabel(s) {
    s = Math.max(0, Math.floor(s || 0));
    var m = Math.floor(s / 60);
    var sec = s % 60;
    return (m < 10 ? "0" : "") + m + ":" + (sec < 10 ? "0" : "") + sec;
}

function readOfferStore() {
    try {
        return JSON.parse(localStorage.getItem(OFFER_KEY) || "null");
    } catch (e) {
        return null;
    }
}

function writeOfferStore(email, token) {
    localStorage.setItem(OFFER_KEY, JSON.stringify({ email: email, token: token }));
}

function paintOffer(state) {
    offerState = state;
    var live = !!(state && state.live && state.remaining_s > 0);
    document.body.classList.toggle("offer-live", live);
    var price = live ? state.sale_clp || state.price_clp : (state && state.list_clp) || 450000;
    document.querySelectorAll("[data-offer-now]").forEach(function (el) {
        el.textContent = clpLabel(price);
    });
    document.querySelectorAll("[data-offer-clock]").forEach(function (el) {
        if (live) {
            el.hidden = false;
            el.textContent = clockLabel(state.remaining_s);
        } else {
            el.hidden = true;
            el.textContent = "";
        }
    });
    var pay = document.getElementById("offerPay");
    var ask = document.getElementById("offerAsk");
    var liveBox = document.getElementById("offerLiveBox");
    var submit = document.getElementById("offerSubmit");
    if (ask) ask.hidden = live;
    if (liveBox) liveBox.hidden = !live;
    if (submit) submit.hidden = live;
    if (pay) {
        pay.hidden = !live;
        pay.textContent = live
            ? "Pagar " + clpLabel(state.sale_clp || state.price_clp)
            : "Pagar";
    }
}

function stopOfferTick() {
    if (offerTick) {
        clearInterval(offerTick);
        offerTick = null;
    }
}

function startOfferTick() {
    stopOfferTick();
    if (!offerState || !offerState.live) return;
    offerTick = setInterval(function () {
        if (!offerState) return;
        offerState.remaining_s = Math.max(0, (offerState.remaining_s || 0) - 1);
        if (offerState.remaining_s <= 0) {
            offerState.live = false;
            offerState.price_clp = offerState.list_clp;
            stopOfferTick();
        }
        paintOffer(offerState);
    }, 1000);
}

async function fetchOfferState(token) {
    var res = await fetch("/api/oferta-estado?token=" + encodeURIComponent(token));
    var data = await res.json().catch(function () { return {}; });
    if (!res.ok || !data.ok) return null;
    return data;
}

function bindOfferForm() {
    if (document.getElementById("offerModal")) {
        wireOfferModal();
        return;
    }
    var html = ""
        + '<div class="modal" id="offerModal">'
        + '<form class="card" id="offerForm">'
        + "<h3>50% por tiempo limitado</h3>"
        + '<p class="muted" id="offerIntro">Déjanos tu correo. Al enviarlo arranca el 50%: $225.000 en vez de $450.000, por tiempo limitado.</p>'
        + '<div id="offerError" class="error"></div>'
        + '<div id="offerOk" class="ok"></div>'
        + '<div id="offerAsk">'
        + '<label for="offerEmail">Correo electrónico</label>'
        + '<input id="offerEmail" type="email" required autocomplete="email" placeholder="tucorreo@email.com">'
        + "</div>"
        + '<div id="offerLiveBox" hidden>'
        + '<p class="offer-clock offer-clock-lg" data-offer-clock></p>'
        + '<p class="muted">Paga ahora a <b data-offer-now>$225.000</b> CLP. Después vuelve a $450.000.</p>'
        + "</div>"
        + '<div class="actions">'
        + '<button type="button" class="btn btn-ghost" id="offerClose">Ahora no</button>'
        + '<button type="submit" class="btn btn-gold" id="offerSubmit">Quiero el 50%</button>'
        + '<button type="button" class="btn btn-gold" id="offerPay" hidden>Pagar</button>'
        + "</div>"
        + '<p class="note">El código llega al correo y no se muestra aquí. Mercado Pago cobra en pesos.</p>'
        + "</form></div>";
    document.body.insertAdjacentHTML("beforeend", html);
    wireOfferModal();
}

function wireOfferModal() {
    var modal = document.getElementById("offerModal");
    var form = document.getElementById("offerForm");
    if (!modal || !form || form.getAttribute("data-bound")) return;
    form.setAttribute("data-bound", "1");
    var stored = readOfferStore();
    if (stored && stored.email) {
        var emailInput = document.getElementById("offerEmail");
        if (emailInput) emailInput.value = stored.email;
    }

    function openOffer() {
        modal.classList.add("open");
        paintOffer(offerState);
        if (offerState && offerState.live) return;
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

    var payBtn = document.getElementById("offerPay");
    if (payBtn) {
        payBtn.addEventListener("click", async function () {
            var err = document.getElementById("offerError");
            if (err) err.classList.remove("show");
            var rec = readOfferStore() || {};
            if (!rec.token || !rec.email) return;
            payBtn.disabled = true;
            try {
                var res = await fetch("/api/checkout-3meses", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email: rec.email, token: rec.token }),
                });
                var data = await res.json().catch(function () { return {}; });
                if (!res.ok || !data.url) {
                    if (err) {
                        err.textContent = data.error || "No se pudo abrir el pago.";
                        err.classList.add("show");
                    }
                    payBtn.disabled = false;
                    return;
                }
                window.location.href = data.url;
            } catch (e) {
                if (err) {
                    err.textContent = "Sin conexión con el servidor.";
                    err.classList.add("show");
                }
                payBtn.disabled = false;
            }
        });
    }

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
                    err.textContent = data.error || "No se pudo activar el 50%.";
                    err.classList.add("show");
                }
                if (btn) btn.disabled = false;
                return;
            }
            writeOfferStore(email, data.token);
            paintOffer(data);
            startOfferTick();
            if (ok) {
                ok.textContent = data.message || "El 50% está activo. El reloj ya corre.";
                ok.classList.add("show");
            }
        } catch (e) {
            if (err) {
                err.textContent = "Sin conexión con el servidor.";
                err.classList.add("show");
            }
            if (btn) btn.disabled = false;
        }
    });

    (async function restoreOffer() {
        var rec = readOfferStore();
        if (!rec || !rec.token) return;
        try {
            var data = await fetchOfferState(rec.token);
            if (!data || !data.live) return;
            paintOffer(data);
            startOfferTick();
        } catch (e) { /* ignore */ }
    })();
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
        ? "Con este IMC, bajar de peso suele ser el foco. El acompañamiento de 3 meses adapta comida y rutina a esa meta; no es otro producto."
        : "Si quieres ganar músculo o verte más firme, el mismo acompañamiento de 3 meses se adapta: cambia la comida y la rutina, no el servicio.";
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
if (document.querySelector("[data-open-offer]")) bindOfferForm();
