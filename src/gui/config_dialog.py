from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QCheckBox, QDialogButtonBox, QFileDialog, QHBoxLayout,
                               QPushButton, QWidget, QSpinBox, QComboBox)
from core import config
import os

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global Configuration")
        self.resize(550, 420)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.xtb_bin_edit = QLineEdit(config.get("XTB_BIN", "xtb"))
        self.xtb_param_dir_edit = QLineEdit(config.get("XTB_PARAM_DIR", ""))
        self.uma_param_edit = QLineEdit(config.get("UMA_PARAM_PATH", "uma-s-1p1.pt"))
        self.uma_gpu_cb = QCheckBox("Use GPU for UMA (Auto-fallback to CPU)")
        self.uma_gpu_cb.setChecked(config.get("UMA_USE_GPU", False))
        
        max_cpus = os.cpu_count() or 16
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, max_cpus * 4)
        self.threads_spin.setValue(int(config.get("NUM_THREADS", 1)))
        self.threads_spin.setToolTip("Sets OMP_NUM_THREADS (and MKL_NUM_THREADS for xTB)")

        self.memory_combo = QComboBox()
        self.memory_combo.setEditable(True)
        mem_items = ["250M", "500M", "1G", "2G", "4G", "8G", "16G", "32G"]
        self.memory_combo.addItems(mem_items)
        current_mem = str(config.get("MEMORY_PER_THREAD", "500M"))
        if current_mem not in mem_items:
            self.memory_combo.addItem(current_mem)
        self.memory_combo.setCurrentText(current_mem)
        self.memory_combo.setToolTip("Sets OMP_STACKSIZE per thread (e.g. 500M, 1G)")

        self.keep_log_combo = QComboBox()
        self.keep_log_combo.addItem("When fail (Keep on error only)", 1)
        self.keep_log_combo.addItem("Always (Never delete temp files)", 2)
        self.keep_log_combo.addItem("Never (Always delete temp files)", 0)
        curr_keep = int(config.get("KEEP_LOG", 1))
        idx = self.keep_log_combo.findData(curr_keep)
        if idx >= 0:
            self.keep_log_combo.setCurrentIndex(idx)
        self.keep_log_combo.setToolTip("Whether to keep intermediate calculation logs in temporary folder")
        
        self.xtb_bin_edit.textChanged.connect(self.auto_update_param_dir)
        
        form_layout.addRow("XTB_BIN path", self._with_browse(self.xtb_bin_edit, True))
        form_layout.addRow("XTB_PARAM_DIR", self._with_browse(self.xtb_param_dir_edit, False))
        form_layout.addRow("UMA parameter file", self._with_browse(self.uma_param_edit, True))
        form_layout.addRow("GPU", self.uma_gpu_cb)
        form_layout.addRow("CPUs (OMP_NUM_THREADS)", self.threads_spin)
        form_layout.addRow("Memory / CPU (OMP_STACKSIZE)", self.memory_combo)
        form_layout.addRow("Keep Log Files", self.keep_log_combo)
        
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
        if bin_path.parent.name.lower() == 'bin' and not self.xtb_param_dir_edit.text().strip():
            param_dir = bin_path.parent.parent / "share" / "xtb"
            self.xtb_param_dir_edit.setText(str(param_dir))

    def save_and_close(self):
        new_settings = {
            "XTB_BIN": self.xtb_bin_edit.text().strip(),
            "XTB_PARAM_DIR": self.xtb_param_dir_edit.text().strip(),
            "UMA_PARAM_PATH": self.uma_param_edit.text().strip(),
            "UMA_USE_GPU": self.uma_gpu_cb.isChecked(),
            "NUM_THREADS": self.threads_spin.value(),
            "MEMORY_PER_THREAD": self.memory_combo.currentText().strip(),
            "KEEP_LOG": self.keep_log_combo.currentData()
        }
        config.save_config(new_settings)
        self.accept()
