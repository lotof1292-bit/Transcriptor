from __future__ import annotations

import sys
import tempfile
import urllib.request
import json
import re
import subprocess
import os
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

APP_VERSION = "1.0.0"
GITHUB_REPOSITORY = "lotof1292-bit/Transcriptor"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
AI_PROVIDERS = {
    "OpenAI": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "Groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "OpenRouter": ("https://openrouter.ai/api/v1", "meta-llama/llama-3.3-70b-instruct"),
}
KEYRING_SERVICE = "Transcriptor"


class LLMWorker(QThread):
    done = Signal(str)
    error = Signal(str)

    def __init__(self, text, instruction, api_key, base_url, model):
        super().__init__()
        self.text, self.instruction = text, instruction
        self.api_key, self.base_url, self.model = api_key, base_url, model

    def run(self):
        try:
            body = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Eres un asistente experto en resumir y traducir transcripciones. Conserva los hechos y nombres, no inventes información. Responde solo con el resultado solicitado."},
                    {"role": "user", "content": f"{self.instruction}\n\nTEXTO:\n{self.text}"},
                ],
                "temperature": 0.3,
            }).encode("utf-8")
            request = urllib.request.Request(
                self.base_url.rstrip("/") + "/chat/completions", data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "User-Agent": "Transcriptor"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.load(response)
            self.done.emit(result["choices"][0]["message"]["content"].strip())
        except Exception as exc:
            self.error.emit(str(exc))


class AISetupDialog(QDialog):
    def __init__(self, provider="OpenAI", model="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar asistente de IA")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Elige un proveedor compatible y añade tu API key. La clave se guarda en el almacén seguro de Windows."))
        form = QFormLayout()
        self.provider = QComboBox()
        self.provider.addItems([*AI_PROVIDERS, "Compatible personalizado"])
        if provider in [self.provider.itemText(i) for i in range(self.provider.count())]:
            self.provider.setCurrentText(provider)
        self.endpoint = QLineEdit()
        self.model = QLineEdit(model)
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("API key")
        form.addRow("Proveedor", self.provider)
        form.addRow("URL base", self.endpoint)
        form.addRow("Modelo", self.model)
        form.addRow("API key", self.key)
        layout.addLayout(form)
        self.provider.currentTextChanged.connect(self.provider_changed)
        self.provider_changed(self.provider.currentText())
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def provider_changed(self, name):
        if name in AI_PROVIDERS:
            endpoint, model = AI_PROVIDERS[name]
            self.endpoint.setText(endpoint)
            self.model.setText(model)
            self.endpoint.setEnabled(False)
        else:
            self.endpoint.setEnabled(True)
            if not self.endpoint.text() or self.endpoint.text() in [item[0] for item in AI_PROVIDERS.values()]:
                self.endpoint.clear()
            if self.model.text() in [item[1] for item in AI_PROVIDERS.values()]:
                self.model.clear()


class UpdateChecker(QThread):
    available = Signal(str, str)
    checked = Signal(bool)
    failed = Signal(str)

    def run(self):
        try:
            request = urllib.request.Request(RELEASES_API, headers={"User-Agent": "Transcriptor-Updater"})
            with urllib.request.urlopen(request, timeout=8) as response:
                release = json.load(response)
            latest = release.get("tag_name", "").lstrip("v")
            latest_parts = tuple(int(n) for n in re.findall(r"\d+", latest))
            current_parts = tuple(int(n) for n in re.findall(r"\d+", APP_VERSION))
            asset = next((item for item in release.get("assets", []) if item.get("name") == "Transcriptor.exe"), None)
            if latest_parts > current_parts and asset:
                self.available.emit(latest, asset["browser_download_url"])
            else:
                self.checked.emit(True)
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateDownloader(QThread):
    complete = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            target = Path(tempfile.gettempdir()) / "Transcriptor-update.exe"
            request = urllib.request.Request(self.url, headers={"User-Agent": "Transcriptor-Updater"})
            with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
            self.complete.emit(str(target))
        except Exception as exc:
            self.failed.emit(str(exc))


class TranscriptionWorker(QThread):
    status = Signal(str)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, source: str, is_url: bool, model_name: str):
        super().__init__()
        self.source, self.is_url, self.model_name = source, is_url, model_name

    def run(self):
        temp_dir = None
        try:
            media_path = self.source
            if self.is_url:
                self.status.emit("Descargando audio del enlace…")
                import yt_dlp
                temp_dir = tempfile.TemporaryDirectory(prefix="transcriptor_")
                template = str(Path(temp_dir.name) / "media.%(ext)s")
                with yt_dlp.YoutubeDL({"format": "bestaudio/best", "outtmpl": template, "noplaylist": True, "quiet": True}) as dl:
                    info = dl.extract_info(self.source, download=True)
                    media_path = dl.prepare_filename(info)
            self.status.emit(f"Cargando Whisper ({self.model_name}); la primera descarga puede tardar…")
            from faster_whisper import WhisperModel
            model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
            self.status.emit("Transcribiendo…")
            segments, _ = model.transcribe(media_path, vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if not text:
                raise RuntimeError("No se detectó voz en el archivo.")
            self.done.emit(text)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            if temp_dir:
                temp_dir.cleanup()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcriptor | Audio a texto")
        self.resize(1000, 780)
        self.setMinimumSize(760, 620)
        self.file_path = ""
        self.setAcceptDrops(True)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(18)

        header = QHBoxLayout()
        brand = QLabel("T")
        brand.setObjectName("brandMark")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(brand)
        heading = QVBoxLayout()
        title = QLabel("Transcriptor")
        title.setObjectName("pageTitle")
        heading.addWidget(title)
        subtitle = QLabel("Convierte voz en texto, de forma sencilla y privada.")
        subtitle.setObjectName("muted")
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        local_badge = QLabel("●  PROCESAMIENTO LOCAL")
        local_badge.setObjectName("badge")
        header.addWidget(local_badge, 0)
        self.update_button = QPushButton("Buscar actualizaciones")
        self.update_button.setObjectName("updateButton")
        self.update_button.clicked.connect(lambda: self.check_updates(manual=True))
        header.addWidget(self.update_button, 0)
        self.ai_setup_button = QPushButton("Configurar IA")
        self.ai_setup_button.setObjectName("aiButton")
        self.ai_setup_button.clicked.connect(self.configure_ai)
        header.addWidget(self.ai_setup_button, 0)
        layout.addLayout(header)

        source_card = QFrame()
        source_card.setObjectName("card")
        source_layout = QVBoxLayout(source_card)
        source_layout.setContentsMargins(22, 20, 22, 20)
        source_layout.setSpacing(13)
        source_heading = QHBoxLayout()
        source_title = QLabel("1. Elige tu contenido")
        source_title.setObjectName("sectionTitle")
        source_heading.addWidget(source_title)
        source_heading.addStretch()
        source_heading.addWidget(QLabel("ENLACE O ARCHIVO"), 0)
        source_layout.addLayout(source_heading)
        source_layout.addWidget(QLabel("Pega un enlace público o arrastra un archivo de audio/video aquí."))
        self.url = QLineEdit()
        self.url.setPlaceholderText("https://  Pega aquí el enlace de YouTube, Facebook, Reels…")
        self.url.textChanged.connect(self.url_changed)
        source_layout.addWidget(self.url)

        row = QHBoxLayout()
        self.file_label = QLabel("Ningún archivo seleccionado")
        self.file_label.setObjectName("fileLabel")
        choose = QPushButton("Elegir archivo…")
        choose.setObjectName("secondaryButton")
        choose.clicked.connect(self.choose_file)
        row.addWidget(choose, 0)
        row.addWidget(self.file_label, 1)
        source_layout.addLayout(row)
        layout.addWidget(source_card)

        settings_card = QFrame()
        settings_card.setObjectName("card")
        settings_layout = QHBoxLayout(settings_card)
        settings_layout.setContentsMargins(22, 17, 22, 17)
        settings_layout.addWidget(QLabel("2. Calidad de transcripción"))
        settings_layout.addStretch()
        model_row = QHBoxLayout()
        self.model = QComboBox()
        self.model.addItem("Rápida", "small")
        self.model.addItem("Equilibrada", "medium")
        self.model.addItem("Más precisa", "large-v3")
        self.model.setMinimumWidth(180)
        settings_layout.addLayout(model_row)
        settings_layout.addWidget(self.model)
        layout.addWidget(settings_card)

        self.start_button = QPushButton("Transcribir")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.start_transcription)
        layout.addWidget(self.start_button)
        ai_actions = QHBoxLayout()
        ai_actions.addWidget(QLabel("4. Trabaja con tu texto"))
        ai_actions.addStretch()
        self.summarize_button = QPushButton("✦  Resumir")
        self.summarize_button.setObjectName("summaryButton")
        self.summarize_button.clicked.connect(self.start_summary)
        ai_actions.addWidget(self.summarize_button)
        self.translate_button = QPushButton("⇄  Traducir")
        self.translate_button.setObjectName("translateButton")
        self.translate_button.clicked.connect(self.start_translation)
        ai_actions.addWidget(self.translate_button)
        self.replace_button = QPushButton("Aa  Quitar o cambiar palabra")
        self.replace_button.setObjectName("replaceButton")
        self.replace_button.clicked.connect(self.replace_word)
        ai_actions.addWidget(self.replace_button)
        layout.addLayout(ai_actions)
        result_card = QFrame()
        result_card.setObjectName("card")
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(22, 18, 22, 18)
        result_heading = QHBoxLayout()
        result_title = QLabel("3. Tu transcripción")
        result_title.setObjectName("sectionTitle")
        result_heading.addWidget(result_title)
        result_heading.addStretch()
        self.status = QLabel("LISTO")
        self.status.setObjectName("status")
        result_heading.addWidget(self.status)
        result_layout.addLayout(result_heading)
        self.tabs = QTabWidget()
        self.output = QPlainTextEdit()
        self.output.setPlaceholderText("Cuando termine el proceso, el texto aparecerá aquí. Después podrás guardarlo como archivo .txt.")
        self.summary_output = QPlainTextEdit()
        self.summary_output.setPlaceholderText("El resumen generado aparecerá aquí…")
        self.translation_output = QPlainTextEdit()
        self.translation_output.setPlaceholderText("La traducción aparecerá aquí…")
        self.tabs.addTab(self.output, "Transcripción")
        self.tabs.addTab(self.summary_output, "Resumen")
        self.tabs.addTab(self.translation_output, "Traducción")
        result_layout.addWidget(self.tabs, 1)
        save = QPushButton("Guardar como .txt")
        save.setObjectName("secondaryButton")
        save.clicked.connect(self.save_text)
        result_layout.addWidget(save, 0, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(result_card, 1)

        self.status.setText("LISTO · El audio se procesa en este equipo")
        self.status.setObjectName("status")
        self.output.setObjectName("output")
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow,QWidget { background:#f5f4f9; color:#201d32; font:14px 'Segoe UI'; }
            QLabel#brandMark { background:#6542f5; color:white; border-radius:16px; font-size:25px; font-weight:800; min-width:54px; max-width:54px; min-height:54px; max-height:54px; }
            QLabel#pageTitle { color:#211b3a; font-size:28px; font-weight:750; }
            QLabel#muted { color:#706b82; font-size:13px; }
            QLabel#badge { background:#d8fff3; color:#087a60; border:1px solid #8be6cf; border-radius:12px; padding:9px 13px; font-size:10px; font-weight:800; }
            QFrame#card { background:#ffffff; border:1px solid #e5e1ef; border-radius:16px; }
            QLabel#sectionTitle { color:#2a2144; font-size:16px; font-weight:750; }
            QLabel#fileLabel { color:#716b82; padding-left:8px; }
            QLabel#status { color:#078566; font-size:11px; font-weight:800; }
            QLineEdit,QComboBox,QPlainTextEdit { background:#fbfaff; color:#252039; border:1px solid #dcd6ec; border-radius:10px; padding:11px; selection-background-color:#7657ff; }
            QLineEdit:focus,QComboBox:focus,QPlainTextEdit:focus { border:1px solid #7657ff; background:#ffffff; }
            QPlainTextEdit#output { font-size:14px; }
            QPushButton { color:white; background:#6945f5; border:0; border-radius:10px; padding:12px 17px; font-weight:750; }
            QPushButton:hover { background:#5030db; }
            QPushButton:disabled { background:#c4bfd3; color:#f7f6fa; }
            QPushButton#primaryButton { min-height:22px; font-size:15px; }
            QPushButton#secondaryButton { background:#fff0ed; border:1px solid #ffc6bb; color:#b53d32; }
            QPushButton#secondaryButton:hover { background:#ffddd6; }
            QPushButton#updateButton { background:transparent; color:#6542f5; border:1px solid #c9bcff; padding:9px 12px; }
            QPushButton#updateButton:hover { background:#eee9ff; }
            QPushButton#aiButton { background:#fff0d7; color:#9a5700; border:1px solid #ffd38d; padding:9px 12px; }
            QPushButton#aiButton:hover { background:#ffe5b7; }
            QPushButton#summaryButton { background:#fa5d75; }
            QPushButton#summaryButton:hover { background:#e74461; }
            QPushButton#translateButton { background:#087fcd; }
            QPushButton#translateButton:hover { background:#0569ae; }
            QPushButton#replaceButton { background:#078566; }
            QPushButton#replaceButton:hover { background:#056b52; }
            QTabWidget::pane { border:0; }
            QTabBar::tab { background:#eeeaf6; color:#706b82; border-radius:8px; padding:9px 15px; margin-right:5px; }
            QTabBar::tab:selected { background:#6945f5; color:white; }
        """)
        if getattr(sys, "frozen", False):
            QTimer.singleShot(1800, lambda: self.check_updates(manual=False))

    def check_updates(self, manual):
        if not getattr(sys, "frozen", False):
            if manual:
                QMessageBox.information(self, "Actualizaciones", "La comprobación de versiones nuevas estará disponible en el EXE instalado.")
            return
        if hasattr(self, "update_checker") and self.update_checker.isRunning():
            return
        self.update_manual = manual
        self.update_button.setEnabled(False)
        self.update_checker = UpdateChecker()
        self.update_checker.available.connect(self.offer_update)
        self.update_checker.checked.connect(self.up_to_date)
        self.update_checker.failed.connect(self.update_check_failed)
        self.update_checker.finished.connect(lambda: self.update_button.setEnabled(True))
        self.update_checker.start()

    def up_to_date(self, _):
        if self.update_manual:
            QMessageBox.information(self, "Actualizaciones", f"Tienes la versión más reciente ({APP_VERSION}).")

    def update_check_failed(self, error):
        if self.update_manual:
            QMessageBox.warning(self, "No se pudo comprobar", f"Revisa tu conexión e inténtalo de nuevo.\n\n{error}")

    def offer_update(self, version, url):
        answer = QMessageBox.question(
            self, "Actualización disponible",
            f"Está disponible la versión {version}.\nTu versión: {APP_VERSION}\n\n¿Descargarla e instalarla ahora? La aplicación se reiniciará.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.status.setText("DESCARGANDO ACTUALIZACIÓN…")
        self.start_button.setEnabled(False)
        self.update_downloader = UpdateDownloader(url)
        self.update_downloader.complete.connect(self.apply_update)
        self.update_downloader.failed.connect(self.update_download_failed)
        self.update_downloader.start()

    def apply_update(self, downloaded_path):
        if not getattr(sys, "frozen", False):
            return
        current = Path(sys.executable).resolve()
        downloaded = Path(downloaded_path).resolve()
        script = Path(tempfile.gettempdir()) / "transcriptor_apply_update.ps1"
        def ps_quote(value):
            return "'" + str(value).replace("'", "''") + "'"
        script.write_text(
            f"Start-Sleep -Seconds 2\n"
            f"while (Get-Process -Id {os.getpid()} -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 400 }}\n"
            f"Move-Item -LiteralPath {ps_quote(downloaded)} -Destination {ps_quote(current)} -Force\n"
            f"Start-Process -FilePath {ps_quote(current)}\n"
            f"Remove-Item -LiteralPath $PSCommandPath -Force\n",
            encoding="utf-8",
        )
        subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.close()

    def update_download_failed(self, error):
        self.status.setText("NO SE PUDO DESCARGAR LA ACTUALIZACIÓN")
        self.start_button.setEnabled(True)
        QMessageBox.warning(self, "Error de descarga", error)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            self.file_path = urls[0].toLocalFile()
            self.url.clear()
            self.file_label.setText(Path(self.file_path).name)
            event.acceptProposedAction()

    def url_changed(self, value):
        if value.strip() and self.file_path:
            self.file_path = ""
            self.file_label.setText("Ningún archivo seleccionado")

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar audio o video", "", "Medios (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.mp4 *.mkv *.mov *.webm);;Todos (*)")
        if path:
            self.file_path = path
            self.url.clear()
            self.file_label.setText(Path(path).name)

    def start_transcription(self):
        url = self.url.text().strip()
        if not url and not self.file_path:
            QMessageBox.information(self, "Falta el contenido", "Pega un enlace o elige un archivo primero.")
            return
        self.start_button.setEnabled(False)
        self.output.clear()
        self.status.setText("TRANSCRIBIENDO…")
        self.tabs.setCurrentWidget(self.output)
        self.worker = TranscriptionWorker(url or self.file_path, bool(url), self.model.currentData())
        self.worker.status.connect(self.status.setText)
        self.worker.done.connect(self.transcription_done)
        self.worker.error.connect(self.transcription_error)
        self.worker.start()

    def transcription_done(self, text):
        self.output.setPlainText(text)
        self.status.setText("Transcripción completada.")
        self.start_button.setEnabled(True)
        self.summarize_button.setEnabled(True)
        self.translate_button.setEnabled(True)

    def transcription_error(self, message):
        self.status.setText("No se pudo transcribir.")
        QMessageBox.warning(self, "Error de transcripción", message)
        self.start_button.setEnabled(True)

    def configure_ai(self):
        try:
            import keyring
        except ImportError:
            QMessageBox.warning(self, "Falta un componente", "No se encontró el almacén seguro de credenciales. Reinstala Transcriptor para habilitar el asistente de IA.")
            return
        settings = self.settings()
        dialog = AISetupDialog(settings.value("provider", "OpenAI"), settings.value("model", ""), self)
        dialog.key.setText(keyring.get_password(KEYRING_SERVICE, "api_key") or "")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        key = dialog.key.text().strip()
        endpoint = dialog.endpoint.text().strip().rstrip("/")
        model = dialog.model.text().strip()
        if not key or not endpoint.startswith("https://") or not model:
            QMessageBox.warning(self, "Revisa la configuración", "Se requiere API key, modelo y una URL base HTTPS válida.")
            return
        keyring.set_password(KEYRING_SERVICE, "api_key", key)
        settings.setValue("provider", dialog.provider.currentText())
        settings.setValue("endpoint", endpoint)
        settings.setValue("model", model)
        self.status.setText("IA CONFIGURADA")

    def settings(self):
        from PySide6.QtCore import QSettings
        return QSettings("Transcriptor", "Transcriptor")

    def transcript_text(self):
        text = self.output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Falta la transcripción", "Primero transcribe un audio o video.")
            return ""
        return text

    def llm_credentials(self):
        try:
            import keyring
            key = keyring.get_password(KEYRING_SERVICE, "api_key")
        except Exception:
            key = None
        settings = self.settings()
        if not key or not settings.value("endpoint") or not settings.value("model"):
            QMessageBox.information(self, "Configura el asistente", "Añade un proveedor y API key para generar resúmenes y traducciones.")
            self.configure_ai()
            try:
                import keyring
                key = keyring.get_password(KEYRING_SERVICE, "api_key")
            except Exception:
                key = None
        if not key:
            return None
        return key, settings.value("endpoint"), settings.value("model")

    def start_summary(self):
        text = self.transcript_text()
        if not text:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("¿Qué deseas destacar?")
        dialog.setMinimumWidth(470)
        form = QVBoxLayout(dialog)
        form.addWidget(QLabel("Elige un enfoque o escribe exactamente qué quieres que el resumen priorice."))
        focus = QComboBox()
        focus.addItems(["Ideas principales", "Acuerdos y tareas pendientes", "Fechas, cifras y nombres", "Argumentos y conclusiones", "Resumen ejecutivo breve", "Otro enfoque…"])
        form.addWidget(focus)
        detail = QLineEdit()
        detail.setPlaceholderText("Opcional: indica el contexto o el nivel de detalle")
        form.addWidget(detail)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Generar resumen")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        choice = focus.currentText()
        if choice == "Otro enfoque…":
            choice = detail.text().strip()
            if not choice:
                QMessageBox.information(self, "Indica el enfoque", "Escribe qué deseas destacar en el resumen.")
                return
        elif detail.text().strip():
            choice += ". Contexto adicional: " + detail.text().strip()
        self.run_llm(text, f"Resume la transcripción en español. Enfoque solicitado: {choice}. Usa títulos y viñetas cuando ayuden.", self.summary_output, "GENERANDO RESUMEN…")

    def start_translation(self):
        text = self.transcript_text()
        if not text:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Traducir transcripción")
        dialog.setMinimumWidth(420)
        form = QVBoxLayout(dialog)
        form.addWidget(QLabel("Selecciona el idioma al que quieres traducir."))
        language = QComboBox()
        language.addItems(["Inglés", "Español", "Francés", "Portugués", "Alemán", "Italiano", "Japonés", "Coreano", "Chino simplificado", "Otro idioma…"])
        form.addWidget(language)
        custom = QLineEdit()
        custom.setPlaceholderText("Escribe el idioma")
        custom.setEnabled(False)
        language.currentTextChanged.connect(lambda value: custom.setEnabled(value == "Otro idioma…"))
        form.addWidget(custom)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Traducir")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        target = custom.text().strip() if language.currentText() == "Otro idioma…" else language.currentText()
        if not target:
            QMessageBox.information(self, "Indica el idioma", "Escribe el idioma de destino.")
            return
        self.run_llm(text, f"Traduce íntegramente la transcripción al idioma {target}. Conserva el sentido, los nombres propios y el formato. No resumas.", self.translation_output, "TRADUCIENDO…")

    def replace_word(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Quitar o cambiar palabra")
        dialog.setMinimumWidth(450)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Busca todas las apariciones de una palabra completa y cámbiala por otra. Deja el reemplazo vacío para quitarla."))
        form = QFormLayout()
        find = QLineEdit()
        find.setPlaceholderText("Palabra que quieres quitar o cambiar")
        replacement = QLineEdit()
        replacement.setPlaceholderText("Palabra nueva (vacío = quitar)")
        form.addRow("Buscar", find)
        form.addRow("Reemplazar por", replacement)
        layout.addLayout(form)
        all_tabs = QCheckBox("Aplicar a la transcripción, el resumen y la traducción")
        all_tabs.setChecked(True)
        layout.addWidget(all_tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar cambios")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        term = find.text().strip()
        if not term:
            QMessageBox.information(self, "Escribe una palabra", "Indica qué palabra quieres buscar.")
            return
        targets = [self.output, self.summary_output, self.translation_output] if all_tabs.isChecked() else [self.tabs.currentWidget()]
        pattern = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE | re.UNICODE)
        total = 0
        for editor in targets:
            original = editor.toPlainText()
            updated, count = pattern.subn(replacement.text(), original)
            editor.setPlainText(updated)
            total += count
        if total:
            self.status.setText(f"CAMBIOS APLICADOS · {total} aparición(es)")
            QMessageBox.information(self, "Texto actualizado", f"Se cambiaron o quitaron {total} aparición(es).")
        else:
            QMessageBox.information(self, "Sin coincidencias", f"No se encontró la palabra completa «{term}» en el texto seleccionado.")

    def run_llm(self, text, instruction, target, status):
        credentials = self.llm_credentials()
        if not credentials:
            return
        key, endpoint, model = credentials
        self.status.setText(status)
        self.summarize_button.setEnabled(False)
        self.translate_button.setEnabled(False)
        self.llm_target = target
        self.tabs.setCurrentWidget(target)
        self.llm_worker = LLMWorker(text, instruction, key, endpoint, model)
        self.llm_worker.done.connect(self.llm_done)
        self.llm_worker.error.connect(self.llm_error)
        self.llm_worker.start()

    def llm_done(self, result):
        self.llm_target.setPlainText(result)
        self.status.setText("COMPLETADO")
        self.summarize_button.setEnabled(True)
        self.translate_button.setEnabled(True)

    def llm_error(self, error):
        self.status.setText("NO SE PUDO COMPLETAR")
        self.summarize_button.setEnabled(True)
        self.translate_button.setEnabled(True)
        QMessageBox.warning(self, "Error del asistente de IA", f"No se pudo generar el resultado. Revisa la API key, el modelo y tu conexión.\n\n{error}")

    def save_text(self):
        text = self.tabs.currentWidget().toPlainText()
        if not text:
            QMessageBox.information(self, "Sin texto", "No hay contenido en esta pestaña para guardar.")
            return
        filename = {0: "transcripcion.txt", 1: "resumen.txt", 2: "traduccion.txt"}.get(self.tabs.currentIndex(), "texto.txt")
        path, _ = QFileDialog.getSaveFileName(self, "Guardar texto", filename, "Texto (*.txt)")
        if path:
            Path(path).write_text(text, encoding="utf-8")
            self.status.setText(f"Guardado en {path}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Transcriptor")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
