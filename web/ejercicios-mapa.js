"use strict";

(function () {
    var NAMES = {
        chest: "Pectoral",
        shoulders: "Hombros (deltoides)",
        biceps: "Bíceps",
        triceps: "Tríceps",
        forearms: "Antebrazos",
        abdominal: "Abdominales",
        obliques: "Oblicuos",
        quads: "Cuádriceps",
        hamstrings: "Isquiotibiales",
        glutes: "Glúteos",
        calves: "Gemelos",
        traps: "Trapecios",
        lats: "Espalda (dorsales)",
        lowerback: "Zona lumbar",
    };

    var CATALOG = {
        gym: {
            chest: ["Press banca", "Press inclinado con mancuernas", "Aperturas"],
            shoulders: ["Press militar", "Elevaciones laterales", "Pájaros"],
            biceps: ["Curl de bíceps", "Martillo", "Curl en banco"],
            triceps: ["Extensión de tríceps en polea", "Fondos", "Press francés"],
            forearms: ["Curl de muñeca", "Farmer walk"],
            abdominal: ["Abdominales", "Plancha", "Dead bug"],
            obliques: ["Pallof press", "Plancha lateral", "Rotaciones con cable"],
            quads: ["Sentadilla", "Prensa", "Zancadas"],
            hamstrings: ["Peso muerto rumano", "Curl femoral", "Buenos días"],
            glutes: ["Hip thrust", "Patada de glúteo", "Peso muerto rumano"],
            calves: ["Elevación de gemelos de pie", "Elevación de gemelos sentado"],
            traps: ["Encogimientos", "Face pull", "Remo al mentón"],
            lats: ["Jalón al pecho", "Remo con barra", "Remo unilateral"],
            lowerback: ["Peso muerto", "Hiperextensiones", "Superman"],
        },
        home: {
            chest: ["Flexiones", "Flexiones inclinadas", "Fondos en silla"],
            shoulders: ["Press con botellas", "Elevaciones laterales con botellas", "Pike push-up"],
            biceps: ["Curl con botellas", "Curl martillo"],
            triceps: ["Fondos de tríceps en silla", "Extensiones con botella"],
            forearms: ["Apretar toalla", "Curl de muñeca con botella"],
            abdominal: ["Plancha 20–40 s", "Bicho muerto", "Mountain climber lento"],
            obliques: ["Plancha lateral", "Giros rusos"],
            quads: ["Sentadilla", "Zancadas", "Sentadilla búlgara"],
            hamstrings: ["Puente de glúteos", "Peso muerto con mochila"],
            glutes: ["Puente de glúteos", "Patada de glúteo a cuatro patas", "Sentadilla sumo"],
            calves: ["Elevación de gemelos a una pierna"],
            traps: ["Face pull con banda", "Encogimientos con botellas"],
            lats: ["Remo con mochila", "Superman", "Face pull con banda"],
            lowerback: ["Superman", "Bird dog"],
        },
    };

    var equipment = "gym";
    var selected = "";
    var hovered = "";

    var mapBox = document.getElementById("muscleMap");
    var labelEl = document.getElementById("muscleLabel");
    var listEl = document.getElementById("exList");
    var hintEl = document.getElementById("exHint");

    function labelText() {
        var id = hovered || selected;
        if (!id) return "Toca un músculo en el mapa.";
        return NAMES[id] || id;
    }

    function registered() {
        return typeof window.gffIsReg === "function" ? window.gffIsReg() : true;
    }

    function renderList() {
        labelEl.textContent = labelText();
        if (!selected) {
            hintEl.textContent = "Elige gimnasio o casa y un músculo.";
            listEl.innerHTML = "";
            return;
        }
        var loc = equipment === "home" ? "casa" : "gimnasio";
        var items = (CATALOG[equipment] && CATALOG[equipment][selected]) || [];
        if (!registered()) {
            hintEl.textContent = (NAMES[selected] || selected) + " · " + loc;
            listEl.innerHTML = '<li><button type="button" class="btn btn-gold" data-open-reg>Regístrate para ver la lista</button></li>';
            var ask = listEl.querySelector("[data-open-reg]");
            if (ask) {
                ask.addEventListener("click", function () {
                    if (window.gffNeedReg) window.gffNeedReg();
                });
            }
            return;
        }
        hintEl.textContent = NAMES[selected] + " · " + loc + " · " + items.length + (items.length === 1 ? " ejercicio" : " ejercicios");
        listEl.innerHTML = items
            .map(function (name) {
                return "<li>" + String(name).replace(/[<>]/g, "") + "</li>";
            })
            .join("");
    }

    function setEquipment(next) {
        equipment = next;
        document.querySelectorAll("[data-eq]").forEach(function (btn) {
            btn.classList.toggle("active", btn.getAttribute("data-eq") === next);
        });
        renderList();
    }

    function paintMap() {
        mapBox.querySelectorAll("[data-muscle]").forEach(function (el) {
            var id = el.getAttribute("data-muscle");
            el.classList.toggle("is-on", id === selected);
            el.classList.toggle("is-hover", Boolean(hovered) && id === hovered);
        });
    }

    function setSelected(id) {
        selected = id === selected ? "" : id;
        paintMap();
        renderList();
    }

    document.querySelectorAll("[data-eq]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            setEquipment(btn.getAttribute("data-eq"));
        });
    });

    fetch("/img/muscle-map.svg")
        .then(function (res) {
            if (!res.ok) throw new Error("map");
            return res.text();
        })
        .then(function (svg) {
            mapBox.innerHTML = svg;
            var root = mapBox.querySelector("svg");
            if (!root) return;
            root.querySelectorAll("[data-muscle]").forEach(function (el) {
                el.setAttribute("tabindex", "0");
                el.setAttribute("role", "button");
                el.setAttribute("aria-label", NAMES[el.getAttribute("data-muscle")] || "");
                el.addEventListener("mouseenter", function () {
                    hovered = el.getAttribute("data-muscle");
                    paintMap();
                    labelEl.textContent = labelText();
                });
                el.addEventListener("mouseleave", function () {
                    hovered = "";
                    paintMap();
                    labelEl.textContent = labelText();
                });
                el.addEventListener("click", function () {
                    setSelected(el.getAttribute("data-muscle"));
                });
                el.addEventListener("keydown", function (ev) {
                    if (ev.key === "Enter" || ev.key === " ") {
                        ev.preventDefault();
                        setSelected(el.getAttribute("data-muscle"));
                    }
                });
            });
            renderList();
            document.addEventListener("gff-reg-ok", renderList);
        })
        .catch(function () {
            mapBox.innerHTML = "<p class=\"muted\">No se pudo cargar el mapa.</p>";
        });
})();
