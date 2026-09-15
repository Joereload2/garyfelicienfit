"use strict";

var TOKEN = localStorage.getItem("gff_admin_session") || "";
if (!TOKEN) location.href = "/ingreso";

function headers() {
    return { Authorization: "Bearer " + TOKEN };
}

function card(item, kind) {
    var pct = item.avg_pct == null ? "sin %" : item.avg_pct + "%";
    var color = item.color || "empty";
    return (
        '<button type="button" class="card user-row" data-id="' + item.id + '">' +
        "<b>" + (item.name || item.email) + "</b>" +
        '<p class="muted" style="margin:6px 0 0">' + item.email + " · " + pct + "</p>" +
        '<span class="comp-pill comp-' + color + '">' + kind + "</span></button>"
    );
}

function renderList(id, rows, kind) {
    var box = document.getElementById(id);
    if (!rows || !rows.length) {
        box.innerHTML = '<p class="muted">Nadie en esta lista.</p>';
        return;
    }
    box.innerHTML = rows.map(function (r) { return card(r, kind); }).join("");
}

function fmtDate(iso) {
    if (!iso || String(iso).length < 10) return iso || "";
    var p = String(iso).slice(0, 10).split("-");
    return p[2] + "-" + p[1] + "-" + p[0].slice(2);
}

async function loadRoster() {
    var res = await fetch("/api/admin/roster", { headers: headers() });
    if (res.status === 401) {
        localStorage.removeItem("gff_admin_session");
        location.href = "/ingreso";
        return;
    }
    var data = await res.json();
    renderList("colEmpty", data.no_fill, "sin registro");
    renderList("colFail", data.failing, "falla el plan");
    renderList("colOk", data.ok, "al día");
}

async function openAlumno(id) {
    var res = await fetch("/api/admin/alumno?id=" + id, { headers: headers() });
    var data = await res.json();
    if (!res.ok) return;
    var det = document.getElementById("detail");
    det.classList.remove("hidden");
    document.getElementById("detailTitle").textContent = (data.name || data.email);
    var pill = document.getElementById("detailPill");
    var c = data.compliance || {};
    pill.className = "comp-pill comp-" + (c.color || "empty");
    pill.textContent = c.kind === "no_fill"
        ? "No rellena el planner"
        : ("Cumplimiento " + (c.avg_pct ?? "—") + "%");
    var days = Object.keys((c.days) || {}).sort();
    document.getElementById("detailBars").innerHTML = days.map(function (d) {
        var sc = c.days[d] || {};
        var fill = sc.pct == null ? 8 : Math.max(8, sc.pct);
        var lab = sc.status === "empty" ? "sin dato" : (sc.pct + "%");
        return '<div class="bar-row"><span>' + fmtDate(d) + '</span><div class="bar-track"><div class="bar-fill c-' +
            (sc.color || "empty") + '" style="width:' + fill + '%"></div></div><span>' + lab + "</span></div>";
    }).join("");
    det.scrollIntoView({ behavior: "smooth" });
}

document.body.addEventListener("click", function (ev) {
    var btn = ev.target.closest("[data-id]");
    if (!btn) return;
    openAlumno(btn.getAttribute("data-id"));
});
document.getElementById("salir").addEventListener("click", function () {
    localStorage.removeItem("gff_admin_session");
    location.href = "/ingreso";
});
loadRoster();
