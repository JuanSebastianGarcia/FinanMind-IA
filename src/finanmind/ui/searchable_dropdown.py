"""Type-to-search dropdown that picks a captioned key from a fixed option list."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme


class SearchableDropdown:
    """Entry-driven dropdown that filters captioned options as the user types."""

    POPUP_HEIGHT = 220
    MIN_POPUP_WIDTH = 240

    def __init__(
        self,
        options: list[tuple[str, str]],
        *,
        placeholder: str = "Escribe para buscar…",
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        self._options: list[tuple[str, str]] = list(options)
        self._placeholder = placeholder
        self._on_change = on_change
        self._selected_key: str | None = self._initial_key()
        self._entry: ctk.CTkEntry | None = None
        self._popup: ctk.CTkToplevel | None = None
        self._popup_holder: ctk.CTkScrollableFrame | None = None
        self._row_buttons: list[ctk.CTkButton] = []
        self._highlight_index: int = -1

    def attach(self, parent: ctk.CTkBaseClass) -> ctk.CTkEntry:
        """Build the entry inside ``parent``, return it for layout by the caller."""
        self._entry = self._build_entry(parent)
        self._sync_initial_caption()
        self._wire_entry_events()
        return self._entry

    def get_selected_key(self) -> str | None:
        """Return the key matching the entry's current caption, or ``None``."""
        return self._key_for_caption(self._current_caption())

    def set_by_key(self, key: str) -> None:
        """Update the entry to the caption matching ``key`` (no-op if missing)."""
        for caption, candidate in self._options:
            if candidate == key:
                self._set_caption(caption)
                self._selected_key = key
                return

    def _initial_key(self) -> str | None:
        return self._options[0][1] if self._options else None

    def _build_entry(self, parent: ctk.CTkBaseClass) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent,
            height=36,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
            placeholder_text=self._placeholder,
        )

    def _sync_initial_caption(self) -> None:
        if not self._options:
            return
        self._set_caption(self._options[0][0])

    def _set_caption(self, caption: str) -> None:
        assert self._entry is not None
        self._entry.delete(0, "end")
        self._entry.insert(0, caption)

    def _current_caption(self) -> str:
        assert self._entry is not None
        return self._entry.get().strip()

    def _wire_entry_events(self) -> None:
        assert self._entry is not None
        self._bind_key_events(self._entry)
        self._bind_focus_events(self._entry)
        self._entry.bind("<Button-1>", self._on_click)
        self._entry.bind("<Destroy>", self._on_destroy)

    def _bind_key_events(self, entry: ctk.CTkEntry) -> None:
        entry.bind("<KeyRelease>", self._on_key_release)
        entry.bind("<Down>", self._on_arrow_down)
        entry.bind("<Up>", self._on_arrow_up)
        entry.bind("<Return>", self._on_return)
        entry.bind("<Escape>", self._on_escape)

    def _bind_focus_events(self, entry: ctk.CTkEntry) -> None:
        entry.bind("<FocusOut>", self._on_focus_out)

    def _on_click(self, _event: object) -> None:
        self._show_popup_with_filter()

    def _on_destroy(self, _event: object) -> None:
        self._close_popup()

    def _on_key_release(self, event: object) -> str | None:
        keysym = getattr(event, "keysym", "")
        if keysym in {"Down", "Up", "Return", "Escape", "Tab"}:
            return None
        self._show_popup_with_filter()
        return None

    def _on_focus_out(self, _event: object) -> None:
        assert self._entry is not None
        self._entry.after(150, self._safe_close_and_validate)

    def _safe_close_and_validate(self) -> None:
        try:
            self._close_and_validate_if_outside()
        except Exception:
            return

    def _close_and_validate_if_outside(self) -> None:
        if self._entry is None:
            return
        focus = self._current_focus_widget()
        if focus is self._entry:
            return
        if self._focus_is_inside_popup(focus):
            return
        self._close_popup()
        self._restore_caption_if_invalid()

    def _current_focus_widget(self) -> ctk.CTkBaseClass | None:
        assert self._entry is not None
        try:
            return self._entry.focus_displayof()
        except Exception:
            return None

    def _focus_is_inside_popup(self, focus: object | None) -> bool:
        if self._popup is None or focus is None:
            return False
        return str(focus).startswith(str(self._popup))

    def _restore_caption_if_invalid(self) -> None:
        if self._key_for_caption(self._current_caption()) is not None:
            return
        self._restore_to_last_valid()

    def _restore_to_last_valid(self) -> None:
        for caption, key in self._options:
            if key == self._selected_key:
                self._set_caption(caption)
                return
        if self._options:
            self._set_caption(self._options[0][0])
            self._selected_key = self._options[0][1]

    def _show_popup_with_filter(self) -> None:
        items = self._filter_options(self._current_caption().lower())
        self._render_popup(items)

    def _filter_options(self, text: str) -> list[tuple[str, str]]:
        if text == "":
            return list(self._options)
        return [pair for pair in self._options if text in pair[0].lower()]

    def _render_popup(self, items: list[tuple[str, str]]) -> None:
        self._ensure_popup()
        self._populate_popup_rows(items)
        self._position_popup()
        self._highlight_index = 0 if items else -1
        self._update_highlight_visual()

    def _ensure_popup(self) -> None:
        if self._popup is not None:
            return
        assert self._entry is not None
        win = ctk.CTkToplevel(self._entry.winfo_toplevel())
        self._configure_popup_window(win)
        holder = self._build_popup_holder(win)
        self._popup = win
        self._popup_holder = holder

    def _configure_popup_window(self, win: ctk.CTkToplevel) -> None:
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(fg_color=BudgetUiTheme.BORDER)

    def _build_popup_holder(self, win: ctk.CTkToplevel) -> ctk.CTkScrollableFrame:
        holder = ctk.CTkScrollableFrame(
            win,
            fg_color=BudgetUiTheme.BG_CARD,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        holder.pack(fill="both", expand=True, padx=1, pady=1)
        return holder

    def _populate_popup_rows(self, items: list[tuple[str, str]]) -> None:
        assert self._popup_holder is not None
        for child in self._popup_holder.winfo_children():
            child.destroy()
        self._row_buttons = []
        if not items:
            self._mount_empty_row()
            return
        for caption, key in items:
            self._mount_option_row(caption, key)

    def _mount_empty_row(self) -> None:
        assert self._popup_holder is not None
        ctk.CTkLabel(
            self._popup_holder,
            text="Sin coincidencias",
            text_color=BudgetUiTheme.TXT_TER,
            anchor="w",
        ).pack(fill="x", padx=8, pady=6)

    def _mount_option_row(self, caption: str, key: str) -> None:
        assert self._popup_holder is not None
        btn = ctk.CTkButton(
            self._popup_holder,
            text=caption,
            anchor="w",
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=BudgetUiTheme.BG_HOVER,
            text_color=BudgetUiTheme.TXT_PRI,
            command=lambda c=caption, k=key: self._select(c, k),
        )
        btn.pack(fill="x", padx=4, pady=1)
        self._row_buttons.append(btn)

    def _position_popup(self) -> None:
        assert self._popup is not None and self._entry is not None
        x = self._entry.winfo_rootx()
        y = self._entry.winfo_rooty() + self._entry.winfo_height()
        width = max(self._entry.winfo_width(), self.MIN_POPUP_WIDTH)
        self._popup.geometry(f"{width}x{self.POPUP_HEIGHT}+{x}+{y}")
        self._popup.deiconify()

    def _select(self, caption: str, key: str) -> None:
        self._set_caption(caption)
        self._selected_key = key
        self._close_popup()
        if self._on_change is not None:
            self._on_change(key)
        assert self._entry is not None
        self._entry.focus_set()

    def _close_popup(self) -> None:
        if self._popup is None:
            return
        try:
            self._popup.destroy()
        finally:
            self._popup = None
            self._popup_holder = None
            self._row_buttons = []
            self._highlight_index = -1

    def _on_arrow_down(self, _event: object) -> str:
        if not self._row_buttons:
            self._show_popup_with_filter()
            return "break"
        self._highlight_index = (self._highlight_index + 1) % len(self._row_buttons)
        self._update_highlight_visual()
        return "break"

    def _on_arrow_up(self, _event: object) -> str:
        if not self._row_buttons:
            return "break"
        self._highlight_index = (self._highlight_index - 1) % len(self._row_buttons)
        self._update_highlight_visual()
        return "break"

    def _update_highlight_visual(self) -> None:
        for idx, btn in enumerate(self._row_buttons):
            tone = BudgetUiTheme.BG_HOVER if idx == self._highlight_index else "transparent"
            btn.configure(fg_color=tone)

    def _on_return(self, _event: object) -> str:
        if self._popup is None:
            return ""
        if self._row_buttons:
            self._invoke_highlighted()
        else:
            self._restore_caption_if_invalid()
            self._close_popup()
        return "break"

    def _invoke_highlighted(self) -> None:
        idx = max(self._highlight_index, 0)
        self._row_buttons[idx].invoke()

    def _on_escape(self, _event: object) -> str:
        self._close_popup()
        return "break"

    def _key_for_caption(self, caption: str) -> str | None:
        for current_caption, key in self._options:
            if current_caption == caption:
                return key
        return None
