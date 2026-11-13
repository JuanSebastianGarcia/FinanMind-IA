/**
 * Re-requests any <link rel="stylesheet"> that failed to load.
 *
 * PyWebView serves the UI from a small local HTTP server; at startup a request
 * occasionally fails and the page renders without part of its CSS. Module
 * scripts run only after the preceding stylesheets settle, so by the time this
 * runs a failed link has ``sheet === null`` and can be retried with a fresh URL.
 */
const MAX_ATTEMPTS = 3;
const RETRY_DELAY_MS = 150;

export class StylesheetGuard {
  static repairFailed() {
    for (const link of document.querySelectorAll('link[rel="stylesheet"]')) {
      if (!link.sheet) StylesheetGuard._retry(link, 1);
    }
  }

  static _retry(link, attempt) {
    const base = link.getAttribute("href").split("?")[0];
    const clone = link.cloneNode();
    clone.setAttribute("href", `${base}?retry=${attempt}-${Date.now()}`);
    clone.addEventListener("load", () => link.remove(), { once: true });
    clone.addEventListener(
      "error",
      () => {
        console.warn(`[stylesheet] no se pudo cargar ${base} (intento ${attempt})`);
        if (attempt >= MAX_ATTEMPTS) return;
        clone.remove();
        setTimeout(() => StylesheetGuard._retry(link, attempt + 1), RETRY_DELAY_MS * attempt);
      },
      { once: true },
    );
    link.after(clone);
  }
}
