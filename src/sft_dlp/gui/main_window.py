from __future__ import annotations

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from sft_dlp.core.encryption_engine import FileEncryptionEngine
from sft_dlp.core.share_access_service import ShareAccessService
from sft_dlp.core.sharing_service import SecureSharingService
from sft_dlp.db.repositories import AuditLogRepository, DlpRuleRepository
from sft_dlp.gui.tabs.audit_logs_tab import AuditLogsTab
from sft_dlp.gui.tabs.dlp_rules_tab import DlpRulesTab
from sft_dlp.gui.tabs.encryption_tab import EncryptionTab
from sft_dlp.gui.tabs.sharing_tab import SharingTab
from sft_dlp.gui.theme import MODERN_DARK_QSS


class MainWindow(QMainWindow):
    """Main desktop window with sidebar navigation across feature tabs."""

    def __init__(
        self,
        encryption_engine: FileEncryptionEngine,
        sharing_service: SecureSharingService,
        share_access_service: ShareAccessService,
        dlp_rule_repository: DlpRuleRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        """Build and wire the main application window.

        Args:
            encryption_engine: File encryption service.
            sharing_service: Secure sharing service.
            share_access_service: Share access/decryption service.
            dlp_rule_repository: DLP rule repository for management tab.
            audit_log_repository: Audit log repository for audit tab.

        Returns:
            None.
        """
        super().__init__()
        self.setWindowTitle("Secure File Transfer & Data Leakage Prevention System")
        
        # Apply modern global theme
        self.setStyleSheet(MODERN_DARK_QSS)

        # Main layout container
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(5)
        
        title_label = QLabel("SFT-DLP")
        title_label.setObjectName("appTitle")
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(20)

        # Sidebar Buttons
        self.btn_encryption = QPushButton("🔒 Encryption")
        self.btn_encryption.setCheckable(True)
        self.btn_sharing = QPushButton("🔗 Sharing")
        self.btn_sharing.setCheckable(True)
        self.btn_dlp = QPushButton("🛡️ DLP Rules")
        self.btn_dlp.setCheckable(True)
        self.btn_audit = QPushButton("📋 Audit Logs")
        self.btn_audit.setCheckable(True)
        
        # Group buttons logically
        self.nav_buttons = [
            self.btn_encryption,
            self.btn_sharing,
            self.btn_dlp,
            self.btn_audit,
        ]

        for i, btn in enumerate(self.nav_buttons):
            sidebar_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, index=i: self.switch_page(index))
        
        sidebar_layout.addStretch()

        # --- Content Area ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(EncryptionTab(encryption_engine=encryption_engine))
        self.stacked_widget.addWidget(
            SharingTab(
                sharing_service=sharing_service,
                share_access_service=share_access_service,
            )
        )
        self.stacked_widget.addWidget(DlpRulesTab(dlp_rule_repository=dlp_rule_repository))
        self.stacked_widget.addWidget(AuditLogsTab(audit_log_repository=audit_log_repository))

        # Add to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget, 1)

        self.setCentralWidget(main_widget)
        
        # Initialize first page
        self.switch_page(0)

    def switch_page(self, index: int) -> None:
        """Switch active tab page and button selection state.

        Args:
            index: Target stacked-widget page index.

        Returns:
            None.
        """
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
