"use strict";

const PRICE = 40;
const SHOPIFY_PLAN_URL = "https://garyfelicien.myshopify.com/products/plan-personalizado-de-12-semanas";

const MODELS = {
    bajar: {
        title: "Bajar de peso · USD $40",
        lead: "Vas a pagar el plan personalizado con enfoque en bajar de peso. Shopify abre Mercado Pago (Chile)."
    },
    vitalidad: {
        title: "Recuperar vitalidad · USD $40",
        lead: "Vas a pagar el plan personalizado con enfoque en energía y calidad de vida. Shopify abre Mercado Pago (Chile)."
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
    const known = ["plan", "calculadora", "coach", "videos", "coaching"];
    showTab(known.indexOf(id) >= 0 ? id : "plan");
}

function shopifyUrl(modelo) {
    const url = new URL(SHOPIFY_PLAN_URL);
    if (modelo) url.searchParams.set("modelo", modelo);
    return url.toString();
}

function openBuy(modelo) {
    const info = MODELS[modelo] || MODELS.bajar;
    document.getElementById("buyTitle").textContent = info.title;
    document.getElementById("buyLead").textContent = info.lead;
    document.getElementById("buySubmit").setAttribute("href", shopifyUrl(modelo));
    document.getElementById("buyModal").classList.add("open");
}

function closeModal() {
    document.getElementById("buyModal").classList.remove("open");
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
        ? "Con este IMC, el modelo Bajar de peso suele encajar mejor. Vitalidad sigue siendo una opción si tu prioridad es energía y hábitos."
        : "Si tu prioridad es energía y sentirte mejor, el modelo Recuperar vitalidad encaja bien. Si quieres bajar kilos, elige Bajar de peso.";
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
document.getElementById("closeBuy").addEventListener("click", closeModal);
document.getElementById("buyModal").addEventListener("click", function (e) {
    if (e.target.id === "buyModal") closeModal();
});
document.getElementById("coachForm").addEventListener("submit", sendCoaching);
document.getElementById("calcForm").addEventListener("submit", runCalculator);

tabFromHash();
loadVideos();
