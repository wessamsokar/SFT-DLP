from __future__ import annotations

# Global modern dark theme stylesheet
MODERN_DARK_QSS = """
/* Global Styles */
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
    font-size: 17px;
}

QLabel {
    font-size: 17px;
}

QToolTip {
    background-color: #262626;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 15px;
}

QLabel#appTitle {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    padding: 14px 24px;
}

/* Sidebar Styles */
#sidebar {
    background-color: #1a1a1a;
    border-right: 1px solid #2d2d2d;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #a0a0a0;
    text-align: left;
    padding: 16px 24px;
    border: none;
    font-size: 17px;
    font-weight: 500;
    border-radius: 8px;
    margin: 4px 8px;
    min-height: 44px;
}

#sidebar QPushButton:hover {
    background-color: #2a2a2a;
    color: #ffffff;
}

#sidebar QPushButton:checked {
    background-color: #333333;
    color: #ffffff;
    font-weight: 600;
    border-left: 4px solid #4ade80; /* Vibrant green accent */
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
}

/* Inputs and Text Areas */
QLineEdit, QTextEdit {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 12px 16px;
    min-height: 38px;
}

QComboBox, QSpinBox {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 10px 14px;
    min-height: 38px;
}

QTextEdit {
    line-height: 1.35;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #4ade80;
    background-color: #242424;
}

/* General Buttons */
QPushButton {
    background-color: #2563eb; /* Primary vibrant blue */
    color: white;
    border: none;
    border-radius: 6px;
    padding: 12px 20px;
    min-height: 40px;
    font-weight: 600;
    font-size: 17px;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton#danger_btn {
    background-color: #dc2626;
}

QPushButton#danger_btn:hover {
    background-color: #b91c1c;
}

QWidget#panel {
    background-color: #181818;
    border-radius: 12px;
    border: 1px solid #2d2d2d;
}

/* Tables */
QTableWidget {
    background-color: #181818;
    color: #e0e0e0;
    gridline-color: #2d2d2d;
    border: 1px solid #2d2d2d;
    border-radius: 8px;
    selection-background-color: #262626;
    selection-color: #ffffff;
    alternate-background-color: #1e1e1e;
    font-size: 16px;
}

QTableView::item {
    padding: 6px 10px;
}

QHeaderView::section {
    background-color: #222222;
    color: #a0a0a0;
    padding: 12px;
    border: none;
    border-bottom: 1px solid #333333;
    border-right: 1px solid #333333;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 14px;
}

QHeaderView {
    background-color: #222222;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

/* Dialogs and message popups */
QMessageBox {
    background-color: #1a1a1a;
    border: 1px solid #2f2f2f;
    border-radius: 10px;
}

QMessageBox QWidget {
    background-color: #1a1a1a;
}

QMessageBox QLabel#qt_msgbox_label {
    color: #f3f4f6;
    font-size: 16px;
    padding: 8px 8px 8px 8px;
    min-width: 420px;
    qproperty-wordWrap: true;
    qproperty-alignment: 'AlignVCenter | AlignLeft';
}

QMessageBox QLabel#qt_msgboxex_icon_label {
    background: transparent;
    min-width: 48px;
    max-width: 56px;
    min-height: 42px;
}

QMessageBox QPushButton {
    min-width: 108px;
    min-height: 34px;
    font-size: 15px;
    border-radius: 8px;
    padding: 6px 14px;
    margin: 4px 2px 2px 2px;
}

QScrollBar:vertical {
    background: #181818;
    width: 15px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #404040;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
