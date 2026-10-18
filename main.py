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
    QFrame, QHBoxLayout, QLabel, QLayout, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget,
)

APP_VERSION = "1.1.3"
GITHUB_REPOSITORY = "lotof1292-bit/Transcriptor"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
AI_MODEL_NAME = "Qwen3-0.6B-Q4_K_M.gguf"
AI_MODEL_URL = "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/main/Qwen_Qwen3-0.6B-Q4_K_M.gguf?download=true"


class LocalAIWorker(QThread):
    status = Signal(str)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, text, instruction, mode):
        super().__init__()
        self.text, self.instruction = text, instruction
        self.mode = mode

    def run(self):
        model = None
        try:
            local_root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Transcriptor" / "models"
            local_root.mkdir(parents=True, exist_ok=True)
            model_path = local_root / AI_MODEL_NAME
            if not model_path.exists() or model_path.stat().st_size < 400_000_000:
                partial = model_path.with_suffix(model_path.suffix + ".part")
                self.status.emit("Descargando IA local (aprox. 500 MB)…")
                request = urllib.request.Request(AI_MODEL_URL, headers={"User-Agent": "Transcriptor-Local-AI"})
                with urllib.request.urlopen(request, timeout=90) as response, partial.open("wb") as output:
                    total = int(response.headers.get("Content-Length", "0"))
                    received = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                        received += len(chunk)
                        if total:
                            self.status.emit(f"Descargando IA local… {received * 100 // total}%")
                if partial.stat().st_size < 400_000_000:
                    partial.unlink(missing_ok=True)
                    raise RuntimeError("La descarga del modelo quedó incompleta. Revisa la conexión e inténtalo otra vez.")
                partial.replace(model_path)
            self.status.emit("Cargando el asistente local…")
            from llama_cpp import Llama
            model = Llama(model_path=str(model_path), n_ctx=8192, n_threads=max(2, (os.cpu_count() or 4) - 1), verbose=False)
            pieces = split_for_local_model(self.text, 5500)
            results = []
            for index, piece in enumerate(pieces, start=1):
                self.status.emit(f"{self.mode} con IA local… {index}/{len(pieces)}")
                result = model.create_chat_completion(
                    messages=[
                        {"role": "system", "content": "Eres un asistente experto en resumir y traducir. Conserva los hechos y nombres; no inventes. Responde solo con el resultado solicitado. /no_think"},
                        {"role": "user", "content": f"{self.instruction}\n\nTEXTO:\n{piece}"},
                    ],
                    temperature=0.2,
                    max_tokens=1800 if self.mode == "Traduciendo" else 700,
                )
                results.append(result["choices"][0]["message"]["content"].strip())
            if self.mode == "Resumiendo" and len(results) > 1:
                self.status.emit("Uniendo las partes del resumen…")
                combined = "\n\n".join(results)
                final = model.create_chat_completion(
                    messages=[
                        {"role": "system", "content": "Sintetiza resúmenes parciales en un único resumen fiel, sin duplicaciones. Responde solo con el resultado. /no_think"},
                        {"role": "user", "content": f"Enfoque: {self.instruction}\n\nRESÚMENES PARCIALES:\n{combined}"},
                    ],
                    temperature=0.2,
                    max_tokens=1200,
                )
                results = [final["choices"][0]["message"]["content"].strip()]
            self.done.emit("\n\n".join(results))
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            if model is not None:
                model.close()


def split_for_local_model(text: str, limit: int) -> list[str]:
    chunks = []
    remaining = text.strip()
    while len(remaining) > limit:
        end = max(remaining.rfind("\n", 0, limit), remaining.rfind(". ", 0, limit), remaining.rfind(" ", 0, limit))
        if end < limit // 2:
            end = limit
        chunks.append(remaining[:end].strip())
        remaining = remaining[end:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


class UpdateChecker(QThread):
    available = Signal(str, str, str)
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
            assets = release.get("assets", [])
            asset = next((item for item in assets if item.get("name") == "Transcriptor-Windows.zip"), None)
            if asset is None:
                asset = next((item for item in assets if item.get("name") == "Transcriptor.exe"), None)
            if latest_parts > current_parts and asset:
                self.available.emit(latest, asset["browser_download_url"], asset["name"])
            else:
                self.checked.emit(True)
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateDownloader(QThread):
    complete = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str, asset_name: str):
        super().__init__()
        self.url = url
        self.asset_name = asset_name

    def run(self):
        try:
            target = Path(tempfile.gettempdir()) / self.asset_name
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
            model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=2,
                num_workers=1,
            )
            self.status.emit("Transcribiendo…")
            segments, _ = model.transcribe(
                media_path,
                beam_size=1,
                condition_on_previous_text=False,
                vad_filter=True,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if not text:
                raise RuntimeError("No se detectó voz en el archivo.")
            self.done.emit(text)
        except Exception as exc:
            message = str(exc)
            if "malloc" in message.lower() or "memory" in message.lower():
                message = (
                    "El equipo se quedó sin memoria durante la transcripción. "
                    "Cierra otros programas e inténtalo con la calidad Rápida.\n\n"
                    f"Detalle: {message}"
                )
            self.error.emit(message)
        finally:
            if temp_dir:
                temp_dir.cleanup()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcriptor | Audio a texto")
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        if available:
            min_width = min(640, max(420, available.width() - 40))
            min_height = min(520, max(360, available.height() - 40))
            self.resize(max(min_width, min(1024, available.width() - 60)), max(min_height, min(760, available.height() - 80)))
        else:
            min_width, min_height = 640, 520
            self.resize(960, 680)
        self.setMinimumSize(min_width, min_height)
        self.file_path = ""
        self.setAcceptDrops(True)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        header = QHBoxLayout()
        brand = QLabel("T")
        brand.setObjectName("brandMark")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(brand)
        heading = QVBoxLayout()
        title = QLabel("Transcriptor")
        title.setObjectName("pageTitle")
        heading.addWidget(title)
        subtitle = QLabel("Transcribe, resume y traduce con inteligencia artificial local.")
        subtitle.setObjectName("muted")
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        local_badge = QLabel("●  IA LOCAL · SIN API KEY")
        local_badge.setObjectName("badge")
        local_badge.setToolTip("El modelo se descarga una sola vez y después funciona en este equipo.")
        header.addWidget(local_badge, 0)
        layout.addLayout(header)
        header_actions = QHBoxLayout()
        header_actions.addStretch()
        self.update_button = QPushButton("Buscar actualizaciones")
        self.update_button.setObjectName("updateButton")
        self.update_button.clicked.connect(lambda: self.check_updates(manual=True))
        header_actions.addWidget(self.update_button, 0)
        layout.addLayout(header_actions)

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
        self.model = QComboBox()
        self.model.addItem("Rápida · menos memoria", "tiny")
        self.model.addItem("Equilibrada", "base")
        self.model.addItem("Más precisa", "small")
        self.model.setMinimumWidth(180)
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
        self.tabs.setMinimumHeight(275)
        result_layout.addWidget(self.tabs, 1)
        save = QPushButton("Guardar como .txt")
        save.setObjectName("secondaryButton")
        save.clicked.connect(self.save_text)
        result_layout.addWidget(save, 0, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(result_card, 1)

        self.status.setText("LISTO · El audio se procesa en este equipo")
        self.status.setObjectName("status")
        self.output.setObjectName("output")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(root)
        self.setCentralWidget(scroll)
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

    def offer_update(self, version, url, asset_name):
        answer = QMessageBox.question(
            self, "Actualización disponible",
            f"Está disponible la versión {version}.\nTu versión: {APP_VERSION}\n\n¿Descargarla e instalarla ahora? La aplicación se reiniciará.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.status.setText("DESCARGANDO ACTUALIZACIÓN…")
        self.start_button.setEnabled(False)
        self.update_downloader = UpdateDownloader(url, asset_name)
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
        if downloaded.suffix.lower() == ".zip":
            install_dir = current.parent
            unpack_dir = Path(tempfile.gettempdir()) / "Transcriptor-update-unpacked"
            script_body = (
                f"$unpack = {ps_quote(unpack_dir)}\n"
                f"Remove-Item -LiteralPath $unpack -Recurse -Force -ErrorAction SilentlyContinue\n"
                f"Expand-Archive -LiteralPath {ps_quote(downloaded)} -DestinationPath $unpack -Force\n"
                f"Copy-Item -Path (Join-Path $unpack '*') -Destination {ps_quote(install_dir)} -Recurse -Force\n"
                f"Start-Process -FilePath {ps_quote(current)}\n"
                f"Remove-Item -LiteralPath $unpack -Recurse -Force -ErrorAction SilentlyContinue\n"
            )
        else:
            script_body = (
                f"Move-Item -LiteralPath {ps_quote(downloaded)} -Destination {ps_quote(current)} -Force\n"
                f"Start-Process -FilePath {ps_quote(current)}\n"
            )
        script.write_text(
            f"Start-Sleep -Seconds 2\n"
            f"while (Get-Process -Id {os.getpid()} -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 400 }}\n"
            + script_body
            + f"Remove-Item -LiteralPath {ps_quote(downloaded)} -Force -ErrorAction SilentlyContinue\n"
            + "Remove-Item -LiteralPath $PSCommandPath -Force\n",
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

    def transcript_text(self):
        text = self.output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Falta la transcripción", "Primero transcribe un audio o video.")
            return ""
        return text

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
        self.status.setText(status)
        self.summarize_button.setEnabled(False)
        self.translate_button.setEnabled(False)
        self.llm_target = target
        self.tabs.setCurrentWidget(target)
        mode = "Resumiendo" if target is self.summary_output else "Traduciendo"
        self.llm_worker = LocalAIWorker(text, instruction, mode)
        self.llm_worker.status.connect(self.status.setText)
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
        QMessageBox.warning(self, "Error de IA local", f"No se pudo cargar o ejecutar el modelo local. Revisa tu conexión si es la primera vez y vuelve a intentarlo.\n\n{error}")

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
