import matplotlib
matplotlib.use('QtAgg')
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSpinBox, QSlider, QCheckBox, QFileDialog, 
                               QMessageBox, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QFrame, QGroupBox, QDialog)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from core import xyzutils

class TableDataDialog(QDialog):
    def __init__(self, parent=None, csv_rows=None, title="Scan Table Data"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(750, 450)
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        if csv_rows and len(csv_rows) > 0:
            header = None
            data_rows = []
            for row in csv_rows:
                if not row:
                    continue
                if row[0].startswith('#') or row[0] in ['1d', '2d', 'concerted']:
                    if 'E (au)' in row or 'rel. E' in str(row) or 'step' in str(row).lower() or 'saddle' in str(row).lower():
                        header = ["Step" if c.strip() == '#' else c.strip() for c in row]
                    continue
                data_rows.append(row)
                
            if not header and len(data_rows) > 0:
                header = [f"Col {i+1}" for i in range(len(data_rows[0]))]
                
            if header:
                self.table.setColumnCount(len(header))
                self.table.setHorizontalHeaderLabels(header)
            elif len(data_rows) > 0:
                self.table.setColumnCount(len(data_rows[0]))
                
            self.table.setRowCount(len(data_rows))
            for r_idx, row in enumerate(data_rows):
                for c_idx, val in enumerate(row):
                    if c_idx < self.table.columnCount():
                        item = QTableWidgetItem(str(val))
                        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                        self.table.setItem(r_idx, c_idx, item)
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            layout.addWidget(QLabel("No table data available."))
            
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)

class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewer = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Top chart area gets stretch ratio 3 so it's not overly tall
        chart_layout = QVBoxLayout()
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        self.layout.addLayout(chart_layout, 3)

        # Divider line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)

        # Bottom Interface Area (gets stretch ratio 0)
        controls_group = QWidget()
        group_layout = QVBoxLayout(controls_group)

        # Row 1: Step slider and animation
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Step:"))
        
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 1)
        self.step_spin.setFixedWidth(70)
        row1.addWidget(self.step_spin)

        self.step_slider = QSlider(Qt.Orientation.Horizontal)
        self.step_slider.setRange(1, 1)
        row1.addWidget(self.step_slider)

        self.btn_animate = QPushButton("Stop Animate")
        self.btn_animate.setFixedWidth(110)
        row1.addWidget(self.btn_animate)

        self.btn_save_xyz = QPushButton("Save Step XYZ...")
        self.btn_save_xyz.setFixedWidth(120)
        row1.addWidget(self.btn_save_xyz)
        group_layout.addLayout(row1)

        # Row 2: Annotations & Table
        row2 = QHBoxLayout()
        self.cb_annotation = QCheckBox("Show Annotations")
        self.cb_annotation.setChecked(True)
        row2.addWidget(self.cb_annotation)

        row2.addStretch()

        self.btn_show_table = QPushButton("Show Table Data...")
        self.btn_show_table.setFixedWidth(140)
        row2.addWidget(self.btn_show_table)
        group_layout.addLayout(row2)

        self.layout.addWidget(controls_group, 0)

        # Internal state
        self.energies = []
        self.saddle_flags = []
        self.csv_rows = []
        self.trajectory_xyz_str = ""
        self.result_file_path = None
        self.step_numbers = []
        self.current_step = 1
        self.is_animating = True
        self.atoms = []
        self.coords_list = []

        # Connect signals
        self.step_spin.valueChanged.connect(self._on_step_spin_changed)
        self.step_slider.valueChanged.connect(self._on_step_slider_changed)
        self.btn_animate.clicked.connect(self._toggle_animation)
        self.btn_save_xyz.clicked.connect(self._save_step_xyz)
        self.cb_annotation.toggled.connect(lambda _: self._draw_plot())
        self.btn_show_table.clicked.connect(self._show_table_data)

    def set_viewer(self, viewer):
        self.viewer = viewer

    def set_result_data(self, energies, saddle_flags, csv_rows, trajectory_xyz_str, result_file_path):
        self.energies = energies or []
        self.saddle_flags = saddle_flags or []
        self.csv_rows = csv_rows or []
        self.trajectory_xyz_str = trajectory_xyz_str or ""
        self.result_file_path = Path(result_file_path) if result_file_path else None

        # Parse frames from trajectory_xyz_str if possible
        self.atoms = []
        self.coords_list = []
        if self.trajectory_xyz_str:
            try:
                lines = self.trajectory_xyz_str.strip().splitlines()
                if lines and lines[0].strip().isdigit():
                    idx = 0
                    while idx < len(lines):
                        if not lines[idx].strip():
                            idx += 1
                            continue
                        n_atoms = int(lines[idx].strip())
                        frame_atoms = []
                        frame_coords = []
                        for line in lines[idx+2 : idx+2+n_atoms]:
                            parts = line.strip().split()
                            if len(parts) >= 4:
                                frame_atoms.append(parts[0].capitalize())
                                frame_coords.append([float(parts[1]), float(parts[2]), float(parts[3])])
                        if frame_coords:
                            if not len(self.atoms):
                                self.atoms = np.array(frame_atoms)
                            self.coords_list.append(np.array(frame_coords, dtype=float))
                        idx += 2 + n_atoms
            except Exception as e:
                print(f"Failed to parse trajectory frames: {e}")

        num_steps = max(len(self.energies), len(self.coords_list), 1)
        
        self.step_spin.blockSignals(True)
        self.step_slider.blockSignals(True)
        self.step_spin.setRange(1, num_steps)
        self.step_slider.setRange(1, num_steps)
        self.step_spin.setValue(1)
        self.step_slider.setValue(1)
        self.step_spin.blockSignals(False)
        self.step_slider.blockSignals(False)

        self.current_step = 1
        self.is_animating = False
        self.btn_animate.setText("Start Animate")
        if self.viewer:
            self.viewer.set_frame(0)

        # Parse step numbers from CSV rows if available
        self.step_numbers = []
        data_rows = [r for r in self.csv_rows if r and not r[0].startswith('#') and r[0] not in ['1d', '2d', 'concerted']]
        if len(data_rows) == len(self.energies):
            for r in data_rows:
                try:
                    self.step_numbers.append(int(float(r[0])))
                except:
                    pass
        if len(self.step_numbers) != len(self.energies):
            self.step_numbers = list(range(1, len(self.energies) + 1))

        self._draw_plot()

    def _on_step_spin_changed(self, val):
        self.step_slider.blockSignals(True)
        self.step_slider.setValue(val)
        self.step_slider.blockSignals(False)
        self._select_step(val)

    def _on_step_slider_changed(self, val):
        self.step_spin.blockSignals(True)
        self.step_spin.setValue(val)
        self.step_spin.blockSignals(False)
        self._select_step(val)

    def _select_step(self, step_num):
        self.current_step = step_num
        if self.is_animating:
            self.is_animating = False
            self.btn_animate.setText("Start Animate")
            if self.viewer:
                self.viewer.stop_animate()
        if self.viewer:
            self.viewer.set_frame(step_num - 1)
        self._draw_plot()

    def _toggle_animation(self):
        if not self.viewer:
            return
        if self.is_animating:
            self.viewer.stop_animate()
            self.is_animating = False
            self.btn_animate.setText("Start Animate")
        else:
            self.viewer.start_animate()
            self.is_animating = True
            self.btn_animate.setText("Stop Animate")

    def _save_step_xyz(self):
        idx = self.step_spin.value() - 1
        if not self.coords_list or idx >= len(self.coords_list):
            QMessageBox.warning(self, "Warning", "No 3D structure coordinates available for this step.")
            return

        default_dir = self.result_file_path.parent if self.result_file_path else Path.cwd()
        default_stem = self.result_file_path.stem if self.result_file_path else "structure"
        default_name = f"{default_stem}_frame{self.step_spin.value():03d}.xyz"
        default_path = str(default_dir / default_name)

        dest_path, _ = QFileDialog.getSaveFileName(self, "Save Step XYZ", default_path, "XYZ Files (*.xyz);;All Files (*)")
        if dest_path:
            try:
                xyzutils.save_xyz_file(dest_path, self.atoms, self.coords_list[idx], title=f"Step {self.step_spin.value()}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save structure: {e}")

    def _show_table_data(self):
        dlg = TableDataDialog(self, self.csv_rows, title=f"Table Data - {self.result_file_path.name if self.result_file_path else ''}")
        dlg.exec()

    def plot_energy(self, energies, title="Scan Energy Profile", xlabel="Step", ylabel="Relative Energy (kcal/mol)"):
        self.energies = energies
        self._draw_plot()

    def _draw_plot(self):
        if not hasattr(self, 'energies') or not self.energies:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        x_vals = self.step_numbers if hasattr(self, 'step_numbers') and len(self.step_numbers) == len(self.energies) else list(range(1, len(self.energies) + 1))
        
        # Base plot
        ax.plot(x_vals, self.energies, marker='o', color='#1f77b4', label='Energy', zorder=2)
        
        # Annotations mode
        if hasattr(self, 'cb_annotation') and self.cb_annotation.isChecked():
            # Write Step number above each point
            for x, y in zip(x_vals, self.energies):
                ax.annotate(str(x), (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, color='#333333', zorder=4)
            
            # Highlight saddle points in RED
            if hasattr(self, 'saddle_flags') and self.saddle_flags and len(self.saddle_flags) == len(self.energies):
                saddle_x = [x for x, s in zip(x_vals, self.saddle_flags) if s]
                saddle_y = [y for y, s in zip(self.energies, self.saddle_flags) if s]
                if saddle_x:
                    ax.scatter(saddle_x, saddle_y, color='red', s=70, zorder=5, label='Saddle Point')
                    
        # Highlight currently selected step
        if hasattr(self, 'current_step') and hasattr(self, 'step_numbers'):
            if self.current_step in x_vals:
                idx = x_vals.index(self.current_step)
                ax.scatter([x_vals[idx]], [self.energies[idx]], color='orange', s=100, edgecolor='black', zorder=6, label=f'Current (Step {self.current_step})')
            elif 1 <= self.current_step <= len(x_vals):
                idx = self.current_step - 1
                ax.scatter([x_vals[idx]], [self.energies[idx]], color='orange', s=100, edgecolor='black', zorder=6, label=f'Current (Step {x_vals[idx]})')
            
        ax.set_title("Scan Energy Profile", fontsize=12, fontweight='bold')
        ax.set_xlabel("Step", fontsize=10)
        ax.set_ylabel("Relative Energy (kcal/mol)", fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.5)
        if hasattr(self, 'cb_annotation') and self.cb_annotation.isChecked() and hasattr(self, 'saddle_flags') and any(self.saddle_flags):
            ax.legend(loc='best')
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_2d_scan(self, x_vals, y_vals, z_vals, title="2D Scan Energy Surface", xlabel="X", ylabel="Y", zlabel="Relative Energy (kcal/mol)"):
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        ax.plot_trisurf(x_vals, y_vals, z_vals, cmap='viridis', edgecolor='none')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_zlabel(zlabel)
        self.figure.tight_layout()
        self.canvas.draw()
