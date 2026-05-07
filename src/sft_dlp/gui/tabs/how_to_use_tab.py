from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt

class HowToUseTab(QWidget):
    """Simple guide to help the user understand the app."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(20)

        container = QWidget()
        container.setObjectName("panel")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 34, 36, 34)
        layout.setSpacing(18)

        title = QLabel("SYSTEM MANUAL / HOW TO USE")
        title.setObjectName("tabTitle")
        
        instructions = (
            "Welcome to the Secure File Transfer & DLP System.\n\n"
            "This application helps you encrypt files securely and share them while ensuring "
            "no sensitive data is leaked.\n\n"
            "--- [ 1. ENCRYPTION ] ---\n"
            "> Select a file you want to encrypt.\n"
            "> Choose the destination folder to save the encrypted file.\n"
            "> Click 'Encrypt File'. The system uses military-grade AES-256 encryption.\n\n"
            "--- [ 2. SHARING & DLP ] ---\n"
            "> To share a file, go to 'Create Share Link' in the Sharing tab.\n"
            "> Select the file, enter the recipient's name, and set an expiration time.\n"
            "> The Data Leakage Prevention (DLP) Engine will scan the file first.\n"
            "> If it finds prohibited content (like credit cards or IDs), it BLOCKS the share.\n"
            "> If approved, you get a Secure Token to give to the recipient.\n"
            "> To open a shared file, the recipient enters the token in 'Access Share'.\n\n"
            "--- [ 3. DLP RULES ] ---\n"
            "> Here you can manage the security rules that block sensitive data.\n"
            "> You can block specific words, regex patterns, or entire file extensions.\n\n"
            "--- [ 4. AUDIT LOGS ] ---\n"
            "> Shows a complete history of all system events: encryptions, sharing, and DLP alerts."
        )
        
        content = QLabel(instructions)
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content.setStyleSheet("font-size: 16px; line-height: 1.6;")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        layout.addWidget(title)
        layout.addWidget(scroll)
        
        main_layout.addWidget(container)
