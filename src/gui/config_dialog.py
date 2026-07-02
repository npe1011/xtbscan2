from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QCheckBox, QDialogButtonBox, QFileDialog, QHBoxLayout,
                               QPushButton, QWidget)
from core import config

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global Configuration")
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.xtb_bin_edit = QLineEdit(config.get("XTB_BIN", "xtb"))
        self.xtb_param_dir_edit = QLineEdit(config.get("XTB_PARAM_DIR", ""))
        self.uma_param_edit = QLineEdit(config.get("UMA_PARAM_PATH", "uma-s-1p1.pt"))
        self.uma_gpu_cb = QCheckBox("Use GPU for UMA")
        self.uma_gpu_cb.setChecked(config.get("UMA_USE_GPU", False))
        
        self.xtb_bin_edit.textChanged.connect(self.auto_update_param_dir)
        
        form_layout.addRow("XTB_BIN path", self._with_browse(self.xtb_bin_edit, True))
        form_layout.addRow("XTB_PARAM_DIR", self._with_browse(self.xtb_param_dir_edit, False))
        form_layout.addRow("UMA parameter file", self._with_browse(self.uma_param_edit, True))
        form_layout.addRow("GPU", self.uma_gpu_cb)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _with_browse(self, line_edit, is_file):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(line_edit)
        btn = QPushButton("Browse...")
        layout.addWidget(btn)
        
        def browse():
            if is_file:
                path, _ = QFileDialog.getOpenFileName(self, "Select File")
            else:
                path = QFileDialog.getExistingDirectory(self, "Select Directory")
            if path:
                line_edit.setText(path)
                
        btn.clicked.connect(browse)
        return widget
        
    def auto_update_param_dir(self, text):
        from pathlib import Path
        bin_path = Path(text)
        if bin_path.parent.name.lower() == 'bin':
            param_dir = bin_path.parent.parent / "share" / "xtb"
            self.xtb_param_dir_edit.setText(str(param_dir))

    def save_and_close(self):
        new_settings = {
            "XTB_BIN": self.xtb_bin_edit.text().strip(),
            "XTB_PARAM_DIR": self.xtb_param_dir_edit.text().strip(),
            "UMA_PARAM_PATH": self.uma_param_edit.text().strip(),
            "UMA_USE_GPU": self.uma_gpu_cb.isChecked()
        }
        config.save_config(new_settings)
        self.accept()
