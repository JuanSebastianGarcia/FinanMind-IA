"""Budget Review window: form, loading state, results, and apply confirmation."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from finanmind.budget.book_service import BudgetBookService
from finanmind.models.budget_review_request import BudgetReviewRequest
from finanmind.models.budget_review_result import BudgetReviewResult
from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.budget_review_applier import BudgetReviewApplier
from finanmind.services.budget_review_llm_factory import BudgetReviewLlmFactory
from finanmind.services.budget_review_service import (
    BudgetReviewService,
    BudgetReviewServiceError,
)
from finanmind.services.llm_configuration_error import LlmConfigurationError
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_model_store import OpenAiModelStore
from finanmind.ui.budget_review_form_card import BudgetReviewFormCard
from finanmind.ui.budget_review_results_panel import BudgetReviewResultsPanel
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.llm_settings_dialog import LlmSettingsDialog


class BudgetReviewWindow:
    """Orchestrates the full AI review flow inside a single layered panel."""

    def __init__(
        self,
        host: ctk.CTkFrame,
        book: BudgetBookService,
        on_back: Callable[[], None],
        on_budget_changed: Callable[[], None],
    ) -> None:
        self._host = host
        self._book = book
        self._on_back = on_back
        self._on_budget_changed = on_budget_changed
        self._log = logging.getLogger("finanmind.review.ui")
        self._form: BudgetReviewFormCard | None = None
        self._results: BudgetReviewResultsPanel | None = None
        self._status_lbl: ctk.CTkLabel | None = None
        self._provider_menu: ctk.CTkOptionMenu | None = None
        self._current_result: BudgetReviewResult | None = None

    def attach(self) -> None:
        """Build all widgets; the form is shown immediately, results are deferred."""
        outer = self._bootstrap_outer_shell()
        self._mount_screen_body(outer)

    def reset(self) -> None:
        """Clear results and status when this layer is shown again."""
        self._current_result = None
        if self._results is not None:
            self._results.clear()
        self._snap_quick_provider_choice()
        self._set_status_idle()

    def _bootstrap_outer_shell(self) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(self._host, fg_color=BudgetUiTheme.BG_MAIN)
        outer.pack(fill="both", expand=True, padx=20, pady=14)
        return outer

    def _mount_screen_body(self, outer: ctk.CTkFrame) -> None:
        self._render_topbar(outer)
        body = self._open_body_scroll(outer)
        self._render_hint(body)
        self._render_provider_strip(body)
        self._render_status_bar(body)
        self._attach_form_panel(body)
        self._attach_results_panel(body)

    def _open_body_scroll(self, outer: ctk.CTkFrame) -> ctk.CTkScrollableFrame:
        scroll = ctk.CTkScrollableFrame(
            outer,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        scroll.pack(fill="both", expand=True)
        return scroll

    def _idle_status_text(self) -> str:
        vendor = self._vendor_human_name()
        model = self._active_model_slug()
        return f"Proveedor: {vendor} · Modelo: {model}"

    def _vendor_human_name(self) -> str:
        resolved = BudgetAiProviderStore.resolve()
        if resolved == BudgetAiProvider.MISTRAL:
            return "Mistral"
        return "OpenAI"

    def _active_model_slug(self) -> str:
        if BudgetAiProviderStore.resolve() == BudgetAiProvider.MISTRAL:
            return MistralModelStore.resolve_model()
        return OpenAiModelStore.resolve_model()

    def _set_status_idle(self) -> None:
        self._set_status(self._idle_status_text(), BudgetUiTheme.TXT_TER)

    def _render_provider_strip(self, outer: ctk.CTkFrame) -> None:
        strip = ctk.CTkFrame(outer, fg_color="transparent")
        strip.pack(fill="x", pady=(0, 6))
        self._label_provider_heading(strip)
        self._build_provider_dropdown(strip)
        self._snap_quick_provider_choice()
        self._maybe_disable_provider_menu()

    def _maybe_disable_provider_menu(self) -> None:
        if self._provider_menu is None:
            return
        if BudgetAiProviderStore.env_var_in_use():
            self._provider_menu.configure(state="disabled")

    def _label_provider_heading(self, strip: ctk.CTkFrame) -> None:
        caption = "Proveedor (mismo proceso, distinta IA)"
        ctk.CTkLabel(
            strip,
            text=caption,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
            anchor="w",
        ).pack(side="left", padx=(0, 14))

    def _build_provider_dropdown(self, strip: ctk.CTkFrame) -> None:
        menu = ctk.CTkOptionMenu(
            strip,
            values=[LlmSettingsDialog.LABEL_OPENAI, LlmSettingsDialog.LABEL_MISTRAL],
            command=self._handle_quick_vendor_switch,
            **self._vendor_menu_kw(),
        )
        menu.pack(side="left")
        self._provider_menu = menu

    def _vendor_menu_kw(self) -> dict:
        return {
            "fg_color": BudgetUiTheme.BG_MAIN,
            "button_color": BudgetUiTheme.BORDER,
            "button_hover_color": BudgetUiTheme.TXT_TER,
            "dropdown_fg_color": BudgetUiTheme.BG_CARD,
            "dropdown_text_color": BudgetUiTheme.TXT_PRI,
            "text_color": BudgetUiTheme.TXT_PRI,
            "height": 32,
            "width": 320,
        }

    def _snap_quick_provider_choice(self) -> None:
        assert self._provider_menu is not None
        label = self._menu_label_from_enum(BudgetAiProviderStore.resolve())
        self._provider_menu.set(label)

    def _menu_label_from_enum(self, prov: BudgetAiProvider) -> str:
        if prov == BudgetAiProvider.MISTRAL:
            return LlmSettingsDialog.LABEL_MISTRAL
        return LlmSettingsDialog.LABEL_OPENAI

    def _handle_quick_vendor_switch(self, label: str) -> None:
        if BudgetAiProviderStore.env_var_in_use():
            self._toast_provider_env_lock()
            self._snap_quick_provider_choice()
            return
        BudgetAiProviderStore.persist(self._enum_from_quick_label(label))
        self._set_status_idle()

    def _toast_provider_env_lock(self) -> None:
        messagebox.showinfo(
            "Proveedor fijado por entorno",
            "Define otro FINANMIND_AI_PROVIDER o borra esa variable.",
        )

    def _enum_from_quick_label(self, label: str) -> BudgetAiProvider:
        trimmed = label.strip()
        mistral_lb = LlmSettingsDialog.LABEL_MISTRAL
        return BudgetAiProvider.MISTRAL if trimmed == mistral_lb else BudgetAiProvider.OPENAI

    def _render_topbar(self, outer: ctk.CTkFrame) -> None:
        bar = self._mk_top_bar(outer)

    def _mk_top_bar(self, outer: ctk.CTkFrame) -> ctk.CTkFrame:
        bar = ctk.CTkFrame(
            outer,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=0,
            height=56,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        bar.pack(fill="x", pady=(0, 4))
        bar.pack_propagate(False)
        self._fill_top_bar(bar)
        return bar

    def _fill_top_bar(self, bar: ctk.CTkFrame) -> None:
        self._mount_back(bar)
        self._mount_review_title(bar)
        self._mount_settings(bar)

    def _mount_back(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="← Presupuesto",
            command=self._on_back,
            fg_color="transparent",
            text_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.INFO_BG,
            border_color=BudgetUiTheme.ACCENT,
            border_width=1,
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(size=12),
            width=130,
        ).pack(side="left", padx=14, pady=14)

    def _mount_review_title(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            bar,
            text="Revisión de presupuesto",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left", padx=(8, 14), pady=14)

    def _mount_settings(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="Configurar IA",
            command=self._handle_configure_ia,
            fg_color="transparent",
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_color=BudgetUiTheme.BORDER,
            border_width=1,
            corner_radius=8,
            height=32,
            width=130,
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=14, pady=12)

    def _render_hint(self, outer: ctk.CTkFrame) -> None:
        msg = (
            "Cuenta tu situación, envíala a la IA y recibe sugerencias para ajustar "
            "tu presupuesto actual. El proceso es idéntico; solo cambia el proveedor "
            "(OpenAI cobra uso típico, Mistral ofrece plan Experiment gratuito). "
            "También se envía tu salario mensual guardado en Presupuesto para que las "
            "sugerencias repartan ese ingreso de forma equilibrada dentro del tope."
        )
        ctk.CTkLabel(
            outer,
            text=msg,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            anchor="w",
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(8, 4))

    def _render_status_bar(self, outer: ctk.CTkFrame) -> None:
        self._status_lbl = ctk.CTkLabel(
            outer,
            text=self._idle_status_text(),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_TER,
            anchor="w",
        )
        self._status_lbl.pack(anchor="w", pady=(0, 4))

    def _attach_form_panel(self, outer: ctk.CTkFrame) -> None:
        card = BudgetReviewFormCard(outer, on_submit=self._handle_submit_context)
        card.attach()
        self._form = card

    def _attach_results_panel(self, body: ctk.CTkFrame) -> None:
        self._results = BudgetReviewResultsPanel(
            body,
            on_accept=self._handle_accept,
            on_reject=self._handle_reject,
        )

    def _handle_configure_ia(self) -> None:
        dialog = LlmSettingsDialog(self._host.winfo_toplevel())
        if dialog.show():
            self._snap_quick_provider_choice()
            self._set_status_idle()

    def _handle_submit_context(self, context: str) -> None:
        if not self._llm_credentials_ready():
            self._invite_ia_setup()
            return
        self._launch_review_job(context)

    def _llm_credentials_ready(self) -> bool:
        try:
            BudgetReviewLlmFactory.build()
            return True
        except LlmConfigurationError:
            return False

    def _invite_ia_setup(self) -> None:
        if not messagebox.askyesno("Configuración IA", "Falta la API key para el proveedor activo. ¿Configurar ahora?"):
            return
        self._handle_configure_ia()

    def _launch_review_job(self, context: str) -> None:
        assert self._form is not None and self._results is not None
        self._results.clear()
        self._current_result = None
        self._form.set_busy(True)
        self._set_status("Enviando datos a la IA...", BudgetUiTheme.ACCENT)
        threading.Thread(target=self._review_worker, args=(context,), daemon=True).start()

    def _review_worker(self, context: str) -> None:
        try:
            payload = self._execute_review_suite(context)
            self._dispatch_to_ui(self._handle_review_success, payload)
        except BudgetReviewServiceError as exc:
            self._log.exception("Review service failure")
            self._dispatch_to_ui(self._handle_review_failure, str(exc))
        except LlmConfigurationError as exc:
            self._dispatch_to_ui(self._handle_review_failure, str(exc))
        except Exception as exc:  # noqa: BLE001
            self._log.exception("Unexpected review failure")
            self._dispatch_to_ui(self._handle_review_failure, f"Error inesperado: {exc}")

    def _execute_review_suite(self, context: str) -> BudgetReviewResult:
        ledger = BudgetReviewRequest(user_context=context, workspace=self._book.peek())
        backend = BudgetReviewLlmFactory.build()
        engine = BudgetReviewService(client=backend)
        return engine.run_review(ledger)

    def _dispatch_to_ui(self, callback: Callable, *args: object) -> None:
        self._host.after(0, lambda: callback(*args))

    def _handle_review_success(self, result: BudgetReviewResult) -> None:
        assert self._form is not None and self._results is not None
        self._form.set_busy(False)
        self._current_result = result
        self._results.render(result)
        self._set_status("Revisión lista. Revisa las sugerencias.", BudgetUiTheme.GREEN)

    def _handle_review_failure(self, message: str) -> None:
        assert self._form is not None
        self._form.set_busy(False)
        self._set_status(f"Error: {message}", BudgetUiTheme.RED)

    def _handle_accept(self) -> None:
        if self._current_result is None:
            return
        if not self._confirm_apply(self._current_result):
            return
        self._apply_current_result()

    def _confirm_apply(self, result: BudgetReviewResult) -> bool:
        count = len(result.recommendations)
        msg = (
            f"Se actualizarán {count} etiquetas del presupuesto. "
            "Esta acción sobrescribe los montos actuales. ¿Continuar?"
        )
        return messagebox.askyesno("Aplicar revisión", msg)

    def _apply_current_result(self) -> None:
        assert self._current_result is not None
        applier = BudgetReviewApplier(self._book)
        try:
            changed = applier.apply(self._current_result.recommendations)
        except Exception as exc:  # noqa: BLE001
            self._log.exception("Apply failure")
            self._set_status(f"No se pudo aplicar: {exc}", BudgetUiTheme.RED)
            return
        self._on_budget_changed()
        txt = f"{changed} etiquetas actualizadas en el presupuesto."
        self._set_status(txt, BudgetUiTheme.GREEN)
        if self._results is not None:
            self._results.clear()
        self._current_result = None

    def _handle_reject(self) -> None:
        if self._results is not None:
            self._results.clear()
        self._current_result = None
        self._set_status("Sugerencias descartadas.", BudgetUiTheme.TXT_SEC)

    def _set_status(self, text: str, color: str) -> None:
        if self._status_lbl is not None:
            self._status_lbl.configure(text=text, text_color=color)