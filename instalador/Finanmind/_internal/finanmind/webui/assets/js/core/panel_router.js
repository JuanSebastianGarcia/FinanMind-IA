export class PanelRouter {
  /** Switches which panel is visible inside the content host and triggers refresh. */
  constructor() {
    this._entries = new Map();
    this._activeKey = null;
  }

  register(key, panel, host) {
    this._entries.set(key, { panel, host, mounted: false });
  }

  has(key) {
    return this._entries.has(key);
  }

  async setActive(key) {
    const entry = this._entries.get(key);
    if (!entry) return;
    const wasMounted = entry.mounted;
    await this._ensureMounted(entry);
    this._applyVisibility(key);
    this._activeKey = key;
    if (wasMounted) await this._refreshIfPossible(entry);
  }

  async _ensureMounted(entry) {
    if (entry.mounted) return;
    await entry.panel.mount();
    entry.mounted = true;
  }

  async _refreshIfPossible(entry) {
    if (typeof entry.panel.refresh === "function") {
      await entry.panel.refresh();
    }
  }

  _applyVisibility(activeKey) {
    for (const [key, entry] of this._entries.entries()) {
      const isActive = key === activeKey;
      entry.host.classList.toggle("panel--active", isActive);
    }
  }
}
