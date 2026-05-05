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


class SharingTab(QWidget):
    """GUI tab for share creation and share access operations."""

    def __init__(
        self,
        sharing_service: SecureSharingService,
        share_access_service: ShareAccessService,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize sharing/access widgets and dependencies.

        Args:
            sharing_service: Service used to create secure shares.
            share_access_service: Service used to access existing shares.
            parent: Optional Qt parent widget.

        Returns:
            None.
        """
        super().__init__(parent)
        self._sharing_service = sharing_service
        self._share_access_service = share_access_service

        self._file_path_edit = QLineEdit()
        self._output_dir_edit = QLineEdit(str(Path("data") / "encrypted"))
        self._recipient_name_edit = QLineEdit()
        self._recipient_email_edit = QLineEdit()
        self._recipient_authorized_checkbox = QCheckBox("Recipient is authorized")
        self._expires_hours_spin = QSpinBox()
        self._expires_hours_spin.setRange(1, 720)
        self._expires_hours_spin.setValue(24)
        self._actor_edit = QLineEdit("operator")

        self._share_token_edit = QLineEdit()
        self._access_output_dir_edit = QLineEdit(str(Path("data") / "decrypted"))
        self._access_actor_edit = QLineEdit("operator")

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
        container.setStyleSheet("QWidget#panel { background-color: #181818; border-radius: 12px; border: 1px solid #2d2d2d; }")
        
        layout = QGridLayout(container)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(9, 1)

        title1 = QLabel("Create Share Link")
        title1.setStyleSheet("font-size: 21px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title1, 0, 0, 1, 3)

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

        title2 = QLabel("Access Share")
        title2.setStyleSheet("font-size: 21px; font-weight: bold; color: #ffffff; margin-top: 18px;")
        layout.addWidget(title2, 10, 0, 1, 3)

        layout.addWidget(QLabel("Share Token / Link"), 11, 0)
        layout.addWidget(self._share_token_edit, 11, 1, 1, 2)

        layout.addWidget(QLabel("Decryption Output Directory"), 12, 0)
        layout.addWidget(self._access_output_dir_edit, 12, 1)
        browse_access_dir_button = QPushButton("Browse...")
        browse_access_dir_button.clicked.connect(self._browse_access_output_dir)
        layout.addWidget(browse_access_dir_button, 12, 2)

        layout.addWidget(QLabel("Access Actor"), 13, 0)
        layout.addWidget(self._access_actor_edit, 13, 1, 1, 2)

        access_share_button = QPushButton("🔓 Access Shared File (Decrypt)")
        access_share_button.clicked.connect(self._access_share)
        layout.addWidget(access_share_button, 14, 0, 1, 3)
        
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

    def _browse_access_output_dir(self) -> None:
        """Open directory picker for decrypted output location.

        Args:
            None.

        Returns:
            None.
        """
        directory = QFileDialog.getExistingDirectory(self, "Select Decryption Output Directory")
        if directory:
            self._access_output_dir_edit.setText(directory)

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

    def _access_share(self) -> None:
        """Access an existing share token/link and decrypt content.

        Args:
            None.

        Returns:
            None.
        """
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
            QMessageBox.critical(self, "Access Error", str(exc))
