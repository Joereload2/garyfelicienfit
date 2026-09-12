"use strict";

const state = {
    step: 1,
    totalSteps: 7,
    token: "",
    email: "",
    user: {},
};

function getToken() {
    const parts = window.location.pathname.split("/usar/");
    return parts.length > 1 ? decodeURIComponent(parts[1]).replace(/\/+$/, "") : "";
}

function cleanText(value, maxLength) {
    maxLength = maxLength || 100;
    if (typeof value !== "string") {
        return "";
    }
    return value.replace(/[<>]/g, "").trim().slice(0, maxLength);
}

function getValue(id) {
    const element = document.getElementById(id);
    if (!element) {
        return "";
    }
    return cleanText(element.value);
}

function getRadio(name) {
    const selected = document.querySelector('input[name="' + name + '"]:checked');
    return selected ? cleanText(selected.value) : "";
}

function getChecked(name) {
    return Array.from(
        document.querySelectorAll('input[name="' + name + '"]:checked')
    ).map(function (input) {
        return cleanText(input.value);
    });
}

function showError(message) {
    const box = document.getElementById("errorBox");
    box.textContent = message;
    box.classList.add("show");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function clearError() {
    const box = document.getElementById("errorBox");
    box.textContent = "";
    box.classList.remove("show");
}

function showGate(title, text) {
    document.getElementById("wizard").classList.add("hidden");
    document.getElementById("gate").classList.remove("hidden");
    document.getElementById("gateTitle").textContent = title;
    document.getElementById("gateText").textContent = text;
}

function bmiValue(weight, height) {
    const meters = height / 100;
    if (meters <= 0) {
        return 0;
    }
    return weight / (meters * meters);
}

function maxChange(weight, goal) {
    if (goal === "lose") {
        return Math.min(weight * 0.09, 10.8);
    }
    if (goal === "gain") {
        return Math.min(weight * 0.06, 6);
    }
    return Math.min(weight * 0.04, 4);
}

function validateStep(step) {
    clearError();

    if (step === 1) {
        const name = getValue("name");
        const age = Number(getValue("age"));
        const weight = Number(getValue("weight"));
        const height = Number(getValue("height"));
        const sex = getValue("sex");

        if (!name) {
            showError("Introduce tu nombre.");
            return false;
        }
        if (!Number.isInteger(age) || age < 18 || age > 70) {
            showError("La edad debe estar entre 18 y 70 años.");
            return false;
        }
        if (!Number.isFinite(weight) || weight < 40 || weight > 180) {
            showError("El peso debe estar entre 40 y 180 kg.");
            return false;
        }
        if (!Number.isFinite(height) || height < 140 || height > 210) {
            showError("La altura debe estar entre 140 y 210 cm.");
            return false;
        }
        if (!["male", "female"].includes(sex)) {
            showError("Selecciona tu sexo.");
            return false;
        }
        const bmi = bmiValue(weight, height);
        if (bmi < 17 || bmi > 65) {
            showError("El IMC debe estar entre 17 y 65.");
            return false;
        }

        state.user.name = name;
        state.user.age = age;
        state.user.weight = weight;
        state.user.height = height;
        state.user.sex = sex;
        return true;
    }

    if (step === 2) {
        const goal = getRadio("goal");
        if (!["lose", "gain", "recomp", "vitality"].includes(goal)) {
            showError("Selecciona un objetivo.");
            return false;
        }
        state.user.goal = goal;
        return true;
    }

    if (step === 3) {
        const target = Number(getValue("targetWeight"));
        if (!Number.isFinite(target) || target < 40 || target > 180) {
            showError("El peso objetivo debe estar entre 40 y 180 kg.");
            return false;
        }
        const goal = state.user.goal;
        const weight = state.user.weight;
        const limit = maxChange(weight, goal);
        if (goal === "lose") {
            if (target >= weight) {
                showError("Para bajar de peso, la meta debe ser menor que tu peso actual.");
                return false;
            }
            if (weight - target > limit) {
                showError("Esa meta en 12 semanas es demasiado agresiva. Elige un objetivo más cercano.");
                return false;
            }
        } else if (goal === "gain") {
            if (target <= weight) {
                showError("Para ganar masa, la meta debe ser mayor que tu peso actual.");
                return false;
            }
            if (target - weight > limit) {
                showError("Esa meta en 12 semanas es demasiado agresiva. Elige un objetivo más cercano.");
                return false;
            }
        } else if (Math.abs(target - weight) > limit) {
            showError("En recomposición, la meta de peso debe ser moderada a 12 semanas.");
            return false;
        }
        state.user.targetWeight = target;
        state.user.motivation = getValue("motivation");
        return true;
    }

    if (step === 4) {
        const days = getRadio("days");
        const location = getRadio("location");
        const duration = getValue("duration");
        const experience = getValue("experience");
        if (!days) {
            showError("Selecciona cuántos días puedes entrenar.");
            return false;
        }
        if (!location) {
            showError("Selecciona dónde quieres entrenar.");
            return false;
        }
        if (!duration) {
            showError("Selecciona la duración de tus sesiones.");
            return false;
        }
        if (!experience) {
            showError("Selecciona tu nivel de experiencia.");
            return false;
        }
        state.user.days = Number(days);
        state.user.location = location;
        state.user.duration = duration;
        state.user.experience = experience;
        return true;
    }

    if (step === 5) {
        const focus = getRadio("focusMuscle");
        if (!focus) {
            showError("Indica si quieres enfocarte en algún músculo.");
            return false;
        }
        state.user.focusMuscle = focus;
        return true;
    }

    if (step === 6) {
        const vegetables = getChecked("vegetable");
        const fruits = getChecked("fruit");
        const proteins = getChecked("protein");
        const carbs = getChecked("carb");
        if (vegetables.length < 3) {
            showError("Debes seleccionar al menos 3 vegetales.");
            return false;
        }
        if (fruits.length < 3) {
            showError("Debes seleccionar al menos 3 frutas.");
            return false;
        }
        if (proteins.length < 1) {
            showError("Debes seleccionar al menos 1 proteína.");
            return false;
        }
        if (carbs.length < 1) {
            showError("Debes seleccionar al menos 1 carbohidrato.");
            return false;
        }
        state.user.vegetables = vegetables;
        state.user.fruits = fruits;
        state.user.proteins = proteins;
        state.user.carbs = carbs;
        return true;
    }

    return true;
}

function updateProgress() {
    const percentage = Math.min(state.step, 7) / 7 * 100;
    document.getElementById("progressBar").style.width = percentage + "%";
}

function showStep(step) {
    document.querySelectorAll(".step").forEach(function (section) {
        section.classList.remove("active");
    });
    const target = document.querySelector('.step[data-step="' + step + '"]');
    if (target) {
        target.classList.add("active");
    }
    state.step = step;
    updateProgress();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function nextStep() {
    if (!validateStep(state.step)) {
        return;
    }
    if (state.step === 6) {
        createSummary();
    }
    showStep(state.step + 1);
}

function prevStep() {
    if (state.step > 1) {
        showStep(state.step - 1);
    }
}

function updateCounters() {
    document.getElementById("vegetableCount").textContent = document.querySelectorAll(
        'input[name="vegetable"]:checked'
    ).length;
    document.getElementById("fruitCount").textContent = document.querySelectorAll(
        'input[name="fruit"]:checked'
    ).length;
}

function safeDisplay(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function createSummary() {
    const u = state.user;
    const goalNames = {
        lose: "Bajar de peso",
        gain: "Ganar masa muscular",
        recomp: "Recomposición corporal",
        vitality: "Recuperar vitalidad y calidad de vida",
    };
    const focusNames = {
        balanced: "Trabajo equilibrado",
        chest: "Pecho",
        back: "Espalda",
        legs: "Piernas",
        shoulders: "Hombros",
        arms: "Brazos",
        glutes: "Glúteos",
    };
    const locationNames = { gym: "Gimnasio", home: "Casa" };
    document.getElementById("summary").innerHTML =
        '<div class="summary-row"><strong>Email</strong><span>' +
        safeDisplay(state.email) +
        "</span></div>" +
        '<div class="summary-row"><strong>Nombre</strong><span>' +
        safeDisplay(u.name) +
        "</span></div>" +
        '<div class="summary-row"><strong>Edad</strong><span>' +
        u.age +
        "</span></div>" +
        '<div class="summary-row"><strong>Peso</strong><span>' +
        u.weight +
        " kg</span></div>" +
        '<div class="summary-row"><strong>Altura</strong><span>' +
        u.height +
        " cm</span></div>" +
        '<div class="summary-row"><strong>Objetivo</strong><span>' +
        goalNames[u.goal] +
        "</span></div>" +
        '<div class="summary-row"><strong>Meta</strong><span>' +
        u.targetWeight +
        " kg</span></div>" +
        '<div class="summary-row"><strong>Entrenamiento</strong><span>' +
        u.days +
        " días / " +
        locationNames[u.location] +
        "</span></div>" +
        '<div class="summary-row"><strong>Especialización</strong><span>' +
        focusNames[u.focusMuscle] +
        "</span></div>" +
        '<div class="summary-row"><strong>Vegetales</strong><span>' +
        u.vegetables.map(safeDisplay).join(", ") +
        "</span></div>" +
        '<div class="summary-row"><strong>Frutas</strong><span>' +
        u.fruits.map(safeDisplay).join(", ") +
        "</span></div>" +
        '<div class="summary-row"><strong>Proteínas</strong><span>' +
        u.proteins.map(safeDisplay).join(", ") +
        "</span></div>" +
        '<div class="summary-row"><strong>Carbohidratos</strong><span>' +
        u.carbs.map(safeDisplay).join(", ") +
        "</span></div>";
}

async function submitForm() {
    if (!validateStep(6)) {
        showStep(6);
        return;
    }
    clearError();
    const button = document.getElementById("submitBtn");
    button.disabled = true;
    const payload = {
        email: state.email,
        name: state.user.name,
        age: state.user.age,
        weight: state.user.weight,
        height: state.user.height,
        sex: state.user.sex,
        goal: state.user.goal,
        targetWeight: state.user.targetWeight,
        motivation: state.user.motivation,
        days: state.user.days,
        location: state.user.location,
        duration: state.user.duration,
        experience: state.user.experience,
        focusMuscle: state.user.focusMuscle,
        vegetables: state.user.vegetables,
        fruits: state.user.fruits,
        proteins: state.user.proteins,
        carbs: state.user.carbs,
    };
    try {
        const res = await fetch("/api/submit/" + encodeURIComponent(state.token), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json().catch(function () {
            return {};
        });
        if (res.status === 409) {
            showGate(
                "Este enlace ya se usó",
                data.error || "El plan no se vuelve a generar. Contacta a soporte."
            );
            return;
        }
        if (!res.ok || !data.ok) {
            showError(data.error || "No se pudieron enviar los datos.");
            button.disabled = false;
            return;
        }
        document.getElementById("resultEmail").textContent = state.email;
        showStep(8);
    } catch (err) {
        showError("No se pudo conectar con el servidor.");
        button.disabled = false;
    }
}

async function init() {
    updateCounters();
    updateProgress();
    state.token = getToken();
    if (!state.token) {
        showGate("Enlace no válido", "Este acceso no existe. Si pagaste, escribe a soporte.");
        return;
    }
    try {
        const res = await fetch("/api/access/" + encodeURIComponent(state.token));
        const data = await res.json().catch(function () {
            return {};
        });
        if (res.status === 409 || data.status === "used") {
            showGate(
                "Este enlace ya se usó",
                data.error || "Si hay un error, contacta a soporte. El enlace no se reabre."
            );
            return;
        }
        if (!res.ok || !data.ok) {
            showGate("Enlace no válido", data.error || "Este acceso no existe.");
            return;
        }
        state.email = data.email;
        document.getElementById("email").value = data.email;
        document.getElementById("gate").classList.add("hidden");
        document.getElementById("wizard").classList.remove("hidden");
        var modelo = new URLSearchParams(location.search).get("modelo") || "";
        if (modelo === "bajar") {
            var lose = document.getElementById("lose");
            if (lose) lose.checked = true;
        }
        if (modelo === "vitalidad") {
            var vit = document.getElementById("vitality");
            if (vit) vit.checked = true;
        }
    } catch (err) {
        showGate("Sin conexión", "No se pudo comprobar el enlace. Recarga la página.");
    }
}

document.addEventListener("change", function (event) {
    if (event.target.matches('input[type="checkbox"]')) {
        updateCounters();
    }
});

document.addEventListener("DOMContentLoaded", init);
