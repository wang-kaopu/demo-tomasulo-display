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
        self.instruction_table.setColumnCount(7)
        self.instruction_table.setHorizontalHeaderLabels(["Op", "Dest", "j", "k", "Issue", "Exec Comp", "Write Result"])
        self.layout.addWidget(self.instruction_table)

        # Reservation station table
        self.reservation_table = QTableWidget()
        self.reservation_table.setColumnCount(8)
        self.reservation_table.setHorizontalHeaderLabels(["Time", "Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk"])
        self.layout.addWidget(self.reservation_table)

        # Register result status table
        self.register_table = QTableWidget()
        self.register_table.setColumnCount(32)  # 32 registers F1..F32
        self.register_table.setHorizontalHeaderLabels([f"F{i}" for i in range(1, 33)])
        self.layout.addWidget(self.register_table)

        # Add titles above each table
        self.instruction_title = QLabel("指令状态")
        self.layout.addWidget(self.instruction_title)
        self.layout.addWidget(self.instruction_table)

        self.reservation_title = QLabel("保留站")
        self.layout.addWidget(self.reservation_title)
        self.layout.addWidget(self.reservation_table)

        self.register_title = QLabel("寄存器结果状态")
        self.layout.addWidget(self.register_title)
        self.layout.addWidget(self.register_table)

        # Step button
        self.step_button = QPushButton("Step")
        self.step_button.clicked.connect(self.step_simulation)
        self.layout.addWidget(self.step_button)

        # Load Instructions button
        self.load_button = QPushButton("Load Instructions")
        self.load_button.clicked.connect(self.load_instructions)
        self.layout.addWidget(self.load_button)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_simulation)
        self.layout.addWidget(self.reset_button)

        # Debug checkbox
        from PyQt5.QtWidgets import QCheckBox
        self.debug_checkbox = QCheckBox("Debug")
        self.debug_checkbox.setChecked(True)
        self.debug_checkbox.stateChanged.connect(self.toggle_debug)
        self.layout.addWidget(self.debug_checkbox)

        # Ensure tables are updated
        self.update_tables()

    def update_tables(self):
        """Update all tables with the current state of Tomasulo."""
        state = self.tomasulo.get_state()

        # Update instruction status table (instruction entries are dicts)
        instrs = state["instruction_queue"]
        self.instruction_table.setRowCount(len(instrs))
        for i, entry in enumerate(instrs):
            text = entry.get("text", "")
            parts = text.split()
            while len(parts) < 4:
                parts.append("")
            self.instruction_table.setItem(i, 0, QTableWidgetItem(parts[0]))
            self.instruction_table.setItem(i, 1, QTableWidgetItem(parts[1] if len(parts) > 1 else ""))
            self.instruction_table.setItem(i, 2, QTableWidgetItem(parts[2] if len(parts) > 2 else ""))
            self.instruction_table.setItem(i, 3, QTableWidgetItem(parts[3] if len(parts) > 3 else ""))

            # Issue / Exec Comp / Write Result from entry fields
            issue_status = "✓" if entry.get("issue_cycle") is not None else ""
            exec_comp_status = "✓" if entry.get("exec_complete") is not None else ""
            write_result_status = "✓" if entry.get("write_cycle") is not None else ""

            self.instruction_table.setItem(i, 4, QTableWidgetItem(issue_status))
            self.instruction_table.setItem(i, 5, QTableWidgetItem(exec_comp_status))
            self.instruction_table.setItem(i, 6, QTableWidgetItem(write_result_status))

        # Update reservation station table
        self.reservation_table.setRowCount(len(state["reservation_stations"]))
        for i, rs in enumerate(state["reservation_stations"]):
            self.reservation_table.setItem(i, 0, QTableWidgetItem(str(rs.get("time_left", ""))))
            self.reservation_table.setItem(i, 1, QTableWidgetItem(rs.get("name", "")))
            self.reservation_table.setItem(i, 2, QTableWidgetItem(str(rs.get("busy", False))))
            self.reservation_table.setItem(i, 3, QTableWidgetItem(rs.get("op", "")))
            # show operand values and source tags
            self.reservation_table.setItem(i, 4, QTableWidgetItem(str(rs.get("src1_value", ""))))
            self.reservation_table.setItem(i, 5, QTableWidgetItem(str(rs.get("src2_value", ""))))
            self.reservation_table.setItem(i, 6, QTableWidgetItem(str(rs.get("src1_source", ""))))
            self.reservation_table.setItem(i, 7, QTableWidgetItem(str(rs.get("src2_source", ""))))

        # Update register result status table
        self.register_table.setRowCount(3)  # Three rows: Qi, Data, and Status
        for i, (reg_name, reg_data) in enumerate(state["registers"].items()):
            self.register_table.setItem(0, i, QTableWidgetItem(reg_data.get("rename", "")))
            self.register_table.setItem(1, i, QTableWidgetItem(str(reg_data.get("value", ""))))

            # Determine the status of the register
            if reg_data.get("busy", False):
                status_text = "Busy"
                color = QColor("yellow")
            else:
                status_text = "Free"
                color = QColor("lightgreen")

            status_item = QTableWidgetItem(status_text)
            status_item.setBackground(color)
            self.register_table.setItem(2, i, status_item)

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
                instructions = [instr.strip() for instr in file.readlines() if instr.strip()]
                # reset internal state and load
                self.tomasulo.instruction_queue = []
                self.tomasulo.completed_operations = []
                self.tomasulo.completed_total = 0
                for instr in instructions:
                    self.tomasulo.add_instruction(instr)
                self.update_tables()

    def reset_simulation(self):
        """Reset the simulator state."""
        self.tomasulo.reset()
        self.update_tables()

    def toggle_debug(self, state):
        """Toggle debug logging in the simulator."""
        self.tomasulo.debug = bool(state)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TomasuloUI()
    window.show()
    sys.exit(app.exec_())