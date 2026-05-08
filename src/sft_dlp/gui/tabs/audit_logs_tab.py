from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QHBoxLayout,
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
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Timestamp
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Event
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Actor
        header.setSectionResizeMode(4, QHeaderView.Fixed)             # Status
        header.setSectionResizeMode(5, QHeaderView.Stretch)           # Message
        self._table.setColumnWidth(4, 170)
        self._table.verticalHeader().setVisible(False)

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

        panel = QWidget()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(14)

        button_row = QHBoxLayout()
        refresh_button = QPushButton("Refresh Logs")
        refresh_button.clicked.connect(self.refresh_logs)
        button_row.addWidget(refresh_button)

        panel_layout.addLayout(button_row)
        panel_layout.addWidget(self._table)
        layout.addWidget(panel)

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
            status_label, background_color, text_color = self._status_badge_style(
                status=status,
                event_type=event_type,
                message=message,
            )
            status_item = QTableWidgetItem(status_label)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(text_color))
            status_item.setBackground(QColor(background_color))
            self._table.setItem(row_idx, 4, status_item)
            message_item = QTableWidgetItem(message)
            message_item.setForeground(self._status_text_color(status, event_type, message))
            self._table.setItem(row_idx, 5, message_item)
            self._table.setRowHeight(row_idx, 34)

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
            return "EXPIRED", "#7c4a03", "#fef3c7"
        if normalized_status == "success":
            return "SUCCESS", "#14532d", "#dcfce7"
        if normalized_status == "blocked":
            return "BLOCKED", "#7f1d1d", "#fee2e2"
        if normalized_status == "warning":
            return "WARNING", "#78350f", "#fef3c7"
        if normalized_status == "error":
            return "ERROR", "#7f1d1d", "#fee2e2"
        return status.strip().upper() or "UNKNOWN", "#334155", "#e2e8f0"

