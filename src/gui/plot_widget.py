import matplotlib
matplotlib.use('QtAgg')
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        
    def plot_energy(self, energies, title="Scan Energy Profile", xlabel="Step", ylabel="Relative Energy (kcal/mol)"):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(energies, marker='o', color='blue')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
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
