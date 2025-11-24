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

        # Table for visualization
        self.table = QTableWidget()
        # allow double click to show reservation station details
        self.table.cellDoubleClicked.connect(self.show_details)
        self.layout.addWidget(self.table)

        # Initialize register and instruction labels
        self.register_label = QLabel("Registers:")
        self.layout.addWidget(self.register_label)

        self.instruction_label = QLabel("Instruction Queue:")
        self.layout.addWidget(self.instruction_label)

        # Load instructions button
        self.load_button = QPushButton("Load Instructions")
        self.load_button.clicked.connect(self.load_instructions)
        self.layout.addWidget(self.load_button)

        # Step button
        self.step_button = QPushButton("Step")
        self.step_button.clicked.connect(self.step_simulation)
        self.layout.addWidget(self.step_button)

        # Ensure table and labels are updated
        self.update_table()

    def update_table(self):
        """Update the table with the current state of Tomasulo."""
        state = self.tomasulo.get_state()
        self.table.setRowCount(len(state["reservation_stations"]))
        self.table.setColumnCount(4)  # Add a column for instruction state
        self.table.setHorizontalHeaderLabels(["Name", "Busy", "Instruction", "State"])

        for i, rs in enumerate(state["reservation_stations"]):
            self.table.setItem(i, 0, QTableWidgetItem(rs.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(str(rs.get("busy", False))))
            self.table.setItem(i, 2, QTableWidgetItem(rs.get("instruction", "")))

            # Determine the state of the instruction
            if not rs["busy"]:
                state_text = "Idle"
                color = QColor("white")
            elif rs["time_left"] > 0:
                state_text = "Executing"
                color = QColor("yellow")
            else:
                state_text = "Completed"
                color = QColor("lightgreen")

            state_item = QTableWidgetItem(state_text)
            state_item.setBackground(color)
            self.table.setItem(i, 3, state_item)

        # Update register state
        registers = self.tomasulo.get_state()["registers"]
        reg_text = "\n".join([f"{reg}: {data['value']}" for reg, data in registers.items()])
        self.register_label.setText(f"Registers:\n{reg_text}")

        # Update instruction queue
        instruction_queue = self.tomasulo.get_state()["instruction_queue"]
        instr_text = "\n".join(instruction_queue)
        self.instruction_label.setText(f"Instruction Queue:\n{instr_text}")

    def step_simulation(self):
        """Advance the simulation by one clock cycle and display completed operations."""
        self.tomasulo.step()
        self.update_table()

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
                self.update_table()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TomasuloUI()
    window.show()
    sys.exit(app.exec_())