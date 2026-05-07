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

        # Stats Row
        self.stats_layout = QHBoxLayout()
        self.lbl_total = self._create_stat_card("Recent Events", "0", "#00FF41")
        self.lbl_today = self._create_stat_card("Today", "0", "#00FF41")
        self.lbl_blocked = self._create_stat_card("Blocked", "0", "#FF0000")
        self.lbl_errors = self._create_stat_card("Errors", "0", "#FF0000")
        
        layout.addLayout(self.stats_layout)

        button_row = QHBoxLayout()
        refresh_button = QPushButton("Refresh Logs")
        refresh_button.clicked.connect(self.refresh_logs)
        button_row.addStretch()
        button_row.addWidget(refresh_button)

        layout.addLayout(button_row)
        layout.addWidget(self._table)

    def _create_stat_card(self, title: str, value: str, color: str) -> QLabel:
        card = QWidget()
        card.setObjectName("panel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        
        t_label = QLabel(title)
        t_label.setStyleSheet("color: #008F11; font-size: 14px; font-weight: bold;")
        t_label.setAlignment(Qt.AlignCenter)
        
        v_label = QLabel(value)
        v_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        v_label.setAlignment(Qt.AlignCenter)
        
        card_layout.addWidget(t_label)
        card_layout.addWidget(v_label)
        
        self.stats_layout.addWidget(card)
        return v_label
    def refresh_logs(self) -> None:
        """Reload recent audit logs into table view.

        Args:
            None.

        Returns:
            None.
        """
        logs = self._audit_log_repository.get_recent_logs(limit=300)
        
        import datetime
        today_str = datetime.date.today().isoformat()
        
        total = len(logs)
        today_count = sum(1 for row in logs if str(row.get("created_at", "")).startswith(today_str))
        blocked = sum(1 for row in logs if str(row.get("status", "")).lower() == "blocked")
        errors = sum(1 for row in logs if str(row.get("status", "")).lower() == "error")
        
        self.lbl_total.setText(str(total))
        self.lbl_today.setText(str(today_count))
        self.lbl_blocked.setText(str(blocked))
        self.lbl_errors.setText(str(errors))

        self._table.setRowCount(len(logs))

        for row_idx, row in enumerate(logs):
            event_type = str(row["event_type"])
            status = str(row["status"])
            message = str(row["message"])

            self._table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self._table.setItem(row_idx, 1, QTableWidgetItem(str(row["created_at"])))
            self._table.setItem(row_idx, 2, QTableWidgetItem(event_type))
            self._table.setItem(row_idx, 3, QTableWidgetItem(str(row["actor"])))
            label_text, _, text_color = self._status_badge_style(status, event_type, message)
            status_item = QTableWidgetItem(label_text)
            status_item.setForeground(QColor(text_color))
            status_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row_idx, 4, status_item)

            message_item = QTableWidgetItem(message)
            message_item.setForeground(self._status_text_color(status, event_type, message))
            self._table.setItem(row_idx, 5, message_item)

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
            return QColor("#00FF41")
        if "BLOCKED" in label_text:
            return QColor("#FF0000")
        if "EXPIRED" in label_text:
            return QColor("#FFFF00")
        return QColor("#00FF41")

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
            return "[ EXPIRED ]", "#000000", "#FFFF00"
        if normalized_status == "success":
            return "[ SUCCESS ]", "#000000", "#00FF41"
        if normalized_status == "blocked":
            return "[ BLOCKED ]", "#000000", "#FF0000"
        if normalized_status == "warning":
            return "[ WARNING ]", "#000000", "#FFFF00"
        if normalized_status == "error":
            return "[ ERROR ]", "#330000", "#FF0000"
        return f"[ {status.strip().upper() or 'UNKNOWN'} ]", "#000000", "#00FF41"
