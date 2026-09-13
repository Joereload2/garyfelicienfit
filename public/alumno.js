"use strict";

const KEY = "gff_alumno_session";
let state = { metrics: [], days: {}, lifts: [], name: "", email: "" };
let dashDays = 7;

function todayISO() {
    const d = new Date();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + m + "-" + day;
}
function fmtDate(iso) {
    if (!iso || String(iso).length < 10) return iso || "";
    var p = String(iso).slice(0, 10).split("-");
    return p[2] + "-" + p[1] + "-" + p[0].slice(2);
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
    const n = dashDays > 0 ? dashDays : 7;
    return { start: addDays(end, -(n - 1)), end: end };
}

function rangeLabel() {
    if (dashDays === 15) return "Quincenal (15 días)";
    if (dashDays === 30) return "Mensual (30 días)";
    return "Semanal (7 días)";
}

function rawVal(day, key) {
    const row = state.days[day];
    if (!row || row[key] === undefined || row[key] === null || row[key] === "") return null;
    return Number(row[key]);
}
function val(day, key) {
    const v = rawVal(day, key);
    return v === null ? 0 : v;
}

function renderDash() {
    const { start, end } = weekRange();
    const days = [];
    let cursor = start;
    while (cursor <= end) {
        days.push(cursor);
        cursor = addDays(cursor, 1);
    }
    const enabled = state.metrics.filter(function (m) { return m.enabled; });
    const items = enabled.map(function (m) {
        const logged = days.filter(function (d) { return rawVal(d, m.key) !== null; });
        if (!logged.length) return { l: m.label, v: "—" };
        if (m.kind === "bool") {
            const c = logged.filter(function (d) { return val(d, m.key) > 0; }).length;
            return { l: m.label, v: c + "/" + logged.length + " días" };
        }
        const sum = logged.reduce(function (s, d) { return s + val(d, m.key); }, 0);
        const avg = sum / logged.length;
        const unit = m.unit ? " " + m.unit : "";
        const shown = m.key === "pasos" || avg >= 20
            ? Math.round(avg).toLocaleString("es")
            : avg.toFixed(1);
        return { l: m.label + " (media · " + logged.length + " d)", v: shown + unit };
    });
    const liftN = (state.lifts || []).length;
    items.push({ l: "Ejercicios anotados", v: String(liftN) });
    document.getElementById("dash").innerHTML = items.map(function (it) {
        return '<div class="stat"><b>' + it.v + "</b><span>" + it.l + "</span></div>";
    }).join("");
    const label = document.getElementById("dashLabel");
    if (label) label.textContent = rangeLabel() + " · " + fmtDate(start) + " → " + fmtDate(end);

    const barDays = days.filter(function (d) {
        return state.days[d] && Object.keys(state.days[d]).length;
    });
    document.getElementById("weekBars").innerHTML = (barDays.length ? barDays : days).map(function (d) {
        const done = val(d, "entreno") > 0;
        const fill = done ? 100 : 12;
        return (
            '<div class="bar-row"><span>' + fmtDate(d) + "</span>" +
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
            if (x.minutes != null && x.minutes !== "") bits.push(x.minutes + " min");
            if (x.load != null) bits.push(x.load + " kg");
            if (x.sets || x.reps) bits.push((x.sets || "—") + " × " + (x.reps || "—"));
            bits.push("sem. " + x.week);
            return (
                '<div class="lift"><span>' + bits.join(" · ") + "</span>" +
                '<button type="button" data-del="' + x.id + '">Quitar</button></div>'
            );
        }).join("")
        : '<p class="muted">Aún no hay cargas este día.</p>';
    fillExerciseSelect();
}

function fillExerciseSelect() {
    const sel = document.getElementById("liftEx");
    if (!sel) return;
    const prev = sel.value;
    const catalog = state.exercises || {};
    const strength = catalog.strength || [];
    const cardio = catalog.cardio || [];
    const known = strength.concat(cardio);
    const mine = [];
    (state.lifts || []).forEach(function (x) {
        if (x.exercise && known.indexOf(x.exercise) < 0 && mine.indexOf(x.exercise) < 0) {
            mine.push(x.exercise);
        }
    });
    let html = '<option value="">Elige un ejercicio</option>';
    if (mine.length) {
        html += '<optgroup label="Tus ejercicios">';
        mine.sort().forEach(function (n) {
            html += '<option value="' + n.replace(/"/g, "") + '">' + n + "</option>";
        });
        html += "</optgroup>";
    }
    html += '<optgroup label="Fuerza">';
    strength.forEach(function (n) {
        html += '<option value="' + n.replace(/"/g, "") + '">' + n + "</option>";
    });
    html += "</optgroup>";
    html += '<optgroup label="Cardio">';
    cardio.forEach(function (n) {
        html += '<option value="' + n.replace(/"/g, "") + '">' + n + "</option>";
    });
    html += "</optgroup>";
    html += '<option value="__custom__">Otro (escribir)…</option>';
    sel.innerHTML = html;
    if (prev && Array.from(sel.options).some(function (o) { return o.value === prev; })) {
        sel.value = prev;
    }
    toggleCustomExercise();
}

function isCardioName(name) {
    const cardio = (state.exercises && state.exercises.cardio) || [];
    return cardio.indexOf(name) >= 0;
}

function toggleCustomExercise() {
    const custom = document.getElementById("liftExCustom");
    const sel = document.getElementById("liftEx").value;
    const isCustom = sel === "__custom__";
    custom.classList.toggle("hidden", !isCustom);
    if (isCustom) custom.focus();
    const name = isCustom ? custom.value.trim() : sel;
    const showTime = isCardioName(name) || isCustom;
    const showLoad = !isCardioName(name);
    document.getElementById("liftCardioFields").classList.toggle("hidden", !showTime);
    document.getElementById("liftStrengthFields").classList.toggle("hidden", !showLoad);
    document.getElementById("liftSetsWrap").classList.toggle("hidden", !showLoad);
    document.getElementById("liftRepsWrap").classList.toggle("hidden", !showLoad);
}

function chosenExercise() {
    const sel = document.getElementById("liftEx").value;
    if (sel === "__custom__") {
        return document.getElementById("liftExCustom").value.trim();
    }
    return sel;
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
    renderGuide();
    renderWeightLog();
}

function lastMetric(key) {
    const days = Object.keys(state.days || {}).sort();
    for (let i = days.length - 1; i >= 0; i--) {
        const v = val(days[i], key);
        if (v) return { day: days[i], v: v };
    }
    return null;
}

function fmt(n, unit) {
    if (n === undefined || n === null || n === "") return "—";
    return n + (unit ? " " + unit : "");
}

function renderGuide() {
    const g = state.guide || {};
    const pesoNow = lastMetric("peso");
    const kcalNow = lastMetric("kcal");
    const protNow = lastMetric("proteina");
    const carbNow = lastMetric("carbos");
    const fatNow = lastMetric("grasa");
    const rows = [
        ["Objetivo", g.objetivo || "—", ""],
        ["Peso de partida", fmt(g.peso, "kg"), pesoNow ? fmt(pesoNow.v, "kg") + " · " + fmtDate(pesoNow.day) : "—"],
        ["Peso meta", fmt(g.peso_meta, "kg"), ""],
        ["Kcal / día", fmt(g.kcal, "kcal"), kcalNow ? fmt(Math.round(kcalNow.v), "kcal") : "—"],
        ["Proteína", fmt(g.proteina, "g"), protNow ? fmt(Math.round(protNow.v), "g") : "—"],
        ["Carbos", fmt(g.carbos, "g"), carbNow ? fmt(Math.round(carbNow.v), "g") : "—"],
        ["Grasa", fmt(g.grasa, "g"), fatNow ? fmt(Math.round(fatNow.v), "g") : "—"]
    ];
    if (g.dias) rows.push(["Días de entreno", String(g.dias), ""]);
    if (g.lugar) rows.push(["Lugar", g.lugar, ""]);
    document.getElementById("guideTable").innerHTML =
        "<thead><tr><th></th><th>Meta del plan</th><th>Último registro</th></tr></thead><tbody>" +
        rows.map(function (r) {
            return "<tr><td>" + r[0] + "</td><td>" + r[1] + "</td><td>" + (r[2] || "—") + "</td></tr>";
        }).join("") + "</tbody>";
    if (g.kcal) {
        document.getElementById("gObj").value = g.objetivo || "";
        document.getElementById("gPeso").value = g.peso || "";
        document.getElementById("gMeta").value = g.peso_meta || "";
        document.getElementById("gKcal").value = g.kcal || "";
        document.getElementById("gProt").value = g.proteina || "";
        document.getElementById("gCarb").value = g.carbos || "";
        document.getElementById("gFat").value = g.grasa || "";
    }
    document.getElementById("guideNote").textContent = g.from_plan
        ? "Estas metas salen de tu plan personalizado. El último registro es lo que marcaste en los días."
        : "Si aún no armaste el plan, escribe aquí las metas. El peso diario se compara en la tercera columna.";
}

function renderWeightLog() {
    const days = Object.keys(state.days || {}).sort().reverse();
    const rows = [];
    days.forEach(function (d) {
        const v = val(d, "peso");
        if (v) rows.push({ d: d, v: v });
    });
    const box = document.getElementById("weightLog");
    if (!rows.length) {
        box.innerHTML = '<p class="muted">Todavía no hay pesos. Guárdalo en el día (hábito Peso).</p>';
        return;
    }
    box.innerHTML = rows.slice(0, 12).map(function (r) {
        return "<div><span>" + fmtDate(r.d) + "</span><b>" + r.v + " kg</b></div>";
    }).join("");
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
document.getElementById("liftEx").addEventListener("change", toggleCustomExercise);
document.getElementById("liftExCustom").addEventListener("input", toggleCustomExercise);

document.getElementById("openDash").addEventListener("click", function () {
    document.getElementById("dashView").classList.remove("hidden");
    document.getElementById("dayView").classList.add("hidden");
    document.getElementById("openDash").classList.add("hidden");
    loadState();
});
function backToRecords() {
    document.getElementById("dashView").classList.add("hidden");
    document.getElementById("dayView").classList.remove("hidden");
    document.getElementById("openDash").classList.remove("hidden");
}
document.getElementById("closeDash").addEventListener("click", backToRecords);
document.getElementById("closeDash2").addEventListener("click", backToRecords);

document.getElementById("saveGuide").addEventListener("click", async function () {
    const { res, data } = await api("POST", "/api/alumno/guide", {
        objetivo: document.getElementById("gObj").value,
        peso: document.getElementById("gPeso").value,
        peso_meta: document.getElementById("gMeta").value,
        kcal: document.getElementById("gKcal").value,
        proteina: document.getElementById("gProt").value,
        carbos: document.getElementById("gCarb").value,
        grasa: document.getElementById("gFat").value
    });
    document.getElementById("guideSaveMsg").textContent = res.ok ? "Guía guardada." : (data.error || "Error");
    if (res.ok) loadState();
});
document.getElementById("dashRange").addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-range]");
    if (!btn) return;
    dashDays = Number(btn.getAttribute("data-range")) || 7;
    document.querySelectorAll("#dashRange [data-range]").forEach(function (b) {
        const on = b === btn;
        b.classList.toggle("btn-gold", on);
        b.classList.toggle("btn-ghost", !on);
    });
    loadState();
});

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
        if (key === "peso") step = 0.1;
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
        exercise: chosenExercise(),
        load: document.getElementById("liftLoad").value,
        sets: document.getElementById("liftSets").value,
        reps: document.getElementById("liftReps").value,
        minutes: document.getElementById("liftMin").value
    });
    if (!res.ok) {
        document.getElementById("saveMsg").textContent = data.error || "No se pudo sumar.";
        return;
    }
    document.getElementById("liftEx").value = "";
    document.getElementById("liftExCustom").value = "";
    document.getElementById("liftExCustom").classList.add("hidden");
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
