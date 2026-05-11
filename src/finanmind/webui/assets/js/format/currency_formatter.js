export class CurrencyFormatter {
  /** Mirrors ``CurrencyPresenter.format_cop`` from the Python UI. */
  static formatCop(amount) {
    const pesos = Math.round(Number(amount) || 0);
    const body = CurrencyFormatter._dotGroup(Math.abs(pesos));
    const signed = pesos < 0 ? `-${body}` : body;
    return `$ ${signed}`;
  }

  static _dotGroup(value) {
    let text = String(value);
    const blocks = [];
    while (text.length > 0) {
      blocks.unshift(text.slice(-3));
      text = text.slice(0, -3);
    }
    return blocks.join(".");
  }
}
