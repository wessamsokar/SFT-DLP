from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sft_dlp.db.repositories import AuditLogRepository


class AuditLogsTab(QWidget):
    """GUI tab for viewing recent system audit events."""

    def __init__(self, audit_log_repository: AuditLogRepository, parent: QWidget | None = None) -> None:
        """Initialize audit log viewer widgets.

        Args:
            audit_log_repository: Repository used to fetch logs.
            parent: Optional Qt parent widget.

        Returns:
            None.
        """
        super().__init__(parent)
        self._audit_log_repository = audit_log_repository

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Timestamp", "Event", "Actor", "Status", "Message"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self._build_ui()
        self.refresh_logs()

    def _build_ui(self) -> None:
        """Build audit tab layout and controls.

        Args:
            None.

        Returns:
            None.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(14)

        button_row = QHBoxLayout()
        refresh_button = QPushButton("Refresh Logs")
        refresh_button.clicked.connect(self.refresh_logs)
        button_row.addWidget(refresh_button)

        layout.addLayout(button_row)
        layout.addWidget(self._table)

    def refresh_logs(self) -> None:
        """Reload recent audit logs into table view.

        Args:
            None.

        Returns:
            None.
        """
        logs = self._audit_log_repository.get_recent_logs(limit=300)
        self._table.setRowCount(len(logs))

        for row_idx, row in enumerate(logs):
            event_type = str(row["event_type"])
            status = str(row["status"])
            message = str(row["message"])

            self._table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self._table.setItem(row_idx, 1, QTableWidgetItem(str(row["created_at"])))
            self._table.setItem(row_idx, 2, QTableWidgetItem(event_type))
            self._table.setItem(row_idx, 3, QTableWidgetItem(str(row["actor"])))
            self._table.setCellWidget(
                row_idx,
                4,
                self._build_status_badge(
                    status=status,
                    event_type=event_type,
                    message=message,
                ),
            )
            message_item = QTableWidgetItem(message)
            message_item.setForeground(self._status_text_color(status, event_type, message))
            self._table.setItem(row_idx, 5, message_item)

    def _build_status_badge(self, status: str, event_type: str, message: str) -> QWidget:
        """Create visual badge widget based on status severity.

        Args:
            status: Stored status value.
            event_type: Event type string.
            message: Event message string.

        Returns:
            Badge container widget.
        """
        label_text, background_color, text_color = self._status_badge_style(status, event_type, message)

        badge = QLabel(label_text)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {background_color};
                color: {text_color};
                border-radius: 12px;
                padding: 4px 12px;
                font-weight: bold;
            }}
            """
        )

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.addWidget(badge)
        layout.setAlignment(Qt.AlignCenter)
        return container

    def _status_text_color(self, status: str, event_type: str, message: str) -> QColor:
        """Determine message text color from derived status bucket.

        Args:
            status: Stored status value.
            event_type: Event type string.
            message: Event message string.

        Returns:
            QColor used for message cell text.
        """
        label_text, _, _ = self._status_badge_style(status, event_type, message)
        if "SUCCESS" in label_text:
            return QColor("#4ade80")
        if "BLOCKED" in label_text:
            return QColor("#f87171")
        if "EXPIRED" in label_text:
            return QColor("#fbbf24")
        return QColor("#e0e0e0")

    @staticmethod
    def _status_badge_style(status: str, event_type: str, message: str) -> tuple[str, str, str]:
        """Map status text into badge label and color theme.

        Args:
            status: Stored status value.
            event_type: Event type string.
            message: Event message string.

        Returns:
            Tuple of label text, background color, and foreground color.
        """
        normalized_status = status.strip().lower()
        combined_text = f"{event_type} {message}".lower()

        if "expired" in combined_text:
            return "⏳ EXPIRED", "#f6ad55", "#1f2937"
        if normalized_status == "success":
            return "✅ SUCCESS", "#2f855a", "#ffffff"
        if normalized_status == "blocked":
            return "🛡️ BLOCKED", "#c53030", "#ffffff"
        if normalized_status == "warning":
            return "⚠️ WARNING", "#d69e2e", "#1f2937"
        if normalized_status == "error":
            return "❌ ERROR", "#742a2a", "#ffffff"
        return status.strip().upper() or "UNKNOWN", "#718096", "#ffffff"
