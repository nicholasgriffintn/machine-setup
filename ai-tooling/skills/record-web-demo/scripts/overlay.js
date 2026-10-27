(() => {
  if (window.top !== window || window.__demo) return;

  const STORE = "__demoOverlayState";
  const state = (() => {
    try {
      return JSON.parse(sessionStorage.getItem(STORE)) || {};
    } catch {
      return {};
    }
  })();
  const save = () => {
    try {
      sessionStorage.setItem(STORE, JSON.stringify(state));
    } catch {}
  };

  const css = `
    html { scrollbar-width: none; }
    ::-webkit-scrollbar { display: none; }
    #__demo-root { position: fixed; inset: 0; pointer-events: none; z-index: 2147483647; }
    #__demo-root * { box-sizing: border-box; }
    .__demo-cursor { position: absolute; left: 0; top: 0; width: 28px; height: 28px; transform-origin: 3px 2px;
      transition: transform 120ms ease-out; filter: drop-shadow(0 2px 3px rgba(0,0,0,.35)); }
    .__demo-cursor.pressed svg { transform: scale(.86); }
    .__demo-cursor svg { transition: transform 90ms ease-out; transform-origin: 3px 2px; }
    .__demo-highlight { position: absolute; border: 3px solid #f59e0b; border-radius: 10px; opacity: 0;
      box-shadow: 0 0 0 6px rgba(245,158,11,.22); transition: opacity 160ms ease-out; }
    .__demo-ripple { position: absolute; width: 18px; height: 18px; margin: -9px 0 0 -9px; border-radius: 50%;
      border: 3px solid #f59e0b; animation: __demo-ripple 650ms ease-out forwards; }
    @keyframes __demo-ripple { from { transform: scale(.4); opacity: 1; } to { transform: scale(3.2); opacity: 0; } }
  `;
  const cursorSvg = `<svg width="28" height="28" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 2 L3 22 L8.5 16.8 L12.2 25 L15.8 23.4 L12.2 15.4 L19.5 15.4 Z" fill="#111827" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>`;

  let root, cursor, highlight, tracked, frame;

  const mount = () => {
    if (root?.isConnected) return true;
    const host = document.documentElement;
    if (!host) return false;
    root = document.createElement("div");
    root.id = "__demo-root";
    const style = document.createElement("style");
    style.textContent = css;
    cursor = document.createElement("div");
    cursor.className = "__demo-cursor";
    cursor.innerHTML = cursorSvg;
    highlight = document.createElement("div");
    highlight.className = "__demo-highlight";
    root.append(style, highlight, cursor);
    host.append(root);
    moveCursor(state.x ?? -40, state.y ?? -40, false);
    return true;
  };

  const moveCursor = (x, y, persist = true) => {
    if (!mount()) return;
    cursor.style.transform = `translate(${x - 3}px, ${y - 2}px)`;
    if (persist) {
      state.x = x;
      state.y = y;
      save();
    }
  };

  const ripple = (x, y) => {
    if (!mount()) return;
    const dot = document.createElement("div");
    dot.className = "__demo-ripple";
    dot.style.left = `${x}px`;
    dot.style.top = `${y}px`;
    root.append(dot);
    setTimeout(() => dot.remove(), 700);
  };

  const paintHighlight = () => {
    frame = null;
    if (!tracked || !mount()) return;
    if (!tracked.isConnected) return clearHighlight();
    const rect = tracked.getBoundingClientRect();
    const onScreen = rect.bottom > 0 && rect.right > 0 && rect.top < innerHeight && rect.left < innerWidth;
    const pad = 6;
    highlight.style.left = `${rect.left - pad}px`;
    highlight.style.top = `${rect.top - pad}px`;
    highlight.style.width = `${rect.width + pad * 2}px`;
    highlight.style.height = `${rect.height + pad * 2}px`;
    highlight.style.opacity = onScreen && rect.width > 0 ? "1" : "0";
    frame = requestAnimationFrame(paintHighlight);
  };

  const track = (element) => {
    tracked = element;
    if (!frame) frame = requestAnimationFrame(paintHighlight);
  };

  const clearHighlight = () => {
    tracked = null;
    if (frame) cancelAnimationFrame(frame);
    frame = null;
    if (highlight) highlight.style.opacity = "0";
  };

  const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  const scrollWindow = (targetY, duration) =>
    new Promise((resolve) => {
      const scroller = document.scrollingElement || document.documentElement;
      const maxY = scroller.scrollHeight - innerHeight;
      const startY = scrollY;
      const endY = Math.max(0, Math.min(targetY, maxY));
      const distance = endY - startY;
      if (Math.abs(distance) < 2) return resolve();
      const time = duration ?? Math.min(2400, Math.max(600, Math.abs(distance) * 0.9));
      const start = performance.now();
      const step = (now) => {
        const progress = Math.min(1, (now - start) / time);
        scrollTo({ top: startY + distance * easeInOut(progress), behavior: "instant" });
        if (progress < 1) requestAnimationFrame(step);
        else resolve();
      };
      requestAnimationFrame(step);
    });

  const scrollToElement = async (element, duration) => {
    const rect = element.getBoundingClientRect();
    const fullyVisible = rect.top >= 0 && rect.bottom <= innerHeight;
    if (!fullyVisible) {
      const centre = scrollY + rect.top + rect.height / 2 - innerHeight / 2;
      await scrollWindow(centre, duration);
    }
    const after = element.getBoundingClientRect();
    if (after.top < 0 || after.bottom > innerHeight) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
      await new Promise((resolve) => setTimeout(resolve, 700));
    }
  };

  addEventListener("mousemove", (event) => moveCursor(event.clientX, event.clientY), true);
  addEventListener("mousedown", (event) => {
    ripple(event.clientX, event.clientY);
    cursor?.classList.add("pressed");
  }, true);
  addEventListener("mouseup", () => cursor?.classList.remove("pressed"), true);
  document.addEventListener("DOMContentLoaded", mount);
  mount();

  window.__demo = {
    track,
    clearHighlight,
    scrollToElement,
    scrollToEdge: (edge) => scrollWindow(edge === "top" ? 0 : Number.MAX_SAFE_INTEGER),
    cursorPosition: () => ({ x: state.x ?? null, y: state.y ?? null }),
  };
})();
