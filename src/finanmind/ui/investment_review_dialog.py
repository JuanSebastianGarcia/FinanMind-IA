"""Modal dialog that runs the AI investment review and shows the result."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.investment_review_request import InvestmentReviewRequest
from finanmind.models.investment_review_result import InvestmentReviewResult
from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.investment_review_llm_factory import InvestmentReviewLlmFactory
from finanmind.services.investment_review_rules_store import (
    InvestmentReviewRulesStore,
)
from finanmind.services.investment_review_service import InvestmentReviewService
from finanmind.services.investment_review_service_error import (
    InvestmentReviewServiceError,
)
from finanmind.services.investment_service import InvestmentService
from finanmind.services.llm_configuration_error import LlmConfigurationError
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_model_store import OpenAiModelStore
from finanmind.services.usd_cop_rate_store import UsdCopRateStore
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.investment_review_results_panel import InvestmentReviewResultsPanel
from finanmind.ui.investment_review_rules_dialog import InvestmentReviewRulesDialog
from finanmind.ui.llm_settings_dialog import LlmSettingsDialog


class InvestmentReviewDialog:
    """Hosts the analyze button, status bar, and the results panel."""

    _WINDOW_SIZE = "780x640"

    def __init__(self, master: ctk.Misc, service: InvestmentService) -> None:
        self._master = master
        self._service = service
        self._log = logging.getLogger("finanmind.investments.review.ui")
        self._win: ctk.CTkToplevel | None = None
        self._status_lbl: ctk.CTkLabel | None = None
        self._analyze_btn: ctk.CTkButton | None = None
        self._results: InvestmentReviewResultsPanel | None = None
        self._scroll: ctk.CTkScrollableFrame | None = None
        self._rate_var: ctk.StringVar | None = None
        self._rules_store = InvestmentReviewRulesStore()
        self._rules_btn: ctk.CTkButton | None = None

    def show(self) -> None:
        """Open the dialog modally."""
        self._spawn()
        assert self._win is not None
        self._master.wait_window(self._win)

    def _spawn(self) -> None:
        self._rules_store.load()
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Análisis IA del portafolio")
        win.geometry(self._WINDOW_SIZE)
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_MAIN)
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_MAIN)
        shell.pack(fill="both", expand=True, padx=14, pady=14)
        self._mount_header(shell)
        self._mount_rules_strip(shell)
        self._mount_rate_strip(shell)
        self._mount_status_bar(shell)
        self._mount_action_bar(shell)
        self._mount_results_scroll(shell)
        self._set_status_idle()

    def _mount_rules_strip(self, shell: ctk.CTkFrame) -> None:
        strip = ctk.CTkFrame(shell, fg_color="transparent")
        strip.pack(fill="x", pady=(0, 6))
        self._mount_rules_label(strip)
        self._mount_rules_button(strip)

    def _mount_rules_label(self, strip: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            strip,
            text="Contexto personal:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left", padx=(0, 8))

    def _mount_rules_button(self, strip: ctk.CTkFrame) -> None:
        btn = ctk.CTkButton(
            strip,
            text=self._rules_button_text(),
            command=self._handle_open_rules,
            fg_color=BudgetUiTheme.BG_CARD,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_width=1,
            border_color=BudgetUiTheme.ACCENT,
            text_color=BudgetUiTheme.ACCENT,
            height=30,
        )
        btn.pack(side="left")
        self._rules_btn = btn

    def _rules_button_text(self) -> str:
        count = self._rules_store.count()
        if count == 0:
            return "Agregar reglas personalizadas"
        suffix = "regla" if count == 1 else "reglas"
        return f"Editar reglas ({count} {suffix})"

    def _refresh_rules_button(self) -> None:
        if self._rules_btn is not None:
            self._rules_btn.configure(text=self._rules_button_text())

    def _handle_open_rules(self) -> None:
        assert self._win is not None
        dlg = InvestmentReviewRulesDialog(
            self._win,
            self._rules_store,
            on_changed=self._refresh_rules_button,
        )
        dlg.show()
        self._refresh_rules_button()

    def _mount_rate_strip(self, shell: ctk.CTkFrame) -> None:
        strip = ctk.CTkFrame(shell, fg_color="transparent")
        strip.pack(fill="x", pady=(0, 6))
        self._mount_rate_label(strip)
        self._mount_rate_entry(strip)
        self._mount_rate_hint(strip)

    def _mount_rate_label(self, strip: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            strip,
            text="Tasa USD→COP:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left", padx=(0, 8))

    def _mount_rate_entry(self, strip: ctk.CTkFrame) -> None:
        self._rate_var = ctk.StringVar(value=self._initial_rate_text())
        ctk.CTkEntry(
            strip,
            textvariable=self._rate_var,
            width=110,
            height=30,
            justify="right",
            fg_color=BudgetUiTheme.BG_CARD,
            text_color=BudgetUiTheme.TXT_PRI,
            border_color=BudgetUiTheme.BORDER,
        ).pack(side="left")

    def _mount_rate_hint(self, strip: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            strip,
            text="(se usa para unificar todo el portafolio en COP)",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
        ).pack(side="left", padx=(8, 0))

    def _initial_rate_text(self) -> str:
        rate = UsdCopRateStore.resolve_rate()
        return f"{rate:.2f}"

    def _mount_header(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            shell,
            text="Análisis IA del portafolio",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w")
        self._mount_header_hint(shell)

    def _mount_header_hint(self, shell: ctk.CTkFrame) -> None:
        hint = (
            "La IA analizará tus inversiones (monto, moneda, tipo y fecha) y "
            "propondrá decisiones, nuevas ideas y cambios concretos al portafolio."
        )
        ctk.CTkLabel(
            shell,
            text=hint,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=720,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(2, 8))

    def _mount_status_bar(self, shell: ctk.CTkFrame) -> None:
        self._status_lbl = ctk.CTkLabel(
            shell,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_TER,
            anchor="w",
        )
        self._status_lbl.pack(anchor="w", pady=(0, 6))

    def _mount_action_bar(self, shell: ctk.CTkFrame) -> None:
        bar = ctk.CTkFrame(shell, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 8))
        self._mount_close_button(bar)
        self._mount_analyze_button(bar)

    def _mount_analyze_button(self, bar: ctk.CTkFrame) -> None:
        self._analyze_btn = ctk.CTkButton(
            bar,
            text="Solicitar análisis",
            command=self._handle_analyze,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            height=34,
            width=180,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self._analyze_btn.pack(side="right")

    def _mount_close_button(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="Cerrar",
            command=self._close,
            fg_color=BudgetUiTheme.BG_CARD,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
            height=34,
            width=120,
        ).pack(side="right", padx=(0, 8))

    def _mount_results_scroll(self, shell: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(
            shell,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll
        self._results = InvestmentReviewResultsPanel(scroll)

    def _handle_analyze(self) -> None:
        if not self._llm_credentials_ready():
            self._invite_ia_setup()
            return
        if not self._service.entries_snapshot():
            messagebox.showinfo(
                "Finanmind",
                "Registra al menos una inversión antes de pedir un análisis.",
            )
            return
        rate = self._consume_rate_input()
        if rate is None:
            return
        self._launch_review_job(rate)

    def _consume_rate_input(self) -> float | None:
        assert self._rate_var is not None
        raw = self._rate_var.get().strip().replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            messagebox.showerror("Finanmind", "La tasa USD→COP debe ser un número.")
            return None
        if value <= 0:
            messagebox.showerror("Finanmind", "La tasa USD→COP debe ser mayor que cero.")
            return None
        self._persist_rate_quietly(value)
        return value

    def _persist_rate_quietly(self, value: float) -> None:
        if UsdCopRateStore.env_var_in_use():
            return
        try:
            UsdCopRateStore.persist_rate(value)
        except (RuntimeError, ValueError):
            self._log.warning("Could not persist USD→COP rate; using session value only.")

    def _llm_credentials_ready(self) -> bool:
        try:
            InvestmentReviewLlmFactory.build()
            return True
        except LlmConfigurationError:
            return False

    def _invite_ia_setup(self) -> None:
        msg = "Falta la API key para el proveedor activo. ¿Configurar ahora?"
        if not messagebox.askyesno("Configuración IA", msg):
            return
        self._open_settings_dialog()

    def _open_settings_dialog(self) -> None:
        assert self._win is not None
        if LlmSettingsDialog(self._win).show():
            self._set_status_idle()

    def _launch_review_job(self, rate: float) -> None:
        assert self._results is not None and self._analyze_btn is not None
        self._results.clear()
        self._analyze_btn.configure(state="disabled", text="Analizando...")
        self._set_status("Enviando portafolio a la IA...", BudgetUiTheme.ACCENT)
        threading.Thread(target=self._review_worker, args=(rate,), daemon=True).start()

    def _review_worker(self, rate: float) -> None:
        try:
            payload = self._execute_review_suite(rate)
            self._dispatch_to_ui(self._handle_review_success, payload)
        except InvestmentReviewServiceError as exc:
            self._log.exception("Review service failure")
            self._dispatch_to_ui(self._handle_review_failure, str(exc))
        except LlmConfigurationError as exc:
            self._dispatch_to_ui(self._handle_review_failure, str(exc))
        except Exception as exc:  # noqa: BLE001
            self._log.exception("Unexpected investment review failure")
            self._dispatch_to_ui(self._handle_review_failure, f"Error inesperado: {exc}")

    def _execute_review_suite(self, rate: float) -> InvestmentReviewResult:
        request = InvestmentReviewRequest(
            entries=self._service.entries_snapshot(),
            categories=self._service.categories_snapshot(),
            usd_to_cop_rate=rate,
            personal_rules=self._collect_rule_texts(),
        )
        backend = InvestmentReviewLlmFactory.build()
        engine = InvestmentReviewService(client=backend)
        return engine.run_review(request)

    def _collect_rule_texts(self) -> list[str]:
        return [rule.cleaned_text() for rule in self._rules_store.snapshot()]

    def _dispatch_to_ui(self, callback: Callable, *args: object) -> None:
        if self._win is None:
            return
        self._win.after(0, lambda: callback(*args))

    def _handle_review_success(self, result: InvestmentReviewResult) -> None:
        assert self._results is not None
        self._restore_analyze_button()
        self._results.render(result)
        self._set_status("Análisis listo. Revisa las recomendaciones.", BudgetUiTheme.GREEN)

    def _handle_review_failure(self, message: str) -> None:
        self._restore_analyze_button()
        self._set_status(f"Error: {message}", BudgetUiTheme.RED)

    def _restore_analyze_button(self) -> None:
        if self._analyze_btn is not None:
            self._analyze_btn.configure(state="normal", text="Solicitar análisis")

    def _set_status_idle(self) -> None:
        self._set_status(self._idle_status_text(), BudgetUiTheme.TXT_TER)

    def _idle_status_text(self) -> str:
        return f"Proveedor: {self._vendor_human_name()} · Modelo: {self._active_model_slug()}"

    def _vendor_human_name(self) -> str:
        if BudgetAiProviderStore.resolve() == BudgetAiProvider.MISTRAL:
            return "Mistral"
        return "OpenAI"

    def _active_model_slug(self) -> str:
        if BudgetAiProviderStore.resolve() == BudgetAiProvider.MISTRAL:
            return MistralModelStore.resolve_model()
        return OpenAiModelStore.resolve_model()

    def _set_status(self, text: str, color: str) -> None:
        if self._status_lbl is not None:
            self._status_lbl.configure(text=text, text_color=color)

    def _close(self) -> None:
        if self._win is not None:
            self._win.destroy()
            self._win = None
