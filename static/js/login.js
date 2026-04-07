(() => {
  const modal = document.getElementById("loginModal");
  const backdrop = document.getElementById("loginBackdrop");
  const sidebarLoginLink = document.getElementById("sidebarLoginLink");
  const closeBtn = document.getElementById("closeLoginBtn");
  const loginSaas = document.getElementById("loginSaas");
  const explicitOpeners = ["openLoginBtn", "openLoginBtnHero", "openLoginBtnCta"];

  function openModal() {
    if (!modal) return;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("login-modal-open");
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("login-modal-open");
  }

  function setUserMode() {
    loginSaas?.classList.remove("is-admin");
  }

  function setAdminMode() {
    loginSaas?.classList.add("is-admin");
  }

  function init() {
    explicitOpeners.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("click", (e) => {
        e.preventDefault();
        openModal();
      });
    });

    document.addEventListener("click", (e) => {
      const opener = e.target.closest("[data-open-login]");
      if (opener) {
        e.preventDefault();
        openModal();
      }
    });

    closeBtn?.addEventListener("click", closeModal);
    backdrop?.addEventListener("click", closeModal);

    sidebarLoginLink?.addEventListener("click", (e) => {
      e.preventDefault();
      openModal();
    });

    document.querySelectorAll(".js-login-tab-user").forEach((el) => {
      el.addEventListener("click", () => setUserMode());
    });
    document.querySelectorAll(".js-login-tab-admin").forEach((el) => {
      el.addEventListener("click", () => setAdminMode());
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
