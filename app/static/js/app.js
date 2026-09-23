document.addEventListener("submit", function (e) {
  const form = e.target;
  if (form.dataset.confirm) {
    if (!window.confirm(form.dataset.confirm)) {
      e.preventDefault();
    }
  }
});

// Auto-dismiss flash messages after a few seconds
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".flash").forEach(function (el) {
    setTimeout(function () {
      el.style.transition = "opacity .4s";
      el.style.opacity = "0";
      setTimeout(function () { el.remove(); }, 400);
    }, 5000);
  });
});
