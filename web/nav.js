"use strict";

(function () {
    var nav = document.querySelector("nav.tabs");
    if (!nav) return;

    var path = (location.pathname.replace(/\/$/, "") || "/");
    var hash = location.hash || "";
    var toolsOn = path === "/herramientas" || path === "/ejercicios";

    nav.querySelectorAll(":scope > a").forEach(function (a) {
        var href = a.getAttribute("href") || "";
        var on = false;
        if (href === "/") {
            on = path === "/" && (!hash || hash === "#plan" || hash === "#guia" || hash === "#top");
        } else if (href.indexOf("/#") === 0) {
            on = path === "/" && hash === "#" + href.split("#")[1];
        } else {
            var p = href.split("#")[0].replace(/\/$/, "") || "/";
            on = path === p;
        }
        a.classList.toggle("active", on);
    });

    var drop = nav.querySelector(".nav-drop");
    if (!drop) return;
    var summary = drop.querySelector("summary");
    if (summary) summary.classList.toggle("active", toolsOn);

    nav.querySelectorAll(".nav-drop-menu a").forEach(function (a) {
        var href = a.getAttribute("href") || "";
        var p = href.split("#")[0].replace(/\/$/, "") || "/";
        var h = href.indexOf("#") >= 0 ? "#" + href.split("#")[1] : "";
        var on = path === p && (!h || hash === h || (p === "/herramientas" && !hash && h === "#calculadora"));
        if (path === "/ejercicios" && p === "/ejercicios") on = true;
        a.classList.toggle("active", on);
    });

    document.addEventListener("click", function (e) {
        if (!drop.contains(e.target)) drop.removeAttribute("open");
    });
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") drop.removeAttribute("open");
    });
})();
