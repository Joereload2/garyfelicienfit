"use strict";

(function () {
    var path = (location.pathname.replace(/\/$/, "") || "/");
    var hash = location.hash || "";
    document.querySelectorAll("nav.tabs a").forEach(function (a) {
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
})();
