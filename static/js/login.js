(() => {
  const modal = document.getElementById("loginModal");
  const backdrop = document.getElementById("loginBackdrop");
  const openBtn = document.getElementById("openLoginBtn");
  const sidebarLoginLink = document.getElementById("sidebarLoginLink");
  const closeBtn = document.getElementById("closeLoginBtn");
  const tabUser = document.getElementById("tabUser");
  const tabAdmin = document.getElementById("tabAdmin");
  const loginSaas = document.getElementById("loginSaas");

  function openModal() {
    if (!modal) return;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
  }

  function setUserMode() {
    loginSaas?.classList.remove("is-admin");
  }

  function setAdminMode() {
    loginSaas?.classList.add("is-admin");
  }

  openBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    openModal();
  });
  sidebarLoginLink?.addEventListener("click", (e) => {
    e.preventDefault();
    openModal();
  });
  closeBtn?.addEventListener("click", closeModal);
  backdrop?.addEventListener("click", closeModal);

  tabUser?.addEventListener("click", () => setUserMode());
  tabAdmin?.addEventListener("click", () => setAdminMode());

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
})();

