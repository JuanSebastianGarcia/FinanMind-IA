export class DomBuilder {
  /** Small helpers to build DOM nodes without templating libraries. */
  static el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  static button(className, text, onClick) {
    const btn = DomBuilder.el("button", className, text);
    btn.type = "button";
    if (onClick) btn.addEventListener("click", onClick);
    return btn;
  }

  static append(parent, ...children) {
    for (const child of children) {
      if (child) parent.appendChild(child);
    }
    return parent;
  }
}
