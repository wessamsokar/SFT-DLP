from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from sft_dlp.core.encryption_engine import FileEncryptionEngine


class EncryptionTab(QWidget):
    """GUI tab for local AES-256-GCM file encryption."""

    def __init__(self, encryption_engine: FileEncryptionEngine, parent: QWidget | None = None) -> None:
        """Initialize encryption tab widgets and state.

        Args:
            encryption_engine: Encryption service instance.
            parent: Optional Qt parent widget.

        Returns:
            None.
        """
        super().__init__(parent)
        self._encryption_engine = encryption_engine

        self._input_path_edit = QLineEdit()
        self._output_path_edit = QLineEdit(str(Path("data") / "encrypted"))
        self._actor_edit = QLineEdit("operator")
        self._status_label = QLabel("Ready")

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct tab layout and signal bindings.

        Args:
            None.

        Returns:
            None.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(20)
        
        container = QWidget()
        container.setObjectName("panel")
        
        layout = QGridLayout(container)
        layout.setContentsMargins(36, 34, 36, 34)
        layout.setSpacing(18)
        layout.setColumnStretch(1, 1)

        title = QLabel("File Encryption")
        title.setObjectName("tabTitle")
        layout.addWidget(title, 0, 0, 1, 3)

        layout.addWidget(QLabel("Input File"), 1, 0)
        layout.addWidget(self._input_path_edit, 1, 1)
        browse_input_button = QPushButton("Browse...")
        browse_input_button.clicked.connect(self._browse_input_file)
        layout.addWidget(browse_input_button, 1, 2)

        layout.addWidget(QLabel("Encrypted Output Directory"), 2, 0)
        layout.addWidget(self._output_path_edit, 2, 1)
        browse_output_button = QPushButton("Browse...")
        browse_output_button.clicked.connect(self._browse_output_directory)
        layout.addWidget(browse_output_button, 2, 2)

        layout.addWidget(QLabel("Actor"), 3, 0)
        layout.addWidget(self._actor_edit, 3, 1)

        encrypt_button = QPushButton("🔒 Encrypt File (AES-256-GCM)")
        encrypt_button.setObjectName("primaryBtn")
        encrypt_button.clicked.connect(self._encrypt_file)
        layout.addWidget(encrypt_button, 4, 0, 1, 3)

        layout.addWidget(QLabel("Status"), 5, 0)
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label, 5, 1, 1, 2)
        
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(container)
        center_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()

    def _browse_input_file(self) -> None:
        """Open file picker and populate input path.

        Args:
            None.

        Returns:
            None.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Encrypt")
        if file_path:
            self._input_path_edit.setText(file_path)

    def _browse_output_directory(self) -> None:
        """Open directory picker and populate output path.

        Args:
            None.

        Returns:
            None.
        """
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self._output_path_edit.setText(directory)

    def _encrypt_file(self) -> None:
        """Validate user input and run encryption workflow.

        Args:
            None.

        Returns:
            None.
        """
        input_path = self._input_path_edit.text().strip()
        output_dir = self._output_path_edit.text().strip()
        actor = self._actor_edit.text().strip() or "operator"

        if not input_path:
            QMessageBox.warning(self, "Input Required", "Please select an input file.")
            return

        if not output_dir:
            QMessageBox.warning(
                self,
                "Output Required",
                "Please choose an output directory for encrypted files.",
            )
            return

        try:
            result = self._encryption_engine.encrypt_file(
                input_path=Path(input_path),
                output_dir=Path(output_dir),
                actor=actor,
            )
            self._status_label.setText(
                f"Encrypted successfully. file_id={result.file_id}, key_id={result.key_id}"
            )
            QMessageBox.information(
                self,
                "Success",
                f"Encrypted file created at:\n{result.encrypted_path}",
            )
        except Exception as exc:
            self._status_label.setText(f"Error: {exc}")
            QMessageBox.critical(self, "Encryption Failed", str(exc))
