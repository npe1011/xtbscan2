import os
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QRadioButton, QButtonGroup, QCheckBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_content}</script>
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
        #container {{ width: 100%; height: 100%; position: relative; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        let viewer = null;
        let loadQueue = null;
        let measureMode = 'none'; // 'distance', 'angle', 'dihedral'
        let selectedAtoms = [];
        let measurementShapes = [];

        document.addEventListener("DOMContentLoaded", function() {{
            let element = document.getElementById('container');
            let config = {{ backgroundColor: 'black' }};
            viewer = $3Dmol.createViewer(element, config);
            if (loadQueue !== null) {{
                loadXYZ(loadQueue);
                loadQueue = null;
            }}
        }});
        
        let showLabelsState = false;

        function setMeasureMode(mode) {{
            measureMode = mode;
            selectedAtoms = [];
            viewer.removeAllShapes();
            for (let s of measurementShapes) {{
                if (s.type === 'cylinder') viewer.addCylinder(s.data);
            }}
            updateLabels(showLabelsState);
        }}
        
        function clearMeasurements() {{
            measurementShapes = [];
            selectedAtoms = [];
            viewer.removeAllShapes();
            updateLabels(showLabelsState);
        }}

        function loadXYZ(data) {{
            if (viewer === null) {{
                loadQueue = data;
                return;
            }}
            viewer.clear();
            viewer.addModel(data, "xyz");
            viewer.setStyle({{}}, {{stick: {{radius: 0.15}}, sphere: {{scale: 0.3}}}});
            viewer.zoomTo();
            viewer.setClickable({{}}, true, atomClicked);
            clearMeasurements(); 
        }}

        function updateLabels(show) {{
            if (!viewer) return;
            if (show !== undefined) showLabelsState = show;
            viewer.removeAllLabels();
            if (showLabelsState) {{
                let atoms = viewer.selectedAtoms({{}});
                for (let i = 0; i < atoms.length; i++) {{
                    let atom = atoms[i];
                    let num = atom.index + 1;
                    viewer.addLabel(atom.elem + num, {{
                        position: atom,
                        backgroundColor: 'black', fontColor: 'white',
                        fontSize: 14, backgroundOpacity: 0.85, borderThickness: 0
                    }});
                }}
            }}
            for (let s of measurementShapes) {{
                if (s.type === 'label') viewer.addLabel(s.text, s.data);
            }}
            viewer.render();
        }}

        function sub(v1, v2) {{ return {{x: v1.x - v2.x, y: v1.y - v2.y, z: v1.z - v2.z}}; }}
        function add(v1, v2) {{ return {{x: v1.x + v2.x, y: v1.y + v2.y, z: v1.z + v2.z}}; }}
        function dot(v1, v2) {{ return v1.x*v2.x + v1.y*v2.y + v1.z*v2.z; }}
        function cross(v1, v2) {{ return {{x: v1.y*v2.z - v1.z*v2.y, y: v1.z*v2.x - v1.x*v2.z, z: v1.x*v2.y - v1.y*v2.x}}; }}
        function mag(v) {{ return Math.sqrt(dot(v, v)); }}
        function norm(v) {{ let m = mag(v); return {{x: v.x/m, y: v.y/m, z: v.z/m}}; }}
        function scale(v, s) {{ return {{x: v.x*s, y: v.y*s, z: v.z*s}}; }}

        function atomClicked(atom, viewer) {{
            if (measureMode === 'none') return;
            selectedAtoms.push(atom);
            let selNum = selectedAtoms.length;
            viewer.addSphere({{center: {{x:atom.x, y:atom.y, z:atom.z}}, radius: 0.65, color: '#00ff00', alpha: 0.7}});
            viewer.addLabel("[" + selNum + "] " + atom.elem + (atom.index + 1), {{
                position: atom,
                backgroundColor: '#006600', fontColor: 'white',
                fontSize: 13, backgroundOpacity: 0.9, borderThickness: 1, borderColor: '#00ff00'
            }});
            viewer.render();
            
            let reqAtoms = measureMode === 'distance' ? 2 : (measureMode === 'angle' ? 3 : 4);
            if (selectedAtoms.length === reqAtoms) {{
                calculateMeasurement();
                selectedAtoms = [];
                viewer.removeAllShapes();
                for (let s of measurementShapes) {{
                    if (s.type === 'cylinder') viewer.addCylinder(s.data);
                }}
                updateLabels(showLabelsState);
            }}
        }}
        
        function calculateMeasurement() {{
            let a1 = selectedAtoms[0];
            let a2 = selectedAtoms[1];
            
            if (measureMode === 'distance') {{
                let d = mag(sub(a1, a2));
                let mid = scale(add(a1, a2), 0.5);
                let cylData = {{start:{{x:a1.x,y:a1.y,z:a1.z}}, end:{{x:a2.x,y:a2.y,z:a2.z}}, radius: 0.05, color: 'white', dashed: true}};
                let lblData = {{position: mid, backgroundColor: 'black', fontColor: 'white'}};
                measurementShapes.push({{type: 'cylinder', data: cylData}});
                measurementShapes.push({{type: 'label', text: d.toFixed(3) + " A", data: lblData}});
                viewer.addCylinder(cylData);
                viewer.addLabel(d.toFixed(3) + " A", lblData);
            }} 
            else if (measureMode === 'angle') {{
                let a3 = selectedAtoms[2];
                let v1 = sub(a1, a2);
                let v2 = sub(a3, a2);
                let angle = Math.acos(dot(v1, v2) / (mag(v1) * mag(v2))) * 180 / Math.PI;
                let lblData = {{position: {{x:a2.x, y:a2.y, z:a2.z}}, backgroundColor: 'black', fontColor: 'yellow', alignment: 'bottomLeft'}};
                measurementShapes.push({{type: 'label', text: angle.toFixed(1) + " deg", data: lblData}});
                viewer.addLabel(angle.toFixed(1) + " deg", lblData);
                
                let c1 = {{start:{{x:a1.x,y:a1.y,z:a1.z}}, end:{{x:a2.x,y:a2.y,z:a2.z}}, radius: 0.05, color: 'white', dashed: true}};
                let c2 = {{start:{{x:a3.x,y:a3.y,z:a3.z}}, end:{{x:a2.x,y:a2.y,z:a2.z}}, radius: 0.05, color: 'white', dashed: true}};
                measurementShapes.push({{type: 'cylinder', data: c1}});
                measurementShapes.push({{type: 'cylinder', data: c2}});
                viewer.addCylinder(c1);
                viewer.addCylinder(c2);
            }} 
            else if (measureMode === 'dihedral') {{
                let a3 = selectedAtoms[2];
                let a4 = selectedAtoms[3];
                let b1 = sub(a2, a1);
                let b2 = sub(a3, a2);
                let b3 = sub(a4, a3);
                let n1 = cross(b1, b2);
                let n2 = cross(b2, b3);
                let m1 = cross(n1, norm(b2));
                let x = dot(n1, n2);
                let y = dot(m1, n2);
                let dihedral = Math.atan2(y, x) * 180 / Math.PI;
                let mid = scale(add(a2, a3), 0.5);
                let lblData = {{position: mid, backgroundColor: 'black', fontColor: 'cyan'}};
                measurementShapes.push({{type: 'label', text: dihedral.toFixed(1) + " deg", data: lblData}});
                viewer.addLabel(dihedral.toFixed(1) + " deg", lblData);
                
                let c1 = {{start:{{x:a1.x,y:a1.y,z:a1.z}}, end:{{x:a2.x,y:a2.y,z:a2.z}}, radius: 0.05, color: 'white', dashed: true}};
                let c2 = {{start:{{x:a3.x,y:a3.y,z:a3.z}}, end:{{x:a4.x,y:a4.y,z:a4.z}}, radius: 0.05, color: 'white', dashed: true}};
                measurementShapes.push({{type: 'cylinder', data: c1}});
                measurementShapes.push({{type: 'cylinder', data: c2}});
                viewer.addCylinder(c1);
                viewer.addCylinder(c2);
            }}
        }}
    </script>
</body>
</html>
"""

class CustomWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, source):
        print(f"JS [{level}] {source}:{line} - {msg}")

class Viewer3D(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.toolbar_layout = QHBoxLayout()
        self.layout.addLayout(self.toolbar_layout)
        
        self.toolbar_layout.addWidget(QLabel("Measure:"))
        
        self.mode_group = QButtonGroup(self)
        self.btn_none = QRadioButton("None")
        self.btn_none.setChecked(True)
        self.btn_dist = QRadioButton("Distance")
        self.btn_angle = QRadioButton("Angle")
        self.btn_dihedral = QRadioButton("Dihedral")
        
        self.mode_group.addButton(self.btn_none)
        self.mode_group.addButton(self.btn_dist)
        self.mode_group.addButton(self.btn_angle)
        self.mode_group.addButton(self.btn_dihedral)
        
        self.toolbar_layout.addWidget(self.btn_none)
        self.toolbar_layout.addWidget(self.btn_dist)
        self.toolbar_layout.addWidget(self.btn_angle)
        self.toolbar_layout.addWidget(self.btn_dihedral)
        
        self.btn_clear = QPushButton("Clear")
        self.toolbar_layout.addWidget(self.btn_clear)
        
        self.label_cb = QCheckBox("Labels")
        self.toolbar_layout.addWidget(self.label_cb)
        
        self.toolbar_layout.addStretch()
        
        self.btn_none.toggled.connect(lambda c: self.set_mode('none') if c else None)
        self.btn_dist.toggled.connect(lambda c: self.set_mode('distance') if c else None)
        self.btn_angle.toggled.connect(lambda c: self.set_mode('angle') if c else None)
        self.btn_dihedral.toggled.connect(lambda c: self.set_mode('dihedral') if c else None)
        self.btn_clear.clicked.connect(self.clear_measurements)
        self.label_cb.toggled.connect(self.toggle_labels)
        
        self.web_view = QWebEngineView()
        self.web_page = CustomWebPage()
        self.web_view.setPage(self.web_page)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        self.layout.addWidget(self.web_view)
        
        self.is_loaded = False
        self.pending_xyz = None
        self.web_view.loadFinished.connect(self._on_load_finished)
        
        js_path = Path(__file__).parent / "resources" / "3Dmol-min.js"
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        js_content = js_content.replace('</script>', '<\\/script>')
        html = HTML_TEMPLATE.format(js_content=js_content)
        self.web_view.setHtml(html)

    def _on_load_finished(self, ok):
        if not ok:
            print("Warning: WebEngine page failed to load")
            return
        self.is_loaded = True
        if self.pending_xyz:
            if getattr(self, 'pending_mode', 'xyz') == 'trajectory':
                self.load_trajectory(self.pending_xyz)
            else:
                self.load_xyz(self.pending_xyz)
            self.pending_xyz = None

    def toggle_labels(self, state):
        if self.is_loaded:
            show_val = "true" if state else "false"
            self.web_view.page().runJavaScript(f"updateLabels({show_val});")

    def set_mode(self, mode: str):
        if self.is_loaded:
            self.web_view.page().runJavaScript(f"setMeasureMode('{mode}');")

    def clear_measurements(self):
        if self.is_loaded:
            self.web_view.page().runJavaScript("clearMeasurements();")

    def load_xyz(self, xyz_str: str):
        if not self.is_loaded:
            self.pending_xyz = xyz_str
            self.pending_mode = 'xyz'
            return
            
        import json
        xyz_json = json.dumps(xyz_str)
        show_val = "true" if self.label_cb.isChecked() else "false"
        self.btn_none.setChecked(True)
        
        js = f"""
        if(viewer) {{
            if(viewer.isAnimated()) {{
                viewer.stopAnimate();
            }}
            viewer.clear();
        }}
        loadXYZ({xyz_json});
        updateLabels({show_val});
        """
        self.web_view.page().runJavaScript(js)

    def load_trajectory(self, xyz_str: str):
        if not self.is_loaded:
            self.pending_xyz = xyz_str
            self.pending_mode = 'trajectory'
            return
            
        import json
        xyz_json = json.dumps(xyz_str)
        show_val = "true" if self.label_cb.isChecked() else "false"
        self.btn_none.setChecked(True)
        
        js = f"""
        if(viewer) {{
            if(viewer.isAnimated()) {{
                viewer.stopAnimate();
            }}
            viewer.clear();
            viewer.addModelsAsFrames({xyz_json}, "xyz");
            viewer.setStyle({{}}, {{stick: {{radius: 0.15}}, sphere: {{scale: 0.3}}}});
            viewer.zoomTo();
            viewer.setFrame(0);
            viewer.setClickable({{}}, true, atomClicked);
            clearMeasurements();
            updateLabels({show_val});
            viewer.render();
        }}
        """
        self.web_view.page().runJavaScript(js)

    def start_animate(self):
        if self.is_loaded:
            self.web_view.page().runJavaScript("if(viewer) { viewer.animate({loop: 'forward', step: 1, interval: 250}); }")
            
    def stop_animate(self):
        if self.is_loaded:
            self.web_view.page().runJavaScript("if(viewer) { if(viewer.isAnimated()) viewer.stopAnimate(); }")
            
    def set_frame(self, frame_idx: int):
        if self.is_loaded:
            self.web_view.page().runJavaScript(f"if(viewer) {{ if(viewer.isAnimated()) viewer.stopAnimate(); viewer.setFrame({frame_idx}); viewer.setClickable({{}}, true, atomClicked); viewer.render(); }}")

    def cleanup(self):
        if hasattr(self, 'web_view') and self.web_view:
            self.web_view.stop()
            page = self.web_view.page()
            self.web_view.setPage(None)
            if page:
                page.deleteLater()
            self.web_view.deleteLater()
            self.web_view = None


