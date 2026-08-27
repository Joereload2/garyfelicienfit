"use strict";

const PRICE = 40;

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
    const id = (location.hash || "#guia").replace("#", "");
    const known = ["guia", "coach", "videos", "coaching"];
    showTab(known.indexOf(id) >= 0 ? id : "guia");
}

function openModal() {
    document.getElementById("buyModal").classList.add("open");
    document.getElementById("buyError").classList.remove("show");
}

function closeModal() {
    document.getElementById("buyModal").classList.remove("open");
}

async function buyGuide(ev) {
    ev.preventDefault();
    const err = document.getElementById("buyError");
    err.classList.remove("show");
    const email = document.getElementById("buyEmail").value.trim();
    const btn = document.getElementById("buySubmit");
    if (!isLocalApp()) {
        err.textContent =
            "Esta web es la vitrina. El pago lo confirma Gary y te envía el enlace de la guía por correo o WhatsApp.";
        err.classList.add("show");
        return;
    }
    btn.disabled = true;
    try {
        const res = await fetch("/api/checkout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email }),
        });
        const data = await res.json().catch(function () { return {}; });
        if (!res.ok || !data.ok) {
            err.textContent = data.error || "No se pudo iniciar el pago.";
            err.classList.add("show");
            btn.disabled = false;
            return;
        }
        if (data.mode === "stripe" && data.url) {
            window.location.href = data.url;
            return;
        }
        window.location.href = "/gracias?test=1";
    } catch (e) {
        err.textContent = "Sin conexión con el servidor.";
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
            box.innerHTML =
                '<div class="empty">Gary irá subiendo aquí sus videos. ' +
                "Para añadir uno, edita <code>public/videos.json</code> con el ID de YouTube.</div>";
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

document.querySelectorAll(".tabs button").forEach(function (b) {
    b.addEventListener("click", function () {
        showTab(b.getAttribute("data-tab"));
    });
});
window.addEventListener("hashchange", tabFromHash);
document.getElementById("openBuy").addEventListener("click", openModal);
document.getElementById("openBuy2").addEventListener("click", openModal);
document.getElementById("closeBuy").addEventListener("click", closeModal);
document.getElementById("buyForm").addEventListener("submit", buyGuide);
document.getElementById("coachForm").addEventListener("submit", sendCoaching);
document.getElementById("buyModal").addEventListener("click", function (e) {
    if (e.target.id === "buyModal") closeModal();
});

tabFromHash();
loadVideos();
