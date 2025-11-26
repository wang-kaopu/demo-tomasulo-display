import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QMessageBox, QLabel, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QColor
from tomasulo import Tomasulo

class TomasuloUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tomasulo Algorithm Visualization")
        self.setGeometry(100, 100, 800, 600)

        self.tomasulo = Tomasulo()

        # Main widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Instruction status table
        self.instruction_table = QTableWidget()
        self.instruction_table.setColumnCount(5)
        self.instruction_table.setHorizontalHeaderLabels(["Op", "Dest", "j", "k", "Status"])
        self.layout.addWidget(self.instruction_table)

        # Reservation station table
        self.reservation_table = QTableWidget()
        self.reservation_table.setColumnCount(8)
        self.reservation_table.setHorizontalHeaderLabels(["Time", "Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk"])
        self.layout.addWidget(self.reservation_table)

        # Register result status table
        self.register_table = QTableWidget()
        self.register_table.setColumnCount(32)  # Assuming 32 registers
        self.register_table.setHorizontalHeaderLabels([f"F{i}" for i in range(32)])
        self.layout.addWidget(self.register_table)

        # Step button
        self.step_button = QPushButton("Step")
        self.step_button.clicked.connect(self.step_simulation)
        self.layout.addWidget(self.step_button)

        # Load Instructions button
        self.load_button = QPushButton("Load Instructions")
        self.load_button.clicked.connect(self.load_instructions)
        self.layout.addWidget(self.load_button)

        # Ensure tables are updated
        self.update_tables()

    def update_tables(self):
        """Update all tables with the current state of Tomasulo."""
        state = self.tomasulo.get_state()

        # Update instruction status table
        self.instruction_table.setRowCount(len(state["instruction_queue"]))
        for i, instr in enumerate(state["instruction_queue"]):
            parts = instr.split()
            while len(parts) < 4:
                parts.append("")  # Fill missing parts with empty strings
            self.instruction_table.setItem(i, 0, QTableWidgetItem(parts[0]))
            self.instruction_table.setItem(i, 1, QTableWidgetItem(parts[1]))
            self.instruction_table.setItem(i, 2, QTableWidgetItem(parts[2]))
            self.instruction_table.setItem(i, 3, QTableWidgetItem(parts[3]))
            self.instruction_table.setItem(i, 4, QTableWidgetItem("Issued" if i < state["clock"] else "Pending"))

        # Update reservation station table
        self.reservation_table.setRowCount(len(state["reservation_stations"]))
        for i, rs in enumerate(state["reservation_stations"]):
            self.reservation_table.setItem(i, 0, QTableWidgetItem(str(rs.get("time_left", ""))))
            self.reservation_table.setItem(i, 1, QTableWidgetItem(rs.get("name", "")))
            self.reservation_table.setItem(i, 2, QTableWidgetItem(str(rs.get("busy", False))))
            self.reservation_table.setItem(i, 3, QTableWidgetItem(rs.get("op", "")))
            self.reservation_table.setItem(i, 4, QTableWidgetItem(str(rs.get("vj", ""))))
            self.reservation_table.setItem(i, 5, QTableWidgetItem(str(rs.get("vk", ""))))
            self.reservation_table.setItem(i, 6, QTableWidgetItem(rs.get("qj", "")))
            self.reservation_table.setItem(i, 7, QTableWidgetItem(rs.get("qk", "")))

        # Update register result status table
        self.register_table.setRowCount(2)  # Two rows: Qi and Data
        for i, reg in enumerate(state["registers"].values()):
            self.register_table.setItem(0, i, QTableWidgetItem(reg.get("rename", "")))
            self.register_table.setItem(1, i, QTableWidgetItem(str(reg.get("value", ""))))

    def step_simulation(self):
        """Advance the simulation by one clock cycle."""
        self.tomasulo.step()
        self.update_tables()

        # Get the completed operations and their effects
        completed_operations = self.tomasulo.get_completed_operations()
        if completed_operations:
            details = "\n".join(completed_operations)
            QMessageBox.information(self, "Cycle Summary", f"Completed Operations:\n{details}")

    def show_details(self, row, column):
        """Show details of the selected reservation station."""
        rs = self.tomasulo.get_state()["reservation_stations"][row]
        src1_source = rs.get("src1_source", "N/A")  # Source of the first operand
        src2_source = rs.get("src2_source", "N/A")  # Source of the second operand
        details = (
            f"Name: {rs['name']}\n"
            f"Busy: {rs['busy']}\n"
            f"Instruction: {rs['instruction']}\n"
            f"Time Left: {rs['time_left']}\n"
            f"Source 1: {src1_source}\n"
            f"Source 2: {src2_source}"
        )
        QMessageBox.information(self, "Reservation Station Details", details)

    def load_instructions(self):
        """Load instructions from a file."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Instruction File", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            with open(file_path, "r") as file:
                instructions = file.readlines()
                self.tomasulo.instruction_queue = [instr.strip() for instr in instructions]
                self.update_tables()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TomasuloUI()
    window.show()
    sys.exit(app.exec_())