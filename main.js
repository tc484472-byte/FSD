// ---------- Helpers ----------
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function setYear() {
  const y = new Date().getFullYear();
  const yearEl = $("#year");
  if (yearEl) yearEl.textContent = String(y);
}

// ---------- Theme Toggle (Assignment 9) ----------
function initTheme() {
  const btn = $("#themeToggle");
  if (!btn) return;

  const saved = localStorage.getItem("theme");
  if (saved === "dark" || saved === "light") {
    document.documentElement.setAttribute("data-theme", saved);
    btn.setAttribute("aria-pressed", saved === "dark" ? "true" : "false");
  }

  btn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    btn.setAttribute("aria-pressed", next === "dark" ? "true" : "false");
  });
}

// ---------- Modal (Assignment 6) ----------
function initModal() {
  const backdrop = $("#modalBackdrop");
  const openBtn = $("#openModalBtn");
  const heroCTA = $("#heroCTA");
  const ctaBottom = $("#ctaBottom");
  const closeBtn = $("#closeModalBtn");

  if (!backdrop) return;

  const open = () => { backdrop.hidden = false; };
  const close = () => { backdrop.hidden = true; };

  [openBtn, heroCTA, ctaBottom].forEach((b) => b?.addEventListener("click", open));
  closeBtn?.addEventListener("click", close);

  // Close when clicking outside modal
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close();
  });

  // Optional: close on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !backdrop.hidden) close();
  });

  $("#modalForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    alert("Thanks! We'll send the guide to your email.");
    close();
  });
}

// ---------- FAQ Toggle (Assignment 4) ----------
function initFAQ() {
  const faq = $("#faqList");
  if (!faq) return;

  $$(".faq-q", faq).forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.closest(".faq-item");
      const ans = $(".faq-a", item);

      const isOpen = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!isOpen));
      ans.hidden = isOpen;
    });
  });
}

// ---------- Live Character Counter (Assignment 5) ----------
function initCharCounter() {
  const box = $("#messageBox");
  const counter = $("#charCount");
  if (!box || !counter) return;

  const update = () => {
    const max = Number(box.getAttribute("maxlength")) || 250;
    const len = box.value.length;
    counter.textContent = `${len} / ${max}`;
  };

  box.addEventListener("input", update);
  update();
}

// ---------- Image Grid Filter (Assignment 8) ----------
function initGalleryFilter() {
  const grid = $("#imageGrid");
  if (!grid) return;

  const buttons = $$("[data-filter]");
  const cards = $$(".img-card", grid);

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("is-active"));
      btn.classList.add("is-active");

      const filter = btn.dataset.filter;
      cards.forEach((card) => {
        const cat = card.dataset.category;
        const show = filter === "all" || filter === cat;
        card.style.display = show ? "" : "none";
      });
    });
  });
}

// ---------- Currency Converter (Assignment 7) ----------
// NOTE: exchangerate.host docs mention an access_key requirement. :contentReference[oaicite:0]{index=0}
// We attempt exchangerate.host first (works in many setups), then fallback to open.er-api.com if needed.
async function convertCurrency(amount, from, to) {
  // Try exchangerate.host convert endpoint
  // Docs show: https://api.exchangerate.host/convert?from=EUR&to=GBP&amount=100 :contentReference[oaicite:1]{index=1}
  const url1 = `https://api.exchangerate.host/convert?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&amount=${encodeURIComponent(amount)}`;

  try {
    const r1 = await fetch(url1);
    const d1 = await r1.json();
    if (d1 && (d1.result || d1.result === 0)) return { ok: true, result: d1.result, source: "exchangerate.host" };
  } catch (_) {}

  // Fallback: open.er-api.com (no-key endpoint with base currency list)
  // Example: https://open.er-api.com/v6/latest/USD :contentReference[oaicite:2]{index=2}
  const url2 = `https://open.er-api.com/v6/latest/${encodeURIComponent(from)}`;
  const r2 = await fetch(url2);
  const d2 = await r2.json();

  if (d2?.result === "success" && d2?.rates?.[to]) {
    return { ok: true, result: Number(amount) * Number(d2.rates[to]), source: "open.er-api.com" };
  }
  return { ok: false, error: "Could not fetch rates right now." };
}

function initConverter() {
  const form = $("#converterForm");
  const out = $("#convertResult");
  if (!form || !out) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const amount = Number($("#amount").value || 0);
    const from = $("#fromCurrency").value;
    const to = $("#toCurrency").value;

    out.textContent = "Converting…";

    if (!Number.isFinite(amount) || amount <= 0) {
      out.textContent = "Please enter a valid amount greater than 0.";
      return;
    }

    try {
      const res = await convertCurrency(amount, from, to);
      if (!res.ok) {
        out.textContent = "Sorry — rates are unavailable right now. Please try again.";
        return;
      }
      out.textContent = `${amount} ${from} ≈ ${res.result.toFixed(2)} ${to} (via ${res.source})`;
    } catch {
      out.textContent = "Something went wrong. Please try again.";
    }
  });
}

// ---------- Contact form (optional) ----------
function initContactForm() {
  $("#contactForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    alert("Message sent! (Demo)");
    e.target.reset();
    // reset counter
    const box = $("#messageBox");
    if (box) box.dispatchEvent(new Event("input"));
  });
}

// ---------- Boot ----------
setYear();
initTheme();
initModal();
initFAQ();
initCharCounter();
initGalleryFilter();
initConverter();
initContactForm();

