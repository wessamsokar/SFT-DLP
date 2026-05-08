from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sft_dlp.core.share_access_service import ShareAccessService
from sft_dlp.core.sharing_service import SecureSharingService


class CreateShareTab(QWidget):
    """GUI tab for secure share creation only."""

    def __init__(
        self,
        sharing_service: SecureSharingService,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize share-creation widgets and dependencies.

        Args:
            sharing_service: Service used to create secure shares.
            parent: Optional Qt parent widget.

        Returns:
            None.
        """
        super().__init__(parent)
        self._sharing_service = sharing_service

        self._file_path_edit = QLineEdit()
        self._file_path_edit.setPlaceholderText("Select source file to share...")
        self._output_dir_edit = QLineEdit(str(Path("data") / "encrypted"))
        self._output_dir_edit.setPlaceholderText("Encrypted output directory")
        self._recipient_name_edit = QLineEdit()
        self._recipient_name_edit.setPlaceholderText("Recipient full name")
        self._recipient_email_edit = QLineEdit()
        self._recipient_email_edit.setPlaceholderText("recipient@example.com")
        self._recipient_authorized_checkbox = QCheckBox("Recipient is authorized")
        self._expires_hours_spin = QSpinBox()
        self._expires_hours_spin.setRange(1, 720)
        self._expires_hours_spin.setValue(24)
        self._actor_edit = QLineEdit("operator")
        self._actor_edit.setPlaceholderText("Share creator actor")

        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMinimumHeight(160)

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct tab UI and button signal connections.

        Args:
            None.

        Returns:
            None.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 30)
        main_layout.setSpacing(18)

        container = QWidget()
        container.setObjectName("panel")
        
        layout = QGridLayout(container)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(10, 1)

        title = QLabel("Create Share Link")
        title.setStyleSheet("font-size: 21px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title, 0, 0, 1, 3)

        layout.addWidget(QLabel("Source File"), 1, 0)
        layout.addWidget(self._file_path_edit, 1, 1)
        browse_file_button = QPushButton("Browse...")
        browse_file_button.clicked.connect(self._browse_file)
        layout.addWidget(browse_file_button, 1, 2)

        layout.addWidget(QLabel("Encrypted Output Directory"), 2, 0)
        layout.addWidget(self._output_dir_edit, 2, 1)
        browse_dir_button = QPushButton("Browse...")
        browse_dir_button.clicked.connect(self._browse_output_dir)
        layout.addWidget(browse_dir_button, 2, 2)

        layout.addWidget(QLabel("Recipient Name"), 3, 0)
        layout.addWidget(self._recipient_name_edit, 3, 1, 1, 2)

        layout.addWidget(QLabel("Recipient Email"), 4, 0)
        layout.addWidget(self._recipient_email_edit, 4, 1, 1, 2)

        layout.addWidget(QLabel("Authorization"), 5, 0)
        layout.addWidget(self._recipient_authorized_checkbox, 5, 1, 1, 2)

        layout.addWidget(QLabel("Expiry (hours)"), 6, 0)
        layout.addWidget(self._expires_hours_spin, 6, 1, 1, 2)

        layout.addWidget(QLabel("Actor"), 7, 0)
        layout.addWidget(self._actor_edit, 7, 1, 1, 2)

        create_share_button = QPushButton("🔗 Create Secure Share Link")
        create_share_button.clicked.connect(self._create_share)
        layout.addWidget(create_share_button, 8, 0, 1, 3)

        layout.addWidget(QLabel("Result"), 9, 0)
        layout.addWidget(self._result_text, 9, 1, 1, 2)
        
        main_layout.addWidget(container, 1)

    def _browse_file(self) -> None:
        """Open file picker for source file selection.

        Args:
            None.

        Returns:
            None.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Share")
        if file_path:
            self._file_path_edit.setText(file_path)

    def _browse_output_dir(self) -> None:
        """Open directory picker for encrypted output location.

        Args:
            None.

        Returns:
            None.
        """
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self._output_dir_edit.setText(directory)

    def _create_share(self) -> None:
        """Create a secure share after validating mandatory fields.

        Args:
            None.

        Returns:
            None.
        """
        file_path = self._file_path_edit.text().strip()
        output_dir = self._output_dir_edit.text().strip()
        recipient_email = self._recipient_email_edit.text().strip()
        recipient_name = self._recipient_name_edit.text().strip()
        actor = self._actor_edit.text().strip() or "operator"

        if not file_path or not recipient_email:
            QMessageBox.warning(
                self,
                "Missing Inputs",
                "Source file and recipient email are required.",
            )
            return

        try:
            result = self._sharing_service.create_share(
                file_path=Path(file_path),
                output_dir=Path(output_dir or str(Path("data") / "encrypted")),
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                recipient_authorized=self._recipient_authorized_checkbox.isChecked(),
                expires_in_hours=int(self._expires_hours_spin.value()),
                actor=actor,
            )
            self._result_text.setPlainText(
                "\n".join(
                    [
                        f"Share ID: {result.share_id}",
                        f"File ID: {result.file_id}",
                        f"Expires At: {result.expires_at}",
                        f"Share Link: {result.share_link}",
                    ]
                )
            )
            QMessageBox.information(self, "Share Created", "Secure share link generated.")
        except PermissionError as exc:
            QMessageBox.warning(self, "Blocked by DLP", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Share Error", str(exc))

class AccessShareTab(QWidget):
    """GUI tab for secure share access/decryption only."""

    def __init__(
        self,
        share_access_service: ShareAccessService,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize share-access widgets and dependencies.

        Args:
            share_access_service: Service used to access existing shares.
            parent: Optional Qt parent widget.

        Returns:
            None.
        """
        super().__init__(parent)
        self._share_access_service = share_access_service

        self._share_token_edit = QLineEdit()
        self._share_token_edit.setPlaceholderText("Paste share token or full share link...")
        self._access_output_dir_edit = QLineEdit(str(Path("data") / "decrypted"))
        self._access_output_dir_edit.setPlaceholderText("Decryption output directory")
        self._access_actor_edit = QLineEdit("operator")
        self._access_actor_edit.setPlaceholderText("Access actor")

        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMinimumHeight(160)

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct access tab UI and button signal connections."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 30)
        main_layout.setSpacing(18)

        container = QWidget()
        container.setObjectName("panel")

        layout = QGridLayout(container)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(6, 1)

        title = QLabel("Access Share")
        title.setStyleSheet("font-size: 21px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title, 0, 0, 1, 3)

        layout.addWidget(QLabel("Share Token / Link"), 1, 0)
        layout.addWidget(self._share_token_edit, 1, 1, 1, 2)

        layout.addWidget(QLabel("Decryption Output Directory"), 2, 0)
        layout.addWidget(self._access_output_dir_edit, 2, 1)
        browse_access_dir_button = QPushButton("Browse...")
        browse_access_dir_button.clicked.connect(self._browse_access_output_dir)
        layout.addWidget(browse_access_dir_button, 2, 2)

        layout.addWidget(QLabel("Access Actor"), 3, 0)
        layout.addWidget(self._access_actor_edit, 3, 1, 1, 2)

        access_share_button = QPushButton("🔓 Access Shared File (Decrypt)")
        access_share_button.clicked.connect(self._access_share)
        layout.addWidget(access_share_button, 4, 0, 1, 3)

        layout.addWidget(QLabel("Result"), 5, 0)
        layout.addWidget(self._result_text, 5, 1, 1, 2)

        main_layout.addWidget(container, 1)

    def _browse_access_output_dir(self) -> None:
        """Open directory picker for decrypted output location."""
        directory = QFileDialog.getExistingDirectory(self, "Select Decryption Output Directory")
        if directory:
            self._access_output_dir_edit.setText(directory)

    def _access_share(self) -> None:
        """Access an existing share token/link and decrypt content."""
        token_or_link = self._share_token_edit.text().strip()
        output_dir = self._access_output_dir_edit.text().strip() or str(Path("data") / "decrypted")
        actor = self._access_actor_edit.text().strip() or "operator"

        if not token_or_link:
            QMessageBox.warning(self, "Missing Input", "Share token or link is required.")
            return

        try:
            result = self._share_access_service.access_share(
                token_or_link=token_or_link,
                output_dir=Path(output_dir),
                actor=actor,
            )
            self._result_text.setPlainText(
                "\n".join(
                    [
                        f"Access Share ID: {result.share_id}",
                        f"File ID: {result.file_id}",
                        f"Decrypted Path: {result.decrypted_path}",
                    ]
                )
            )
            QMessageBox.information(self, "Share Access", "Share file decrypted successfully.")
        except PermissionError as exc:
            QMessageBox.warning(self, "Access Denied", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Access Error", self._humanize_access_error(exc))

    @staticmethod
    def _humanize_access_error(exc: Exception) -> str:
        """Map low-level decryption/access exceptions to readable UI messages."""
        error_text = str(exc).strip()
        normalized = error_text.lower()

        if "mac check failed" in normalized or "invalid encrypted file header" in normalized:
            return (
                "Unable to decrypt this share.\n"
                "The encrypted content appears corrupted or was encrypted with a different key."
            )
        if "encrypted payload is too short" in normalized or "malformed" in normalized:
            return "Encrypted file is incomplete or malformed."
        if "encrypted file not found" in normalized:
            return "Encrypted file was not found on disk. Please regenerate the share and try again."
        if "encryption key not found" in normalized:
            return "Required encryption key is missing. Restore the key store, then retry."
        if "share content is still encrypted" in normalized:
            return (
                "This share was generated from an already encrypted file.\n"
                "Create a new share from the original plaintext file, then decrypt again."
            )
        if "path traversal is not allowed" in normalized:
            return "The selected output path is invalid."
        if "already encrypted (.sftenc)" in normalized:
            return (
                "This file is already encrypted.\n"
                "Please select the original plaintext file, not a .sftenc file."
            )
        if not error_text:
            return "Unknown access error occurred."
        return error_text
