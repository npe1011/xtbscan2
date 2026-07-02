from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                               QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
                               QSpinBox, QDoubleSpinBox, QMessageBox)
from PySide6.QtCore import Qt
import numpy as np
import re
from core import xyzutils

class ScanDialog(QDialog):
    def __init__(self, parent=None, scan_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Scan")
        self.layout = QFormLayout(self)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["distance", "angle", "dihedral"])
        
        self.atoms_edit = QLineEdit()
        self.atoms_edit.setPlaceholderText("e.g. 1, 2")
        self.atoms_edit.setToolTip("1-based atom indices separated by commas")
        
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(-360, 1000)
        self.start_spin.setDecimals(3)
        
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(-360, 1000)
        self.end_spin.setDecimals(3)
        
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(2, 1000)
        self.steps_spin.setValue(10)
        
        self.current_atoms = None
        self.current_coords = None
        
        if scan_data:
            self.type_combo.setCurrentText(scan_data['type'])
            self.atoms_edit.setText(", ".join(map(str, [x + 1 for x in scan_data['atoms']])))
            self.start_spin.setValue(scan_data['start'])
            self.end_spin.setValue(scan_data['end'])
            self.steps_spin.setValue(scan_data['steps'])
            
        self.layout.addRow("Type", self.type_combo)
        self.layout.addRow("Atoms", self.atoms_edit)
        self.layout.addRow("Start", self.start_spin)
        self.layout.addRow("End", self.end_spin)
        self.layout.addRow("Steps", self.steps_spin)
        
        get_val_btn = QPushButton("Get Current Start Value")
        get_val_btn.clicked.connect(self.get_current_value)
        self.layout.addRow("", get_val_btn)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addRow(self.button_box)
        
    def set_structure(self, atoms, coords):
        self.current_atoms = atoms
        self.current_coords = coords

    def get_current_value(self):
        if self.current_coords is None:
            QMessageBox.warning(self, "Warning", "No structure loaded.")
            return
        
        atoms_str = self.atoms_edit.text()
        atoms = [int(x) - 1 for x in re.split(r'[,\s]+', atoms_str.strip()) if x.isdigit()]
        t = self.type_combo.currentText()
        try:
            if t == "distance" and len(atoms) == 2:
                val = xyzutils.calc_distance(self.current_coords, atoms)
                self.start_spin.setValue(val)
            elif t == "angle" and len(atoms) == 3:
                val = xyzutils.calc_angle(self.current_coords, atoms)
                self.start_spin.setValue(val)
            elif t == "dihedral" and len(atoms) == 4:
                val = xyzutils.calc_dihedral(self.current_coords, atoms)
                self.start_spin.setValue(val)
            else:
                QMessageBox.warning(self, "Warning", f"Invalid number of atoms for {t}.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to calculate: {e}")

    def get_data(self):
        atoms_str = self.atoms_edit.text()
        atoms = [int(x) - 1 for x in re.split(r'[,\s]+', atoms_str.strip()) if x.isdigit()]
        return {
            "type": self.type_combo.currentText(),
            "atoms": atoms,
            "start": self.start_spin.value(),
            "end": self.end_spin.value(),
            "steps": self.steps_spin.value()
        }

class ConstrainDialog(QDialog):
    def __init__(self, parent=None, constrain_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Constrain")
        self.layout = QFormLayout(self)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["distance", "angle", "dihedral"])
        
        self.atoms_edit = QLineEdit()
        self.atoms_edit.setPlaceholderText("e.g. 1, 2")
        self.atoms_edit.setToolTip("1-based atom indices separated by commas")
        
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setRange(-360, 1000)
        self.value_spin.setDecimals(3)
        self.value_spin.setSpecialValueText("Auto")
        self.value_spin.setValue(self.value_spin.minimum()) # Minimum implies auto in our logic
        
        self.current_atoms = None
        self.current_coords = None
        
        if constrain_data:
            self.type_combo.setCurrentText(constrain_data['type'])
            self.atoms_edit.setText(", ".join(map(str, [x + 1 for x in constrain_data['atoms']])))
            if constrain_data.get('value') is not None:
                self.value_spin.setValue(constrain_data['value'])
                
        self.layout.addRow("Type", self.type_combo)
        self.layout.addRow("Atoms", self.atoms_edit)
        self.layout.addRow("Value", self.value_spin)
        
        get_val_btn = QPushButton("Get Current Value")
        get_val_btn.clicked.connect(self.get_current_value)
        self.layout.addRow("", get_val_btn)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addRow(self.button_box)
        
    def set_structure(self, atoms, coords):
        self.current_atoms = atoms
        self.current_coords = coords

    def get_current_value(self):
        if self.current_coords is None:
            QMessageBox.warning(self, "Warning", "No structure loaded.")
            return
        
        atoms_str = self.atoms_edit.text()
        atoms = [int(x) - 1 for x in re.split(r'[,\s]+', atoms_str.strip()) if x.isdigit()]
        t = self.type_combo.currentText()
        try:
            if t == "distance" and len(atoms) == 2:
                val = xyzutils.calc_distance(self.current_coords, atoms)
                self.value_spin.setValue(val)
            elif t == "angle" and len(atoms) == 3:
                val = xyzutils.calc_angle(self.current_coords, atoms)
                self.value_spin.setValue(val)
            elif t == "dihedral" and len(atoms) == 4:
                val = xyzutils.calc_dihedral(self.current_coords, atoms)
                self.value_spin.setValue(val)
            else:
                QMessageBox.warning(self, "Warning", f"Invalid number of atoms for {t}.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to calculate: {e}")
            
    def get_data(self):
        atoms_str = self.atoms_edit.text()
        atoms = [int(x) - 1 for x in re.split(r'[,\s]+', atoms_str.strip()) if x.isdigit()]
        val = self.value_spin.value()
        if val == self.value_spin.minimum():
            val = None
        return {
            "type": self.type_combo.currentText(),
            "atoms": atoms,
            "value": val
        }

class SettingsTablesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Scans Table
        self.scans_table = QTableWidget(0, 5)
        self.scans_table.setHorizontalHeaderLabels(["Type", "Atoms", "Start", "End", "Steps"])
        self.scans_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.scans_table.setMaximumHeight(150)
        self.scans_table.doubleClicked.connect(self.edit_scan)
        
        btn_layout1 = QHBoxLayout()
        add_scan_btn = QPushButton("Add Scan")
        del_scan_btn = QPushButton("Delete Scan")
        add_scan_btn.clicked.connect(self.add_scan)
        del_scan_btn.clicked.connect(self.delete_scan)
        btn_layout1.addWidget(add_scan_btn)
        btn_layout1.addWidget(del_scan_btn)
        
        layout.addWidget(self.scans_table)
        layout.addLayout(btn_layout1)
        
        # Constrains Table
        self.constrains_table = QTableWidget(0, 3)
        self.constrains_table.setHorizontalHeaderLabels(["Type", "Atoms", "Value"])
        self.constrains_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.constrains_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.constrains_table.setMaximumHeight(150)
        self.constrains_table.doubleClicked.connect(self.edit_constrain)
        
        btn_layout2 = QHBoxLayout()
        add_constrain_btn = QPushButton("Add Constrain")
        del_constrain_btn = QPushButton("Delete Constrain")
        add_constrain_btn.clicked.connect(self.add_constrain)
        del_constrain_btn.clicked.connect(self.delete_constrain)
        btn_layout2.addWidget(add_constrain_btn)
        btn_layout2.addWidget(del_constrain_btn)
        
        layout.addWidget(self.constrains_table)
        layout.addLayout(btn_layout2)
        layout.addStretch()
        
        self.scans_data = []
        self.constrains_data = []
        self.current_atoms = None
        self.current_coords = None
        
    def set_structure(self, atoms, coords):
        self.current_atoms = atoms
        self.current_coords = coords

    def _refresh_scans_table(self):
        self.scans_table.setRowCount(len(self.scans_data))
        for i, s in enumerate(self.scans_data):
            self.scans_table.setItem(i, 0, QTableWidgetItem(s['type']))
            self.scans_table.setItem(i, 1, QTableWidgetItem(", ".join(map(str, [x+1 for x in s['atoms']]))))
            self.scans_table.setItem(i, 2, QTableWidgetItem(str(s['start'])))
            self.scans_table.setItem(i, 3, QTableWidgetItem(str(s['end'])))
            self.scans_table.setItem(i, 4, QTableWidgetItem(str(s['steps'])))

    def _refresh_constrains_table(self):
        self.constrains_table.setRowCount(len(self.constrains_data))
        for i, c in enumerate(self.constrains_data):
            self.constrains_table.setItem(i, 0, QTableWidgetItem(c['type']))
            self.constrains_table.setItem(i, 1, QTableWidgetItem(", ".join(map(str, [x+1 for x in c['atoms']]))))
            val_str = str(c['value']) if c.get('value') is not None else "Auto"
            self.constrains_table.setItem(i, 2, QTableWidgetItem(val_str))

    def add_scan(self):
        dlg = ScanDialog(self)
        dlg.set_structure(self.current_atoms, self.current_coords)
        if dlg.exec():
            self.scans_data.append(dlg.get_data())
            self._refresh_scans_table()

    def edit_scan(self, index):
        row = index.row()
        dlg = ScanDialog(self, self.scans_data[row])
        dlg.set_structure(self.current_atoms, self.current_coords)
        if dlg.exec():
            self.scans_data[row] = dlg.get_data()
            self._refresh_scans_table()

    def delete_scan(self):
        for item in self.scans_table.selectedItems():
            row = item.row()
            if row < len(self.scans_data):
                self.scans_data.pop(row)
                break # Only delete one per click to keep simple
        self._refresh_scans_table()

    def add_constrain(self):
        dlg = ConstrainDialog(self)
        dlg.set_structure(self.current_atoms, self.current_coords)
        if dlg.exec():
            self.constrains_data.append(dlg.get_data())
            self._refresh_constrains_table()

    def edit_constrain(self, index):
        row = index.row()
        dlg = ConstrainDialog(self, self.constrains_data[row])
        dlg.set_structure(self.current_atoms, self.current_coords)
        if dlg.exec():
            self.constrains_data[row] = dlg.get_data()
            self._refresh_constrains_table()

    def delete_constrain(self):
        for item in self.constrains_table.selectedItems():
            row = item.row()
            if row < len(self.constrains_data):
                self.constrains_data.pop(row)
                break
        self._refresh_constrains_table()

    def get_scans(self):
        return self.scans_data
        
    def get_constrains(self):
        return self.constrains_data
