"use strict";

const PRICE = 40;

const MODELS = {
    bajar: {
        title: "Bajar de peso · USD $40",
        lead: "Pagas el plan personalizado con enfoque en bajar de peso. Mercado Pago (Chile, CLP)."
    },
    recomposicion: {
        title: "Recomposición corporal · USD $40",
        lead: "Pagas el plan personalizado con enfoque en bajar grasa y conservar o ganar músculo. Mercado Pago (Chile, CLP)."
    }
};

function isLocalApp() {
    const h = location.hostname;
    return h === "localhost" || h === "127.0.0.1";
}

function showTab(id) {
    document.querySelectorAll(".panel").forEach(function (p) {
        p.classList.toggle("active", p.id === "panel-" + id);
    });
    document.querySelectorAll(".tabs button").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-tab") === id);
    });
    if (id) {
        history.replaceState(null, "", "#" + id);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function tabFromHash() {
    const raw = (location.hash || "#plan").replace("#", "");
    const id = raw === "guia" ? "plan" : raw;
    const known = ["plan", "calculadora", "coach", "videos", "tresmeses", "coaching"];
    showTab(known.indexOf(id) >= 0 ? id : "plan");
}

function openBuy(modelo) {
    const info = MODELS[modelo] || MODELS.bajar;
    const title = document.getElementById("buyTitle");
    const lead = document.getElementById("buyLead");
    const hidden = document.getElementById("buyModelo");
    const err = document.getElementById("buyError");
    if (title) title.textContent = info.title;
    if (lead) lead.textContent = info.lead;
    if (hidden) hidden.value = modelo;
    if (err) err.classList.remove("show");
    document.getElementById("buyModal").classList.add("open");
}

function closeModal() {
    document.getElementById("buyModal").classList.remove("open");
}

async function buyPlan(ev) {
    ev.preventDefault();
    const err = document.getElementById("buyError");
    const emailEl = document.getElementById("buyEmail");
    const modeloEl = document.getElementById("buyModelo");
    const btn = document.getElementById("buySubmit");
    if (!emailEl || !err) return;
    err.classList.remove("show");
    const email = emailEl.value.trim();
    const modelo = (modeloEl && modeloEl.value) || "bajar";
    btn.disabled = true;
    try {
        const res = await fetch("/api/checkout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, modelo: modelo }),
        });
        const data = await res.json().catch(function () { return {}; });
        if (!res.ok || !data.ok) {
            err.textContent = data.error || "No se pudo iniciar el pago.";
            err.classList.add("show");
            btn.disabled = false;
            return;
        }
        if ((data.mode === "mp" || data.mode === "stripe") && data.url) {
            window.location.href = data.url;
            return;
        }
        window.location.href = isLocalApp() ? "/gracias?test=1" : "/gracias.html?test=1";
    } catch (e) {
        err.textContent = "Sin conexión con el servidor de pago.";
        err.classList.add("show");
        btn.disabled = false;
    }
}

async function sendCoaching(ev) {
    if (!isLocalApp()) {
        return;
    }
    ev.preventDefault();
    const err = document.getElementById("coachError");
    const ok = document.getElementById("coachOk");
    err.classList.remove("show");
    ok.classList.remove("show");
    const payload = {
        name: document.getElementById("cName").value,
        email: document.getElementById("cEmail").value,
        phone: document.getElementById("cPhone").value,
        message: document.getElementById("cMsg").value,
    };
    try {
        const res = await fetch("/api/coaching", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json().catch(function () { return {}; });
        if (!res.ok || !data.ok) {
            err.textContent = data.error || "No se pudo enviar.";
            err.classList.add("show");
            return;
        }
        ok.textContent = data.message || "Recibido.";
        ok.classList.add("show");
        ev.target.reset();
    } catch (e) {
        err.textContent = "Sin conexión con el servidor.";
        err.classList.add("show");
    }
}

function bindOfferForm() {
    const form = document.getElementById("offerForm");
    if (!form) return;
    form.addEventListener("submit", async function (ev) {
        ev.preventDefault();
        const err = document.getElementById("offerError");
        const ok = document.getElementById("offerOk");
        if (err) err.classList.remove("show");
        if (ok) ok.classList.remove("show");
        const email = document.getElementById("offerEmail").value.trim();
        const name = (document.getElementById("offerName") || {}).value || "";
        const btn = document.getElementById("offerSubmit");
        if (btn) btn.disabled = true;
        try {
            const res = await fetch("/api/oferta-3meses", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email, name: name }),
            });
            const data = await res.json().catch(function () { return {}; });
            if (!res.ok || !data.ok) {
                if (err) {
                    err.textContent = data.error || "No se pudo aplicar el descuento.";
                    err.classList.add("show");
                }
                if (btn) btn.disabled = false;
                return;
            }
            const list = document.getElementById("offerList");
            const deal = document.getElementById("offerDeal");
            if (list) list.classList.add("hidden");
            if (deal) deal.classList.remove("hidden");
            form.classList.add("hidden");
            const wa = document.getElementById("offerWa");
            if (wa) {
                const msg = encodeURIComponent(
                    "Hola, dejé mi correo (" + email + ") para el 50% off del acompañamiento de 3 meses. Quiero coordinar el pago de $225.000 CLP."
                );
                wa.setAttribute("href", "https://wa.me/56959128603?text=" + msg);
            }
            if (ok) {
                ok.textContent = data.message || "Descuento aplicado.";
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
}

function youtubeThumb(id) {
    return "https://i.ytimg.com/vi/" + id + "/hqdefault.jpg";
}

async function loadVideos() {
    const box = document.getElementById("videoGrid");
    try {
        const res = await fetch("/videos.json", { cache: "no-store" });
        const data = await res.json();
        const videos = data.videos || [];
        if (!videos.length) {
            box.innerHTML = '<div class="empty">Pronto videos de Gary aquí.</div>';
            return;
        }
        box.innerHTML = videos.map(function (v) {
            const id = encodeURIComponent(v.id);
            const title = String(v.title || "Video").replace(/[<>]/g, "");
            return (
                '<article class="video">' +
                '<iframe src="https://www.youtube-nocookie.com/embed/' + id +
                '" title="' + title + '" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>' +
                "<p>" + title + "</p></article>"
            );
        }).join("");
    } catch (e) {
        box.innerHTML = '<div class="empty">No se pudo cargar la lista de videos.</div>';
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
        ? "Con este IMC, el modelo Bajar de peso suele encajar mejor. Recomposición corporal es una opción si quieres bajar grasa y cuidar el músculo a la vez."
        : "Si quieres verte más firme sin perseguir solo la báscula, Recomposición corporal encaja bien. Si tu meta es bajar kilos, elige Bajar de peso.";
    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

document.querySelectorAll(".tabs button").forEach(function (b) {
    b.addEventListener("click", function () {
        showTab(b.getAttribute("data-tab"));
    });
});
window.addEventListener("hashchange", tabFromHash);
document.querySelectorAll("[data-buy]").forEach(function (el) {
    el.addEventListener("click", function () {
        openBuy(el.getAttribute("data-buy"));
    });
});
var closeBuy = document.getElementById("closeBuy");
if (closeBuy) closeBuy.addEventListener("click", closeModal);
var buyModal = document.getElementById("buyModal");
if (buyModal) {
    buyModal.addEventListener("click", function (e) {
        if (e.target.id === "buyModal") closeModal();
    });
}
var buyForm = document.getElementById("buyForm");
if (buyForm) buyForm.addEventListener("submit", buyPlan);
var coachForm = document.getElementById("coachForm");
if (coachForm) coachForm.addEventListener("submit", sendCoaching);
var calcForm = document.getElementById("calcForm");
if (calcForm) calcForm.addEventListener("submit", runCalculator);
bindOfferForm();
var videoGrid = document.getElementById("videoGrid");
if (videoGrid) loadVideos();
if (!document.body.classList.contains("ad-page")) {
    tabFromHash();
} else {
    var current = location.pathname.replace(/\/$/, "") || "/";
    document.querySelectorAll(".tabs a").forEach(function (a) {
        var href = a.getAttribute("href") || "";
        a.classList.toggle("active", href === current);
    });
}

(function showQuizRecap() {
    var bar = document.getElementById("quizRecapBar");
    if (!bar) return;
    var q = new URLSearchParams(location.search);
    if (q.get("from") !== "quiz") return;
    var sexo = q.get("sexo") === "f" ? "mujer" : q.get("sexo") === "m" ? "hombre" : "";
    var lugar = q.get("lugar") === "casa" ? "casa" : q.get("lugar") === "gym" ? "gimnasio" : "";
    var trabas = {
        motivacion: "la motivación",
        habitos: "sostener hábitos",
        comida: "ordenar la comida",
        tiempo: "el tiempo",
        lesiones: "molestias o lesiones"
    };
    var traba = trabas[q.get("traba") || ""] || "";
    if (!sexo || !lugar) return;
    var bits = ["Llegaste desde el cuestionario: " + sexo + ", entreno en " + lugar];
    if (traba) bits.push("tu traba es " + traba);
    bar.innerHTML = "<b>A tu medida.</b> " + bits.join("; ") + ". El plan de 12 semanas se arma con tus datos después del pago.";
    bar.classList.add("show");
})();
