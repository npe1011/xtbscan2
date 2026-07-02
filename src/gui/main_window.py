import os
import sys
import json
import tempfile
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QSplitter, QFileDialog, QMessageBox, QTabWidget,
                               QPushButton, QLabel, QComboBox, QSpinBox, 
                               QDoubleSpinBox, QCheckBox, QTextEdit, QFormLayout,
                               QFrame, QLineEdit)
from PySide6.QtCore import Qt, QProcess

from gui.viewer3d import Viewer3D
from gui.tables import SettingsTablesWidget
from gui.config_dialog import ConfigDialog
from gui.plot_widget import PlotWidget
from core.parsers import parse_initial_structure
from core import xyzutils

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("xtbscan2 - GUI")
        self.resize(1200, 800)
        self.setAcceptDrops(True)
        
        self.current_input_file = None
        self.process = None
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Menus
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_init_action = file_menu.addAction("Open Initial Structure")
        open_init_action.triggered.connect(lambda: self.open_file_dialog("init"))
        
        open_res_action = file_menu.addAction("Open Result (XYZ/Log)")
        open_res_action.triggered.connect(lambda: self.open_file_dialog("result"))
        
        settings_menu = menubar.addMenu("Settings")
        config_action = settings_menu.addAction("Configuration")
        config_action.triggered.connect(self.open_config_dialog)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left Panel (Viewer)
        self.viewer_panel = Viewer3D()
        
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.file_path_label = QLabel("No file loaded")
        self.file_path_label.setStyleSheet("color: gray;")
        self.file_path_label.setWordWrap(True)
        left_layout.addWidget(self.file_path_label)
        left_layout.addWidget(self.viewer_panel)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        self.left_widget = left_widget
        splitter.addWidget(left_widget)
        
        # Right Panel (Settings & Log)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)
        
        # Tabs for settings
        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)
        
        # 1. Calculation & Scans Tab
        calc_tab = QWidget()
        calc_layout = QVBoxLayout(calc_tab)
        
        # Settings Form Layout
        settings_layout = QHBoxLayout()
        
        form1 = QFormLayout()
        self.job_name_edit = QLineEdit()
        form1.addRow("Job Name", self.job_name_edit)
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["xtb", "uma"])
        form1.addRow("Engine", self.engine_combo)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["gxtb", "gfn2", "gfn1", "gfn0", "gfnff"])
        form1.addRow("Method", self.method_combo)
        
        self.solvent_combo = QComboBox()
        from core.config import XTB_SOLVENT_LIST
        self.solvent_combo.addItems(["None"] + XTB_SOLVENT_LIST)
        form1.addRow("Solvent", self.solvent_combo)
        
        settings_layout.addLayout(form1)
        
        form2 = QFormLayout()
        self.charge_spin = QSpinBox()
        self.charge_spin.setRange(-10, 10)
        form2.addRow("Charge", self.charge_spin)
        
        self.mult_spin = QSpinBox()
        self.mult_spin.setRange(1, 10)
        form2.addRow("Multiplicity", self.mult_spin)
        
        self.concerted_cb = QCheckBox("Concerted Scan")
        self.concerted_cb.setToolTip("Perform concerted scan for multiple parameters with same step size")
        form2.addRow("", self.concerted_cb)
        
        settings_layout.addLayout(form2)
        calc_layout.addLayout(settings_layout)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        calc_layout.addWidget(line)
        
        # Connect signals for disabling logic
        self.engine_combo.currentTextChanged.connect(self.update_options_state)
        self.method_combo.currentTextChanged.connect(self.update_options_state)
        
        # Scans/Constrains Tables
        self.tables_widget = SettingsTablesWidget()
        calc_layout.addWidget(self.tables_widget)
        
        self.tabs.addTab(calc_tab, "Calculation")
        
        # 3. Log Output Tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        self.tabs.addTab(log_tab, "Log")
        
        # 4. Result Tab
        self.plot_widget = PlotWidget()
        self.tabs.addTab(self.plot_widget, "Result")
        
        # Control Buttons
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Calculation")
        self.run_btn.clicked.connect(self.run_calculation)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_calculation)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.stop_btn)
        right_layout.addLayout(btn_layout)
        
        splitter.setSizes([700, 500])
        self.update_options_state()

    def update_options_state(self):
        engine = self.engine_combo.currentText()
        if engine == "uma":
            self.method_combo.setEnabled(False)
            self.solvent_combo.setEnabled(False)
        else:
            self.method_combo.setEnabled(True)
            method = self.method_combo.currentText()
            if method in ["gxtb", "gfnff"]:
                self.solvent_combo.setEnabled(False)
                self.solvent_combo.setCurrentText("None")
            else:
                self.solvent_combo.setEnabled(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                if file_path.lower().endswith(".csv"):
                    self.load_result_file(file_path)
                else:
                    pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
                    if hasattr(self, 'left_widget') and pos.x() < self.left_widget.width():
                        self.load_input_file(file_path)
                    else:
                        self.load_result_file(file_path)
                break
                
    def open_file_dialog(self, ftype="init"):
        title = "Open Initial Structure" if ftype == "init" else "Open Result (XYZ/Log)"
        path, _ = QFileDialog.getOpenFileName(self, title, "", "All Files (*)")
        if path:
            if ftype == "init":
                self.load_input_file(path)
            else:
                self.load_result_file(path)
            
    def open_config_dialog(self):
        dlg = ConfigDialog(self)
        dlg.exec()

    def load_input_file(self, file_path):
        self.current_input_file = file_path
        self.file_path_label.setText(f"Initial: {file_path}")
        self.log_text.append(f"Loaded: {file_path}")
        if hasattr(self, 'job_name_edit'):
            self.job_name_edit.setText(f"{Path(file_path).stem}_scan")
        try:
            atoms, coords = parse_initial_structure(Path(file_path))
            xyz_str = xyzutils.get_xyz_string(atoms, coords)
            full_xyz = f"{len(atoms)}\n{Path(file_path).name}\n{xyz_str}"
            self.viewer_panel.load_xyz(full_xyz)
            self.tables_widget.set_structure(atoms, coords)
        except Exception as e:
            self.log_text.append(f"<span style='color:red'>Failed to load structure: {e}</span>")
            
    def load_result_file(self, file_path):
        self.file_path_label.setText(f"Result: {file_path}")
        self.log_text.append(f"Loaded result: {file_path}")
        try:
            fp = Path(file_path)
            xyz_path = None
            csv_path = None

            if fp.suffix.lower() == '.csv':
                csv_path = fp
                candidate_xyz = fp.with_suffix('.xyz')
                if candidate_xyz.exists():
                    xyz_path = candidate_xyz
            elif fp.suffix.lower() == '.xyz':
                xyz_path = fp
                candidate_csv = fp.with_suffix('.csv')
                if candidate_csv.exists():
                    csv_path = candidate_csv
            else:
                xyz_path = fp

            if xyz_path and xyz_path.exists():
                with open(xyz_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.viewer_panel.load_trajectory(data)
            elif fp.suffix.lower() != '.csv':
                with open(fp, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.viewer_panel.load_trajectory(data)

            energies = []
            if csv_path and csv_path.exists():
                import csv
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if not row or row[0].startswith('#') or row[0] in ['1d', '2d', 'concerted']:
                            continue
                        try:
                            if len(row) >= 5 and row[4].replace('.', '', 1).replace('-', '', 1).isdigit():
                                energies.append(float(row[4]))
                            elif len(row) >= 4:
                                energies.append(float(row[3]))
                        except:
                            pass
            elif xyz_path and xyz_path.exists():
                try:
                    atoms, coords, energies_arr = xyzutils.read_xtbscan_file(xyz_path)
                    if len(energies_arr) > 0:
                        from core.config import HARTREE_TO_KCAL
                        e0 = energies_arr[0]
                        energies = [(e - e0) * HARTREE_TO_KCAL for e in energies_arr]
                except Exception:
                    pass

            if len(energies) > 0:
                self.plot_widget.plot_energy(energies)
                self.tabs.setCurrentWidget(self.plot_widget)
        except Exception as e:
            self.log_text.append(f"<span style='color:red'>Failed to load result structure: {e}</span>")
        
    def run_calculation(self):
        if not self.current_input_file:
            QMessageBox.warning(self, "Warning", "No structure loaded.")
            return
            
        # Prepare job config
        solvent = self.solvent_combo.currentText()
        if solvent == "None" or not self.solvent_combo.isEnabled():
            solvent = None
            
        job_name = self.job_name_edit.text().strip()
        if not job_name:
            job_name = Path(self.current_input_file).stem + "_scan"
            
        job_data = {
            "engine": self.engine_combo.currentText(),
            "input_file": str(self.current_input_file),
            "job_name": job_name,
            "charge": self.charge_spin.value(),
            "mult": self.mult_spin.value(),
            "method": self.method_combo.currentText(),
            "solvent": solvent,
            "concerted": self.concerted_cb.isChecked(),
            "scans": self.tables_widget.get_scans(),
            "constrains": self.tables_widget.get_constrains()
        }
        
        # Write to temp json
        fd, json_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, 'w') as f:
            json.dump(job_data, f)
            
        # Start QProcess
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        self.log_text.clear()
        self.tabs.setCurrentIndex(2) # Switch to log tab
        
        # Command
        exe_path = sys.executable # Will use uv's python
        cli_script = Path(__file__).parent.parent / "cli.py"
        self.process.start(exe_path, [str(cli_script), json_path])
        
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
    def stop_calculation(self):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.log_text.append("\nCalculation stopped by user.")
            
    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self.log_text.append(data.strip())
        
    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        self.log_text.append(f"<span style='color:red'>{data.strip()}</span>")
        
    def process_finished(self, exit_code, exit_status):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_text.append(f"\nProcess finished with exit code {exit_code}")
        
        if exit_code == 0 and self.current_input_file:
            workdir = Path(self.current_input_file).parent
            job_name = self.job_name_edit.text().strip()
            if not job_name:
                job_name = Path(self.current_input_file).stem + "_scan"
            res_xyz = workdir / f"{job_name}.xyz"
            res_csv = workdir / f"{job_name}.csv"
            scan_log = workdir / "xtbscan.log"
            opt_xyz = workdir / "xtbopt.xyz"
            
            try:
                if res_xyz.exists():
                    self.load_result_file(str(res_xyz))
                elif res_csv.exists():
                    self.load_result_file(str(res_csv))
                elif scan_log.exists():
                    self.load_result_file(str(scan_log))
                elif opt_xyz.exists():
                    self.load_result_file(str(opt_xyz))
            except Exception as e:
                self.log_text.append(f"<span style='color:red'>Failed to load result structure: {e}</span>")
