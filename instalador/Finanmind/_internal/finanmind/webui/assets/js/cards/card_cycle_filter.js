import { DomBuilder } from "../core/dom_builder.js";

export class CardCycleFilter {
  /** Cycle dropdown with the resolved (start → end) caption. */
  constructor(state, onChange) {
    this._state = state;
    this._onChange = onChange;
  }

  build() {
    const bar = DomBuilder.el("div", "cycle-filter");
    bar.appendChild(DomBuilder.el("span", "cycle-filter__caption", "Ciclo (corte en mes)"));
    bar.appendChild(this._buildSelect());
    bar.appendChild(this._buildRange());
    return bar;
  }

  _buildSelect() {
    const select = DomBuilder.el("select", "cycle-filter__select");
    const active = this._state.active_cycle;
    for (const cycle of this._state.cycles || []) {
      const opt = DomBuilder.el("option", null, cycle);
      opt.value = cycle;
      if (cycle === active) opt.selected = true;
      select.appendChild(opt);
    }
    select.addEventListener("change", () => this._onChange(select.value));
    return select;
  }

  _buildRange() {
    const range = this._state.cycle_range || {};
    const text = range.start && range.end ? `${range.start}  →  ${range.end}` : "";
    return DomBuilder.el("span", "cycle-filter__range", text);
  }
}
