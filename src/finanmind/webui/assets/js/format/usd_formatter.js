export class UsdFormatter {
  /** Mirrors ``UsdAmountPresenter.format_usd``: 2 decimals, comma thousands. */
  static formatUsd(amount) {
    const value = Number(amount) || 0;
    return `USD ${UsdFormatter._groupAndTrim(value)}`;
  }

  static _groupAndTrim(value) {
    const fixed = Math.abs(value).toFixed(2);
    const [intPart, fracPart] = fixed.split(".");
    const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    const sign = value < 0 ? "-" : "";
    return `${sign}${grouped}.${fracPart}`;
  }
}
