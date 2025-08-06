import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class FolderSearchThread(QThread):
    progress_update = pyqtSignal(int)
    result_found = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path, password):
        super().__init__()
        self.folder_path = folder_path
        self.password = password
        self._is_running = True

    def run(self):
        found_any = False  # dodaj ovo
        try:
            txt_files = []
            for root, _, files in os.walk(self.folder_path):
                for file in files:
                    if file.lower().endswith('.txt'):
                        txt_files.append(os.path.join(root, file))

            total_files = len(txt_files)
            if total_files == 0:
                self.result_found.emit("No .txt files found in the selected folder.")
                self.finished.emit()
                return

            for idx, filepath in enumerate(txt_files):
                if not self._is_running:
                    break
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, start=1):
                            if not self._is_running:
                                break
                            if self.password in line:
                                found_any = True  # setujemo da je nesto pronadjeno
                                msg = f"Found '{self.password}' in:\nFile: {filepath}\nLine: {line_num}\nText: {line.strip()}"
                                self.result_found.emit(msg)
                except Exception as e:
                    self.result_found.emit(f"Error reading {filepath}: {str(e)}")

                progress_percent = int(((idx + 1) / total_files) * 100)
                self.progress_update.emit(progress_percent)

            if self._is_running:
                if found_any:
                    self.result_found.emit("Search finished. Password found at least once.")
                else:
                    self.result_found.emit("Search finished. Password NOT found in any file.")

        except Exception as e:
            self.result_found.emit(f"Unexpected error: {str(e)}")

        self.finished.emit()

    def stop(self):
        self._is_running = False


class PasswordFinderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Finder in Folder - PyQt6")
        self.setGeometry(300, 300, 600, 450)
        self.thread = None
        self.folder_path = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.label1 = QLabel("Enter the password (plain text) to find:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter exact password text")

        self.load_folder_btn = QPushButton("Select Folder")
        self.load_folder_btn.clicked.connect(self.select_folder)

        self.folder_label = QLabel("No folder selected")

        self.start_btn = QPushButton("Start Search")
        self.start_btn.clicked.connect(self.start_search)
        self.start_btn.setEnabled(False)

        self.stop_btn = QPushButton("Stop Search")
        self.stop_btn.clicked.connect(self.stop_search)
        self.stop_btn.setEnabled(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        layout.addWidget(self.label1)
        layout.addWidget(self.password_input)
        layout.addWidget(self.load_folder_btn)
        layout.addWidget(self.folder_label)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.result_text)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            self.folder_label.setText(f"Selected folder: {folder}")
            self.start_btn.setEnabled(True)

    def start_search(self):
        password = self.password_input.text().strip()
        if not password:
            QMessageBox.warning(self, "Input Error", "Please enter a password to find.")
            return
        if not self.folder_path:
            QMessageBox.warning(self, "Folder Error", "Please select a folder first.")
            return

        self.result_text.clear()
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.load_folder_btn.setEnabled(False)
        self.password_input.setEnabled(False)

        self.thread = FolderSearchThread(self.folder_path, password)
        self.thread.progress_update.connect(self.progress_bar.setValue)
        self.thread.result_found.connect(self.display_result)
        self.thread.finished.connect(self.finish_search)
        self.thread.start()

    def stop_search(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()
            self.result_text.append("Search stopped by user.")
            self.finish_search()

    def display_result(self, text):
        self.result_text.append(text + "\n")

    def finish_search(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.load_folder_btn.setEnabled(True)
        self.password_input.setEnabled(True)
        self.progress_bar.setValue(0)

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = PasswordFinderApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()