"use strict";

(function () {
    var token = localStorage.getItem("gff_alumno_session") || "";
    if (!token) {
        location.href = "/alumno";
        return;
    }
    fetch("/api/alumno/state", { headers: { Authorization: "Bearer " + token } })
        .then(function (res) {
            if (res.status === 401) {
                location.href = "/alumno";
                return null;
            }
            return fetch("/ejercicios-videos.json", { cache: "no-store" });
        })
        .then(function (res) {
            if (!res) return null;
            return res.json();
        })
        .then(function (data) {
            if (!data) return;
            var box = document.getElementById("exGrid");
            var items = data.videos || [];
            box.innerHTML = items.map(function (v) {
                var name = String(v.name || "").replace(/[<>]/g, "");
                var group = String(v.group || "").replace(/[<>]/g, "");
                var id = String(v.youtube || "").replace(/[^a-zA-Z0-9_-]/g, "");
                var media = id
                    ? '<iframe src="https://www.youtube.com/embed/' + id + '" title="' + name + '" allowfullscreen></iframe>'
                    : '<div class="soon">Video próximamente</div>';
                return (
                    '<article class="card ex-card"><p class="muted">' + group + "</p><h2>" + name + "</h2>" + media + "</article>"
                );
            }).join("");
        })
        .catch(function () {
            location.href = "/alumno";
        });
})();
