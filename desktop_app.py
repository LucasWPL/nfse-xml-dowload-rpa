import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.cancellation import JobCancelled
from src.config import Settings, load_settings, merge_settings
from src.logger import AppLogger
from src.runner import run_job


class DesktopApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("NFSe Downloader")
        self.geometry("1080x820")
        self.minsize(980, 740)
        self.configure(bg="#101418")

        self.base_settings = load_settings()
        self.log_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.stop_event = threading.Event()

        self.username_var = tk.StringVar(value=self.base_settings.nfse_username)
        self.password_var = tk.StringVar(value=self.base_settings.nfse_password)
        self.download_path_var = tk.StringVar(value=str(self.base_settings.download_path))
        self.start_date_var = tk.StringVar(value=self.base_settings.start_date_input)
        self.end_date_var = tk.StringVar(value=self.base_settings.end_date_input)
        self.months_back_var = tk.StringVar(value=str(self.base_settings.months_back))
        self.max_period_days_var = tk.StringVar(value=str(self.base_settings.max_period_days))
        self.wait_timeout_var = tk.StringVar(value=str(self.base_settings.wait_timeout))
        self.headless_var = tk.BooleanVar(value=True)
        self.debug_var = tk.BooleanVar(value=self.base_settings.debug)
        self.status_var = tk.StringVar(value="Pronto para executar.")

        self._configure_style()
        self._build_ui()
        self.after(200, self._poll_queue)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", font=("DejaVu Sans", 11))
        style.configure("App.TFrame", background="#101418")
        style.configure("Card.TFrame", background="#171c22")
        style.configure("Hero.TFrame", background="#141a20")
        style.configure("SectionTitle.TLabel", background="#171c22", foreground="#f5f7fa", font=("DejaVu Sans", 12, "bold"))
        style.configure("Body.TLabel", background="#171c22", foreground="#c1cad4")
        style.configure("HeroTitle.TLabel", background="#141a20", foreground="#f5f7fa", font=("DejaVu Sans", 22, "bold"))
        style.configure("HeroText.TLabel", background="#141a20", foreground="#9fb0c1", font=("DejaVu Sans", 11))
        style.configure("Field.TLabel", background="#171c22", foreground="#dce4ec", font=("DejaVu Sans", 10, "bold"))
        style.configure("Muted.TLabel", background="#171c22", foreground="#8ea0b3", font=("DejaVu Sans", 10))
        style.configure("Status.TLabel", background="#141a20", foreground="#7ee787", font=("DejaVu Sans", 11, "bold"))
        style.configure(
            "Primary.TButton",
            background="#2f6fed",
            foreground="#ffffff",
            borderwidth=0,
            focusthickness=0,
            padding=(16, 10),
            font=("DejaVu Sans", 10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#255ed0"), ("disabled", "#344252")],
            foreground=[("disabled", "#9aa8b6")],
        )
        style.configure(
            "Secondary.TButton",
            background="#232b34",
            foreground="#dce4ec",
            borderwidth=0,
            focusthickness=0,
            padding=(14, 10),
            font=("DejaVu Sans", 10, "bold"),
        )
        style.map("Secondary.TButton", background=[("active", "#2b3642")])
        style.configure(
            "TEntry",
            fieldbackground="#0f1419",
            foreground="#f5f7fa",
            insertcolor="#f5f7fa",
            bordercolor="#303b46",
            lightcolor="#303b46",
            darkcolor="#303b46",
            padding=8,
        )
        style.map("TEntry", bordercolor=[("focus", "#2f6fed")], lightcolor=[("focus", "#2f6fed")], darkcolor=[("focus", "#2f6fed")])
        style.configure("TCheckbutton", background="#171c22", foreground="#dce4ec")

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=20, style="Hero.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        ttk.Label(header, text="NFSe Downloader", style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Executa a automação da NFS-e com configuração local e logs em tempo real.",
            style="HeroText.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").grid(row=0, column=1, rowspan=2, sticky="e")

        body = ttk.Frame(self, padding=(18, 0, 18, 18), style="App.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        form_card = ttk.Frame(body, padding=20, style="Card.TFrame")
        form_card.grid(row=0, column=0, sticky="ew")

        log_card = ttk.Frame(body, padding=20, style="Card.TFrame")
        log_card.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)

        for col in range(4):
            form_card.columnconfigure(col, weight=1)

        ttk.Label(form_card, text="Configuração", style="SectionTitle.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 14))
        self._add_entry(form_card, "CPF/CNPJ", self.username_var, 0, 0, columnspan=2)
        self._add_entry(form_card, "Senha", self.password_var, 0, 2, show="*", columnspan=2)
        self._add_path_entry(form_card, "Pasta de downloads", self.download_path_var, 1)
        self._add_entry(form_card, "Data inicial (YYYY-MM-DD)", self.start_date_var, 2, 0, columnspan=2)
        self._add_entry(form_card, "Data final (YYYY-MM-DD)", self.end_date_var, 2, 2, columnspan=2)
        self._add_entry(form_card, "Meses retroativos", self.months_back_var, 3, 0, columnspan=1)
        self._add_entry(form_card, "Janela máxima (dias)", self.max_period_days_var, 3, 1, columnspan=1)
        self._add_entry(form_card, "Timeout (segundos)", self.wait_timeout_var, 3, 2, columnspan=1)

        options = ttk.Frame(form_card, style="Card.TFrame")
        options.grid(row=9, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Checkbutton(options, text="Headless", variable=self.headless_var).pack(side=tk.LEFT)
        ttk.Checkbutton(options, text="Debug", variable=self.debug_var).pack(side=tk.LEFT, padx=(16, 0))

        help_text = (
            "Se a data inicial estiver vazia, o app usa 'Meses retroativos'. "
            "Se a data final estiver vazia, usa a data de hoje. "
            "Headless marcado evita abrir a janela do Chrome."
        )
        ttk.Label(
            form_card,
            text=help_text,
            style="Muted.TLabel",
            wraplength=860,
            justify="left",
        ).grid(
            row=10, column=0, columnspan=4, sticky="w", pady=(14, 0)
        )

        actions = ttk.Frame(form_card, style="Card.TFrame")
        actions.grid(row=11, column=0, columnspan=4, sticky="ew", pady=(18, 0))
        actions.columnconfigure(2, weight=1)

        self.start_button = ttk.Button(actions, text="Iniciar execução", command=self._start_run, style="Primary.TButton")
        self.start_button.grid(row=0, column=0, sticky="w")
        self.stop_button = ttk.Button(
            actions,
            text="Parar execução",
            command=self._stop_run,
            style="Secondary.TButton",
            state="disabled",
        )
        self.stop_button.grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Button(actions, text="Limpar logs", command=self._clear_logs, style="Secondary.TButton").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        ttk.Label(actions, text="Uma execução por vez.", style="Muted.TLabel").grid(row=0, column=3, sticky="e")
        actions.columnconfigure(3, weight=1)

        log_header = ttk.Frame(log_card, style="Card.TFrame")
        log_header.grid(row=0, column=0, sticky="ew")
        log_header.columnconfigure(0, weight=1)

        ttk.Label(log_header, text="Logs de execução", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            log_header,
            text="Acompanhe o progresso, avisos e erros em tempo real.",
            style="Muted.TLabel",
        ).grid(row=0, column=1, sticky="e")

        self.log_text = tk.Text(
            log_card,
            wrap="word",
            state="disabled",
            bg="#0d1117",
            fg="#dbe5ee",
            insertbackground="#dbe5ee",
            relief="flat",
            borderwidth=0,
            font=("DejaVu Sans Mono", 10),
            padx=14,
            pady=14,
            selectbackground="#2f6fed",
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        scrollbar = ttk.Scrollbar(log_card, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(10, 0), padx=(10, 0))
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _add_entry(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        row: int,
        column: int,
        show: str | None = None,
        columnspan: int = 2,
    ) -> None:
        grid_row = row * 2 + 1
        ttk.Label(parent, text=label, style="Field.TLabel").grid(
            row=grid_row,
            column=column,
            columnspan=columnspan,
            sticky="w",
            pady=(0, 6),
        )
        entry = ttk.Entry(parent, textvariable=variable, show=show or "")
        entry.grid(
            row=grid_row + 1,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=(0, 12),
            pady=(0, 10),
        )

    def _add_path_entry(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        grid_row = row * 2 + 1
        ttk.Label(parent, text=label, style="Field.TLabel").grid(
            row=grid_row,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(0, 6),
        )
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=grid_row + 1, column=0, columnspan=3, sticky="ew", padx=(0, 12), pady=(0, 10))
        ttk.Button(parent, text="Escolher pasta", command=self._choose_directory, style="Secondary.TButton").grid(
            row=grid_row + 1, column=3, sticky="ew", pady=(0, 10)
        )

    def _choose_directory(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.download_path_var.get() or ".")
        if selected:
            self.download_path_var.set(selected)

    def _start_run(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Execução em andamento", "Já existe uma execução em andamento.")
            return

        try:
            settings = self._build_settings_from_form()
        except Exception as exc:
            messagebox.showerror("Configuração inválida", str(exc))
            return

        self._clear_logs()
        self.stop_event.clear()
        self.status_var.set("Executando...")
        self.start_button.configure(state="disabled", text="Executando...")
        self.stop_button.configure(state="normal")

        logger = AppLogger(settings.debug, sink=lambda message: self.log_queue.put(("log", message)))
        self.worker = threading.Thread(
            target=self._run_worker,
            args=(settings, logger),
            daemon=True,
        )
        self.worker.start()

    def _stop_run(self) -> None:
        if not self.worker or not self.worker.is_alive():
            return
        self.stop_event.set()
        self.status_var.set("Interrompendo...")
        self.stop_button.configure(state="disabled")
        self._append_log("Solicitação de parada enviada. A execução será interrompida assim que possível.")

    def _build_settings_from_form(self) -> Settings:
        return merge_settings(
            self.base_settings,
            {
                "nfse_username": self.username_var.get(),
                "nfse_password": self.password_var.get(),
                "download_path": self.download_path_var.get(),
                "start_date_input": self.start_date_var.get(),
                "end_date_input": self.end_date_var.get(),
                "months_back": self.months_back_var.get(),
                "max_period_days": self.max_period_days_var.get(),
                "wait_timeout": self.wait_timeout_var.get(),
                "headless": self.headless_var.get(),
                "debug": self.debug_var.get(),
            },
        )

    def _run_worker(self, settings: Settings, logger: AppLogger) -> None:
        try:
            total = run_job(settings, logger, stop_event=self.stop_event)
            self.log_queue.put(("done", f"Execução concluída. {total} arquivo(s) baixado(s)."))
        except JobCancelled as exc:
            self.log_queue.put(("cancelled", str(exc)))
        except Exception as exc:
            self.log_queue.put(("error", str(exc)))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "done":
                    self._append_log(payload)
                    self.status_var.set("Concluído.")
                    self.start_button.configure(state="normal", text="Iniciar execução")
                    self.stop_button.configure(state="disabled")
                elif kind == "cancelled":
                    self._append_log(payload)
                    self.status_var.set("Interrompido.")
                    self.start_button.configure(state="normal", text="Iniciar execução")
                    self.stop_button.configure(state="disabled")
                elif kind == "error":
                    self._append_log(f"Erro: {payload}")
                    self.status_var.set("Falhou.")
                    self.start_button.configure(state="normal", text="Iniciar execução")
                    self.stop_button.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.after(200, self._poll_queue)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _clear_logs(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")


def main() -> None:
    app = DesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
