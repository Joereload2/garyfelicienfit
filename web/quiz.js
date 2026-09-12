"use strict";

(function () {
    var LABELS = {
        sexo: { m: "Hombre", f: "Mujer" },
        modelo: { bajar: "Bajar de peso", vitalidad: "Recuperar vitalidad" },
        lugar: { gym: "Gimnasio", casa: "Casa" },
        traba: {
            motivacion: "Me cuesta la motivación",
            habitos: "No sostengo los hábitos",
            comida: "La comida se me va de las manos",
            tiempo: "No tengo tiempo",
            lesiones: "Arrastro molestias o lesiones"
        }
    };

    var ALL_STEPS = [
        {
            key: "sexo",
            q: "¿Cuál es tu sexo?",
            options: [
                { v: "m", t: "Hombre" },
                { v: "f", t: "Mujer" }
            ]
        },
        {
            key: "modelo",
            q: "¿Qué quieres trabajar estas 12 semanas?",
            options: [
                { v: "bajar", t: "Bajar de peso", d: "Verme y sentirme más ligero, con un déficit realista." },
                { v: "vitalidad", t: "Recuperar vitalidad", d: "Más energía, hábitos y calidad de vida. El peso no es la única brújula." }
            ]
        },
        {
            key: "lugar",
            q: "¿Dónde prefieres entrenar?",
            options: [
                { v: "gym", t: "Gimnasio" },
                { v: "casa", t: "En casa" }
            ]
        },
        {
            key: "traba",
            q: "¿Cuál es tu principal obstáculo hoy?",
            options: [
                { v: "motivacion", t: "Motivación", d: "Empiezo y se me apaga." },
                { v: "habitos", t: "Hábitos", d: "Sé qué hacer, no lo sostengo." },
                { v: "comida", t: "Comida", d: "Como desordenado o por impulso." },
                { v: "tiempo", t: "Tiempo", d: "El día no me da." },
                { v: "lesiones", t: "Molestias", d: "Rodillas, espalda u otra limitación." }
            ]
        }
    ];

    var preset = (new URLSearchParams(location.search).get("modelo") || "").toLowerCase();
    if (preset !== "bajar" && preset !== "vitalidad") preset = "";

    var steps = ALL_STEPS.filter(function (s) {
        return !(s.key === "modelo" && preset);
    });
    var answers = preset ? { modelo: preset } : {};
    var index = 0;

    var stepBox = document.getElementById("quizStep");
    var resultBox = document.getElementById("quizResult");
    var bar = document.getElementById("quizBar");
    var stepN = document.getElementById("quizStepN");

    function renderProgress() {
        var total = steps.length;
        var done = resultBox.hidden ? index : total;
        if (bar) bar.style.width = Math.round((done / total) * 100) + "%";
        if (stepN) {
            stepN.textContent = resultBox.hidden
                ? "Pregunta " + (index + 1) + " de " + total
                : "Listo";
        }
    }

    function renderStep() {
        resultBox.hidden = true;
        stepBox.hidden = false;
        var step = steps[index];
        var html = "<h2>" + step.q + "</h2><div class=\"quiz-opts\">";
        step.options.forEach(function (opt) {
            html += '<button type="button" class="quiz-opt" data-v="' + opt.v + '">';
            html += "<strong>" + opt.t + "</strong>";
            if (opt.d) html += "<span>" + opt.d + "</span>";
            html += "</button>";
        });
        html += "</div>";
        if (index > 0) {
            html += '<button type="button" class="btn btn-ghost quiz-back" id="quizBack">Atrás</button>';
        }
        stepBox.innerHTML = html;
        stepBox.querySelectorAll(".quiz-opt").forEach(function (btn) {
            btn.addEventListener("click", function () {
                answers[step.key] = btn.getAttribute("data-v");
                if (index < steps.length - 1) {
                    index += 1;
                    renderStep();
                } else {
                    renderResult();
                }
            });
        });
        var back = document.getElementById("quizBack");
        if (back) {
            back.addEventListener("click", function () {
                index -= 1;
                renderStep();
            });
        }
        renderProgress();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function recapLine(key) {
        var map = LABELS[key] || {};
        return map[answers[key]] || answers[key];
    }

    function renderResult() {
        var modelo = answers.modelo === "vitalidad" ? "vitalidad" : "bajar";
        var sexo = recapLine("sexo");
        var lugar = recapLine("lugar");
        var traba = recapLine("traba");
        var isBajar = modelo === "bajar";

        document.getElementById("quizRecTitle").textContent = isBajar
            ? "Te recomendamos: Bajar de peso"
            : "Te recomendamos: Recuperar vitalidad";

        var lead = "Marcas " + sexo.toLowerCase() + ", entrenar en " + lugar.toLowerCase();
        lead += " y que tu traba es: " + traba.toLowerCase() + ". ";
        lead += isBajar
            ? "El modelo de bajar de peso encaja: menús a tu medida y un déficit realista a 12 semanas."
            : "El modelo de vitalidad encaja: energía, hábitos y un entreno que puedas sostener.";
        document.getElementById("quizRecLead").textContent = lead;

        var recap = document.getElementById("quizRecap");
        recap.innerHTML =
            "<li>Sexo: " + sexo + "</li>" +
            "<li>Enfoque: " + recapLine("modelo") + "</li>" +
            "<li>Entreno: " + lugar + "</li>" +
            "<li>Obstáculo: " + traba + "</li>";

        var qs = new URLSearchParams({
            sexo: answers.sexo || "",
            lugar: answers.lugar || "",
            traba: answers.traba || "",
            modelo: modelo,
            from: "quiz"
        });
        document.getElementById("quizCta").setAttribute("href", "/" + modelo + "?" + qs.toString());

        stepBox.hidden = true;
        resultBox.hidden = false;
        renderProgress();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    document.getElementById("quizRestart").addEventListener("click", function () {
        answers = preset ? { modelo: preset } : {};
        index = 0;
        renderStep();
    });

    renderStep();
})();
