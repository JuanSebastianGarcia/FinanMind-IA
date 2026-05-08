"""Configure OpenAI vs Mistral credentials and model ids for budget review."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.mistral_api_key_store import MistralApiKeyStore
from finanmind.services.mistral_api_settings import MistralApiSettings
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_api_key_store import OpenAiApiKeyStore
from finanmind.services.openai_api_settings import OpenAiApiSettings
from finanmind.services.openai_model_store import OpenAiModelStore
from finanmind.ui.budget_ui_theme import BudgetUiTheme


class LlmSettingsDialog:
    """Lets the user pick vendor, paste API keys, and tune model names."""

    LABEL_OPENAI = "ChatGPT (OpenAI, API de pago)"
    LABEL_MISTRAL = "Mistral (plan Experiment gratis, sin tarjeta)"

    def __init__(self, master: ctk.Misc) -> None:
        self._master = master
        self._win: ctk.CTkToplevel | None = None
        self._provider_menu: ctk.CTkOptionMenu | None = None
        self._key_entry: ctk.CTkEntry | None = None
        self._model_entry: ctk.CTkEntry | None = None
        self._examples_lbl: ctk.CTkLabel | None = None
        self._saved = False

    def show(self) -> bool:
        """Block until closing; ``True`` when the user pressed Guardar."""
        self._open_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._saved

    def _open_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Configurar revisión IA")
        win.geometry("580x490")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._layout_body(win)

    def _layout_body(self, win: ctk.CTkToplevel) -> None:
        frame = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        self._mount_intro(frame)
        self._mount_provider_row(frame)
        self._mount_key_field(frame)
        self._mount_model_field(frame)
        self._mount_examples(frame)
        self._mount_buttons(frame)
        self._sync_fields_from_menu_initial()

    def _mount_intro(self, frame: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            frame,
            text="Proveedor de IA",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w")
        text = (
            "Mistral ofrece un plan Experiment con uso gratuito (límites de tasa); "
            "la API key se crea sin tarjeta. OpenAI cobra por uso en la mayoría "
            "de cuentas. Las credenciales se guardan junto a tus CSV; usa variables "
            "de entorno para no guardarlas en disco."
        )
        ctk.CTkLabel(
            frame,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=520,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(8, 12))

    def _mount_provider_row(self, frame: ctk.CTkFrame) -> None:
        self._mount_label(frame, "Usar proveedor", bold=True)
        values = [self.LABEL_OPENAI, self.LABEL_MISTRAL]
        menu = ctk.CTkOptionMenu(
            frame,
            values=values,
            command=lambda _choice: self._sync_fields_from_menu(),
            **self._option_kw(),
        )
        menu.pack(fill="x", pady=(0, 14))
        self._provider_menu = menu

    def _mount_key_field(self, frame: ctk.CTkFrame) -> None:
        self._mount_label(frame, "API Key", bold=True)
        entry = self._styled_entry(frame, show_dots=True)
        entry.pack(fill="x", pady=(0, 14))
        self._key_entry = entry

    def _mount_model_field(self, frame: ctk.CTkFrame) -> None:
        self._mount_label(frame, "Identificador del modelo", bold=True)
        entry = self._styled_entry(frame, show_dots=False)
        entry.pack(fill="x", pady=(0, 4))
        self._model_entry = entry

    def _styled_entry(self, frame: ctk.CTkFrame, *, show_dots: bool) -> ctk.CTkEntry:
        show = "•" if show_dots else ""
        return ctk.CTkEntry(
            frame,
            height=36,
            show=show,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )

    def _mount_examples(self, frame: ctk.CTkFrame) -> None:
        self._examples_lbl = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
            anchor="w",
        )
        self._examples_lbl.pack(anchor="w", pady=(0, 14))

    def _option_kw(self) -> dict:
        return {
            "fg_color": BudgetUiTheme.BG_MAIN,
            "button_color": BudgetUiTheme.BORDER,
            "button_hover_color": BudgetUiTheme.TXT_TER,
            "dropdown_fg_color": BudgetUiTheme.BG_CARD,
            "dropdown_text_color": BudgetUiTheme.TXT_PRI,
            "text_color": BudgetUiTheme.TXT_PRI,
            "height": 36,
        }

    def _mount_label(self, frame: ctk.CTkFrame, text: str, *, bold: bool) -> None:
        weight = "bold" if bold else "normal"
        ctk.CTkLabel(
            frame,
            text=text,
            font=ctk.CTkFont(size=12, weight=weight),
            text_color=BudgetUiTheme.TXT_SEC,
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

    def _mount_buttons(self, frame: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")
        self._outline_btn(row, "Cancelar", self._cancel).pack(side="right")
        self._accent_btn(row, "Guardar", self._confirm).pack(side="right", padx=(0, 10))

    def _accent_btn(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=120,
            height=32,
            command=cmd,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )

    def _outline_btn(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=120,
            height=32,
            command=cmd,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )

    def _sync_fields_from_menu_initial(self) -> None:
        assert self._provider_menu is not None
        saved = BudgetAiProviderStore.resolve()
        self._provider_menu.set(self._menu_label(saved))
        self._apply_provider_state(saved)

    def _sync_fields_from_menu(self) -> None:
        assert self._provider_menu is not None
        label = self._provider_menu.get()
        self._apply_provider_state(self._provider_from_menu_label(label))

    def _menu_label(self, provider: BudgetAiProvider) -> str:
        if provider == BudgetAiProvider.MISTRAL:
            return self.LABEL_MISTRAL
        return self.LABEL_OPENAI

    def _provider_from_menu_label(self, label: str) -> BudgetAiProvider:
        return BudgetAiProvider.MISTRAL if label.strip() == self.LABEL_MISTRAL else BudgetAiProvider.OPENAI

    def _apply_provider_state(self, provider: BudgetAiProvider) -> None:
        assert self._key_entry is not None and self._model_entry is not None and self._examples_lbl is not None
        if provider == BudgetAiProvider.MISTRAL:
            self._paint_mistral_widgets()
            return
        self._paint_openai_widgets()

    def _paint_mistral_widgets(self) -> None:
        assert self._key_entry is not None and self._model_entry is not None and self._examples_lbl is not None
        self._fill_secret_entry(self._key_entry, MistralApiKeyStore.resolve_key())
        resolved = MistralModelStore.resolve_model()
        fallback = MistralApiSettings.DEFAULT_MODEL_ID
        self._replace_model_field(resolved if resolved else fallback)
        hints = ["mistral-small-latest", "mistral-medium-latest"]
        self._examples_lbl.configure(text="Sugerencias (tier gratis): " + " · ".join(hints))

    def _paint_openai_widgets(self) -> None:
        assert self._key_entry is not None and self._model_entry is not None and self._examples_lbl is not None
        self._fill_secret_entry(self._key_entry, OpenAiApiKeyStore.resolve_key())
        resolved = OpenAiModelStore.resolve_model()
        fallback = OpenAiApiSettings.DEFAULT_MODEL_ID
        self._replace_model_field(resolved if resolved else fallback)
        hints = ["gpt-4o-mini", "gpt-5.4-mini"]
        self._examples_lbl.configure(text="Sugerencias: " + " · ".join(hints))

    def _fill_secret_entry(self, entry: ctk.CTkEntry, value: str | None) -> None:
        raw = "" if value is None else value
        entry.configure(state="normal")
        entry.delete(0, "end")
        if raw:
            entry.insert(0, raw)

    def _replace_model_field(self, model: str) -> None:
        assert self._model_entry is not None
        self._model_entry.delete(0, "end")
        self._model_entry.insert(0, model)

    def _confirm(self) -> None:
        assert self._provider_menu is not None
        label = self._provider_menu.get()
        try:
            self._persist_everything(self._provider_from_menu_label(label))
        except (ValueError, RuntimeError) as exc:
            messagebox.showwarning("IA", str(exc))
            return
        self._saved = True
        self._close()

    def _persist_everything(self, provider: BudgetAiProvider) -> None:
        if not BudgetAiProviderStore.env_var_in_use():
            BudgetAiProviderStore.persist(provider)
        self._persist_branch(provider)

    def _persist_branch(self, provider: BudgetAiProvider) -> None:
        if provider == BudgetAiProvider.MISTRAL:
            self._persist_mistral_credentials()
            return
        self._persist_openai_credentials()

    def _persist_openai_credentials(self) -> None:
        assert self._key_entry is not None and self._model_entry is not None
        if not OpenAiApiKeyStore.env_var_in_use():
            OpenAiApiKeyStore.persist_key(self._key_entry.get())
        if not OpenAiModelStore.env_var_in_use():
            OpenAiModelStore.persist_model(self._model_entry.get())

    def _persist_mistral_credentials(self) -> None:
        assert self._key_entry is not None and self._model_entry is not None
        if not MistralApiKeyStore.env_var_in_use():
            MistralApiKeyStore.persist_key(self._key_entry.get())
        if not MistralModelStore.env_var_in_use():
            MistralModelStore.persist_model(self._model_entry.get())

    def _cancel(self) -> None:
        self._saved = False
        self._close()

    def _close(self) -> None:
        if self._win is not None:
            self._win.destroy()
