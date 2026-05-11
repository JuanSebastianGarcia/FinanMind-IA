import { DomBuilder } from "../core/dom_builder.js";

export class DashboardTitleBar {
  /** Static title strip mirroring the original CustomTkinter "Dashboard financiero". */
  build() {
    const bar = DomBuilder.el("div", "dash__title-bar");
    bar.appendChild(DomBuilder.el("div", "dash__title-bar-text", "Dashboard financiero"));
    return bar;
  }
}
