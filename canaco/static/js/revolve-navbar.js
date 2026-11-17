(function () {
  "use strict";

  function initializeNavbar() {
    var toggle = document.querySelector(
      '.canaco-main-header .navbar-toggler[aria-controls="navbar-collapse"]'
    );
    var menu = document.getElementById("navbar-collapse");

    if (!toggle || !menu) return;

    toggle.addEventListener("click", function () {
      var isOpen = menu.classList.toggle("show");
      toggle.setAttribute("aria-expanded", String(isOpen));
      toggle.setAttribute("aria-label", isOpen ? "Cerrar menú" : "Abrir menú");
    });

    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.innerWidth < 992) {
          menu.classList.remove("show");
          toggle.setAttribute("aria-expanded", "false");
          toggle.setAttribute("aria-label", "Abrir menú");
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeNavbar);
  } else {
    initializeNavbar();
  }
})();
