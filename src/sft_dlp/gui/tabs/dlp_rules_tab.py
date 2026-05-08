from __future__ import annotations

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sft_dlp.db.repositories import DlpRuleRepository


class DlpRulesTab(QWidget):
    """GUI tab for creating and viewing active DLP rules."""

    def __init__(self, dlp_rule_repository: DlpRuleRepository, parent: QWidget | None = None) -> None:
        """Initialize DLP rule management widgets.

        Args:
            dlp_rule_repository: Repository for rule CRUD operations.
            parent: Optional Qt parent widget.

        Returns:
            None.
        """
        super().__init__(parent)
        self._dlp_rule_repository = dlp_rule_repository

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Unique rule name")
        self._type_combo = QComboBox()
        self._type_combo.addItems(["pattern", "file_type", "recipient"])
        self._expression_edit = QLineEdit()
        self._expression_edit.setPlaceholderText("Regex, file extension, or recipient pattern")
        self._action_combo = QComboBox()
        self._action_combo.addItems(["allow", "warn", "block"])
        self._severity_combo = QComboBox()
        self._severity_combo.addItems(["low", "medium", "high", "critical"])
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Name", "Type", "Expression", "Action", "Severity"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)

        self._build_ui()
        self._refresh_rules()

    def _build_ui(self) -> None:
        """Build DLP tab layout and wire interactions.

        Args:
            None.

        Returns:
            None.
        """
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(50, 30, 50, 30)
        outer_layout.setSpacing(18)

        container = QWidget()
        container.setObjectName("panel")
        
        form_layout = QGridLayout(container)
        form_layout.setContentsMargins(30, 26, 30, 26)
        form_layout.setSpacing(14)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(3, 1)

        title = QLabel("Manage DLP Rules")
        title.setStyleSheet("font-size: 21px; font-weight: bold; color: #ffffff;")
        form_layout.addWidget(title, 0, 0, 1, 4)

        form_layout.addWidget(QLabel("Rule Name"), 1, 0)
        form_layout.addWidget(self._name_edit, 1, 1)

        form_layout.addWidget(QLabel("Rule Type"), 1, 2)
        form_layout.addWidget(self._type_combo, 1, 3)

        form_layout.addWidget(QLabel("Match Expression"), 2, 0)
        form_layout.addWidget(self._expression_edit, 2, 1, 1, 3)

        form_layout.addWidget(QLabel("Action"), 3, 0)
        form_layout.addWidget(self._action_combo, 3, 1)

        form_layout.addWidget(QLabel("Severity"), 3, 2)
        form_layout.addWidget(self._severity_combo, 3, 3)

        button_row = QHBoxLayout()
        add_button = QPushButton("➕ Add Rule")
        add_button.clicked.connect(self._create_rule)
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.clicked.connect(self._refresh_rules)
        delete_button = QPushButton("🗑️ Delete Selected Rule")
        delete_button.clicked.connect(self._delete_selected_rule)
        button_row.addWidget(add_button)
        button_row.addWidget(refresh_button)
        button_row.addWidget(delete_button)

        outer_layout.addWidget(container)
        outer_layout.addLayout(button_row)
        outer_layout.addWidget(self._table)

    def _create_rule(self) -> None:
        """Validate form inputs and create a new DLP rule.

        Args:
            None.

        Returns:
            None.
        """
        rule_name = self._name_edit.text().strip()
        expression = self._expression_edit.text().strip()

        if not rule_name or not expression:
            QMessageBox.warning(self, "Missing Input", "Rule name and expression are required.")
            return

        try:
            self._dlp_rule_repository.create_rule(
                rule_name=rule_name,
                rule_type=self._type_combo.currentText(),
                match_expression=expression,
                action=self._action_combo.currentText(),
                severity=self._severity_combo.currentText(),
                enabled=True,
            )
            self._name_edit.clear()
            self._expression_edit.clear()
            self._refresh_rules()
            QMessageBox.information(self, "Success", "DLP rule added.")
        except Exception as exc:
            QMessageBox.critical(self, "Rule Error", str(exc))

    def _refresh_rules(self) -> None:
        """Reload enabled DLP rules into the table view.

        Args:
            None.

        Returns:
            None.
        """
        rules = self._dlp_rule_repository.get_enabled_rules()
        self._table.setRowCount(len(rules))

        for row_index, rule in enumerate(rules):
            self._table.setItem(row_index, 0, QTableWidgetItem(str(rule.rule_id)))
            self._table.setItem(row_index, 1, QTableWidgetItem(rule.rule_name))
            self._table.setItem(row_index, 2, QTableWidgetItem(rule.rule_type))
            self._table.setItem(row_index, 3, QTableWidgetItem(rule.match_expression))
            self._table.setItem(row_index, 4, QTableWidgetItem(rule.action))
            self._table.setItem(row_index, 5, QTableWidgetItem(rule.severity))

    def _delete_selected_rule(self) -> None:
        """Delete the currently selected rule row after confirmation."""
        selected_row = self._table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Select a rule to delete.")
            return

        rule_id_item = self._table.item(selected_row, 0)
        rule_name_item = self._table.item(selected_row, 1)
        if rule_id_item is None or rule_name_item is None:
            QMessageBox.warning(self, "Selection Error", "Unable to read the selected rule.")
            return

        rule_id = int(rule_id_item.text())
        rule_name = rule_name_item.text()

        confirmation = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete selected rule '{rule_name}' (ID: {rule_id})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirmation != QMessageBox.Yes:
            return

        try:
            result = self._dlp_rule_repository.delete_rule(rule_id)
            if result == "not_found":
                QMessageBox.warning(self, "Not Found", "The selected rule no longer exists.")
                self._refresh_rules()
                return
            self._refresh_rules()
            if result == "deactivated":
                QMessageBox.information(
                    self,
                    "Rule Disabled",
                    "Rule is referenced by past events, so it was disabled instead of deleted.",
                )
                return
            QMessageBox.information(self, "Rule Deleted", "Selected rule deleted successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Delete Error", str(exc))
