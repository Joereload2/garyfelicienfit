"use strict";

const KEY = "gff_alumno_session";
let state = { metrics: [], days: {}, lifts: [], name: "", email: "" };

function todayISO() {
    const d = new Date();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + m + "-" + day;
}
function addDays(iso, n) {
    const d = new Date(iso + "T12:00:00");
    d.setDate(d.getDate() + n);
    return d.toISOString().slice(0, 10);
}
function token() {
    return localStorage.getItem(KEY) || "";
}
function headers() {
    return {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token()
    };
}
async function api(method, path, body) {
    const opt = { method: method, headers: headers() };
    if (body) opt.body = JSON.stringify(body);
    const res = await fetch(path, opt);
    const data = await res.json().catch(function () { return {}; });
    if (res.status === 401) {
        localStorage.removeItem(KEY);
        showLogin();
    }
    return { res: res, data: data };
}

function showLogin() {
    document.getElementById("loginView").classList.remove("hidden");
    document.getElementById("appView").classList.add("hidden");
    document.getElementById("logoutBtn").classList.add("hidden");
}
function showApp() {
    document.getElementById("loginView").classList.add("hidden");
    document.getElementById("appView").classList.remove("hidden");
    document.getElementById("logoutBtn").classList.remove("hidden");
}

function weekRange() {
    const end = document.getElementById("dayPick").value || todayISO();
    return { start: addDays(end, -6), end: end };
}

function val(day, key) {
    const row = state.days[day] || {};
    if (row[key] === undefined || row[key] === null) return 0;
    return Number(row[key]);
}

function renderDash() {
    const { start, end } = weekRange();
    let days = [];
    for (let i = 0; i < 7; i++) days.push(addDays(start, i));
    days = days.filter(function (d) { return d <= end; });
    const n = days.length || 1;
    const entreno = days.filter(function (d) { return val(d, "entreno") > 0; }).length;
    const avg = function (key) {
        return days.reduce(function (s, d) { return s + val(d, key); }, 0) / n;
    };
    const items = [
        { l: "Entrenos / 7 días", v: entreno + "/" + n },
        { l: "Sueño medio", v: avg("sueno").toFixed(1) + " h" },
        { l: "Agua media", v: avg("agua").toFixed(1) + " vasos" },
        { l: "Pasos medios", v: Math.round(avg("pasos")).toLocaleString("es") }
    ];
    document.getElementById("dash").innerHTML = items.map(function (it) {
        return '<div class="stat"><b>' + it.v + "</b><span>" + it.l + "</span></div>";
    }).join("");

    const active = state.metrics.filter(function (m) { return m.enabled; });
    const maxes = {};
    active.forEach(function (m) {
        maxes[m.key] = Math.max(1, ...days.map(function (d) { return val(d, m.key); }));
    });
    document.getElementById("weekBars").innerHTML = days.map(function (d) {
        const label = d.slice(5);
        const done = val(d, "entreno") > 0;
        const fill = done ? 100 : 15;
        return (
            '<div class="bar-row"><span>' + label + "</span>" +
            '<div class="bar-track"><div class="bar-fill" style="width:' + fill + '%"></div></div>' +
            "<span>" + (done ? "sí" : "—") + "</span></div>"
        );
    }).join("");
}

function renderMetrics() {
    const day = document.getElementById("dayPick").value || todayISO();
    const box = document.getElementById("metrics");
    const enabled = state.metrics.filter(function (m) { return m.enabled; });
    box.innerHTML = enabled.map(function (m) {
        const v = val(day, m.key);
        if (m.kind === "bool") {
            return (
                '<div class="metric"><label>' + m.label + "</label>" +
                '<button type="button" class="toggle' + (v ? " on" : "") + '" data-bool="' + m.key + '"></button></div>'
            );
        }
        const unit = m.unit ? " <small>" + m.unit + "</small>" : "";
        return (
            '<div class="metric"><label>' + m.label + unit + "</label>" +
            '<div class="stepper">' +
            '<button type="button" data-step="' + m.key + '" data-d="-1">−</button>' +
            '<input data-num="' + m.key + '" type="number" step="any" value="' + v + '">' +
            '<button type="button" data-step="' + m.key + '" data-d="1">+</button>' +
            "</div></div>"
        );
    }).join("");

    document.getElementById("chips").innerHTML = state.metrics.map(function (m) {
        return '<button type="button" class="chip' + (m.enabled ? "" : " off") + '" data-chip="' + m.key + '">' + m.label + "</button>";
    }).join("");

    const lifts = (state.lifts || []).filter(function (x) { return x.day === day; });
    document.getElementById("lifts").innerHTML = lifts.length
        ? lifts.map(function (x) {
            const bits = [x.exercise];
            if (x.load != null) bits.push(x.load + " kg");
            if (x.sets || x.reps) bits.push((x.sets || "—") + " × " + (x.reps || "—"));
            bits.push("sem. " + x.week);
            return (
                '<div class="lift"><span>' + bits.join(" · ") + "</span>" +
                '<button type="button" data-del="' + x.id + '">Quitar</button></div>'
            );
        }).join("")
        : '<p class="muted">Aún no hay cargas este día.</p>';
}

function collectValues() {
    const out = {};
    document.querySelectorAll("[data-num]").forEach(function (el) {
        out[el.getAttribute("data-num")] = Number(el.value || 0);
    });
    document.querySelectorAll("[data-bool]").forEach(function (el) {
        out[el.getAttribute("data-bool")] = el.classList.contains("on") ? 1 : 0;
    });
    return out;
}

async function loadState() {
    const { start, end } = weekRange();
    const { res, data } = await api("GET", "/api/alumno/state?start=" + start + "&end=" + end);
    if (!res.ok) return;
    state = data;
    document.getElementById("hello").textContent = "Hola, " + (data.name || data.email);
    renderDash();
    renderMetrics();
}

document.getElementById("loginForm").addEventListener("submit", async function (ev) {
    ev.preventDefault();
    const err = document.getElementById("loginError");
    err.classList.remove("show");
    const { res, data } = await api("POST", "/api/alumno/login", {
        email: document.getElementById("loginEmail").value,
        pin: document.getElementById("loginPin").value
    });
    if (!res.ok) {
        err.textContent = data.error || "No se pudo entrar.";
        err.classList.add("show");
        return;
    }
    localStorage.setItem(KEY, data.session);
    showApp();
    document.getElementById("dayPick").value = todayISO();
    loadState();
});

document.getElementById("logoutBtn").addEventListener("click", function () {
    localStorage.removeItem(KEY);
    showLogin();
});
document.getElementById("dayPick").addEventListener("change", loadState);

document.getElementById("metrics").addEventListener("click", function (ev) {
    const t = ev.target;
    if (t.dataset.bool) t.classList.toggle("on");
    if (t.dataset.step) {
        const key = t.dataset.step;
        const input = document.querySelector('[data-num="' + key + '"]');
        if (!input) return;
        const d = Number(t.dataset.d);
        let step = 1;
        if (key === "pasos") step = 500;
        if (key === "kcal") step = 50;
        if (key === "sueno") step = 0.5;
        input.value = String(Math.max(0, Number(input.value || 0) + d * step));
    }
});

document.getElementById("chips").addEventListener("click", async function (ev) {
    const key = ev.target.dataset.chip;
    if (!key) return;
    const m = state.metrics.find(function (x) { return x.key === key; });
    if (!m) return;
    await api("POST", "/api/alumno/metric-toggle", { key: key, enabled: !m.enabled });
    loadState();
});

document.getElementById("saveDay").addEventListener("click", async function () {
    const day = document.getElementById("dayPick").value || todayISO();
    const { res, data } = await api("POST", "/api/alumno/day", { day: day, values: collectValues() });
    document.getElementById("saveMsg").textContent = res.ok ? "Día guardado." : (data.error || "Error");
    if (res.ok) loadState();
});

document.getElementById("addMetric").addEventListener("click", async function () {
    const label = document.getElementById("newLabel").value;
    const { res, data } = await api("POST", "/api/alumno/metric", {
        label: label,
        kind: document.getElementById("newKind").value,
        unit: document.getElementById("newUnit").value
    });
    if (!res.ok) {
        document.getElementById("saveMsg").textContent = data.error || "No se pudo agregar.";
        return;
    }
    document.getElementById("newLabel").value = "";
    loadState();
});

document.getElementById("addLift").addEventListener("click", async function () {
    const { res, data } = await api("POST", "/api/alumno/lift", {
        day: document.getElementById("dayPick").value || todayISO(),
        week: document.getElementById("liftWeek").value,
        exercise: document.getElementById("liftEx").value,
        load: document.getElementById("liftLoad").value,
        sets: document.getElementById("liftSets").value,
        reps: document.getElementById("liftReps").value
    });
    if (!res.ok) {
        document.getElementById("saveMsg").textContent = data.error || "No se pudo sumar.";
        return;
    }
    document.getElementById("liftEx").value = "";
    loadState();
});

document.getElementById("lifts").addEventListener("click", async function (ev) {
    const id = ev.target.dataset.del;
    if (!id) return;
    await api("POST", "/api/alumno/lift-delete", { id: Number(id) });
    loadState();
});

(function initWeeks() {
    const sel = document.getElementById("liftWeek");
    for (let i = 1; i <= 12; i++) {
        const o = document.createElement("option");
        o.value = String(i);
        o.textContent = "Semana " + i;
        sel.appendChild(o);
    }
    document.getElementById("dayPick").value = todayISO();
    if (token()) {
        showApp();
        loadState();
    } else {
        showLogin();
    }
})();
