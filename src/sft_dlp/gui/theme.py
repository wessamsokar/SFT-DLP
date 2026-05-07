from __future__ import annotations

MODERN_DARK_QSS = """
/* Hacker / Cybersecurity Theme */
QWidget {
    background-color: #050505;
    color: #00FF41;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 14px;
}

/* Sidebar */
#sidebar {
    background-color: #000000;
    border-right: 1px solid #00FF41;
}

#appTitle {
    color: #00FF41;
    font-size: 26px;
    font-weight: bold;
    padding: 20px 20px;
    letter-spacing: 2px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #008F11;
    text-align: left;
    padding: 14px 20px;
    border: none;
    font-weight: bold;
    font-size: 16px;
    margin: 4px 16px;
    border-radius: 0px;
}

#sidebar QPushButton:hover {
    background-color: #002200;
    color: #00FF41;
    border-left: 2px solid #00FF41;
}

#sidebar QPushButton:checked {
    background-color: #003300;
    color: #00FF41;
    border-left: 4px solid #00FF41;
}

/* Cards/Panels */
QWidget#panel {
    background-color: #0A0A0A;
    border: 1px solid #008F11;
    border-radius: 0px;
}

/* Typography */
QLabel#tabTitle {
    color: #00FF41;
    font-size: 22px;
    font-weight: bold;
    background: transparent;
    border: none;
    border-bottom: 1px dashed #008F11;
    padding-bottom: 8px;
}

QLabel {
    color: #008F11;
    font-weight: bold;
    background: transparent;
    border: none;
}

/* Inputs */
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #000000;
    border: 1px solid #008F11;
    border-radius: 0px;
    padding: 10px 14px;
    color: #00FF41;
    selection-background-color: #00FF41;
    selection-color: #000000;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #00FF41;
    background-color: #050505;
}

/* Buttons */
QPushButton {
    background-color: #000000;
    color: #00FF41;
    border-radius: 0px;
    padding: 10px 20px;
    font-weight: bold;
    border: 1px solid #008F11;
}

QPushButton:hover {
    background-color: #002200;
    border: 1px solid #00FF41;
}

QPushButton:pressed {
    background-color: #00FF41;
    color: #000000;
}

QPushButton#primaryBtn {
    background-color: #003300;
    color: #00FF41;
    border: 1px solid #00FF41;
    font-size: 16px;
    padding: 14px 20px;
    text-transform: uppercase;
}

QPushButton#primaryBtn:hover {
    background-color: #00FF41;
    color: #000000;
}

QPushButton#dangerBtn {
    background-color: #330000;
    color: #FF0000;
    border: 1px solid #FF0000;
}
QPushButton#dangerBtn:hover {
    background-color: #FF0000;
    color: #000000;
}

/* Tables */
QTableWidget {
    background-color: #000000;
    alternate-background-color: #0A0A0A;
    border: 1px solid #008F11;
    border-radius: 0px;
    gridline-color: #008F11;
    selection-background-color: #00FF41;
    selection-color: #000000;
    color: #00FF41;
}
QTableView::item {
    padding: 8px;
}
QHeaderView::section {
    background-color: #002200;
    color: #00FF41;
    padding: 10px;
    border: 1px solid #008F11;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 12px;
}
QHeaderView {
    background-color: #000000;
}
"""
