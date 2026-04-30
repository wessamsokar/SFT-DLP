from __future__ import annotations

import sys

from PyQt5.QtWidgets import QApplication

from sft_dlp.config import DEFAULT_DB_PATH, KEYS_DIR
from sft_dlp.core.audit_service import AuditService
from sft_dlp.core.decryption_engine import FileDecryptionEngine
from sft_dlp.core.dlp_engine import DlpPolicyEngine
from sft_dlp.core.encryption_engine import FileEncryptionEngine
from sft_dlp.core.key_manager import OpenSSLKeyManager
from sft_dlp.core.share_access_service import ShareAccessService
from sft_dlp.core.sharing_service import SecureSharingService
from sft_dlp.db.connection import DatabaseConnectionFactory
from sft_dlp.db.init_db import initialize_database
from sft_dlp.db.repositories import (
    AuditLogRepository,
    DlpEventRepository,
    DlpRuleRepository,
    FileRepository,
    KeyStoreRepository,
    RecipientRepository,
    ShareRepository,
)
from sft_dlp.gui.main_window import MainWindow


def build_app() -> QApplication:
    initialize_database(str(DEFAULT_DB_PATH))

    connection_factory = DatabaseConnectionFactory(DEFAULT_DB_PATH)
    audit_log_repository = AuditLogRepository(connection_factory)
    audit_service = AuditService(audit_log_repository)

    file_repository = FileRepository(connection_factory)
    dlp_rule_repository = DlpRuleRepository(connection_factory)
    dlp_event_repository = DlpEventRepository(connection_factory)
    recipient_repository = RecipientRepository(connection_factory)
    share_repository = ShareRepository(connection_factory)

    key_manager = OpenSSLKeyManager(KeyStoreRepository(connection_factory), KEYS_DIR)
    encryption_engine = FileEncryptionEngine(
        file_repository=file_repository,
        key_manager=key_manager,
        audit_service=audit_service,
    )
    dlp_engine = DlpPolicyEngine(
        rule_repository=dlp_rule_repository,
        event_repository=dlp_event_repository,
        audit_service=audit_service,
    )
    sharing_service = SecureSharingService(
        recipient_repository=recipient_repository,
        share_repository=share_repository,
        encryption_engine=encryption_engine,
        dlp_engine=dlp_engine,
        audit_service=audit_service,
    )
    decryption_engine = FileDecryptionEngine(
        file_repository=file_repository,
        key_manager=key_manager,
        audit_service=audit_service,
    )
    share_access_service = ShareAccessService(
        share_repository=share_repository,
        decryption_engine=decryption_engine,
        audit_service=audit_service,
    )

    app = QApplication(sys.argv)
    window = MainWindow(
        encryption_engine=encryption_engine,
        sharing_service=sharing_service,
        share_access_service=share_access_service,
        dlp_rule_repository=dlp_rule_repository,
        audit_log_repository=audit_log_repository,
    )
    window.showMaximized()
    app.exec_()
    return app


def main() -> None:
    build_app()


if __name__ == "__main__":
    main()
