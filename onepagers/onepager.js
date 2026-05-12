document.querySelectorAll("[data-dots]").forEach((el) => {
  const total = Number(el.dataset.total || 0);
  const hi = Number(el.dataset.hi || 0);
  if (!total || el.children.length) return;
  for (let i = 0; i < total; i += 1) {
    const dot = document.createElement("span");
    if (i < hi) dot.className = "hot";
    el.appendChild(dot);
  }
});

document.querySelectorAll(".qbox[data-qr]").forEach((el) => {
  const url = el.dataset.qr;
  const link = document.createElement("a");
  link.href = url;
  link.textContent = "PDF";
  link.className = "qbox";
  link.setAttribute("aria-label", "Open the paper PDF");
  el.replaceWith(link);
});
