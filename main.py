import sys
import copy
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QMessageBox, QLabel, QHBoxLayout, QFileDialog, QHeaderView, QSizePolicy, QLineEdit, QComboBox
from PyQt5.QtGui import QColor
from tomasulo import Tomasulo
from PyQt5.QtWidgets import QPlainTextEdit

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
        # Columns: Op, Dest, j, k, Issue, Exec Start, Exec Comp, Write Result
        self.instruction_table.setColumnCount(8)
        self.instruction_table.setHorizontalHeaderLabels(["Op", "Dest", "j", "k", "Issue", "Exec Start", "Exec Comp", "Write Result"])
        # increase vertical space for instruction table and stretch columns
        self.instruction_table.setMinimumHeight(300)
        self.instruction_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.instruction_table)

        # Reservation station table
        self.reservation_table = QTableWidget()
        self.reservation_table.setColumnCount(8)
        self.reservation_table.setHorizontalHeaderLabels(["Time", "Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk"])
        # make reservation table adapt to window width/height
        self.reservation_table.setMinimumHeight(180)
        self.reservation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reservation_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.reservation_table)

        # Register result status table
        self.register_table = QTableWidget()
        self.register_table.setColumnCount(32)  # 32 registers F1..F32
        self.register_table.setHorizontalHeaderLabels([f"F{i}" for i in range(1, 33)])
        # Three logical rows: Qi (producer RS), Value (register content), Status (Busy/Free)
        self.register_table.setRowCount(3)
        self.register_table.setVerticalHeaderLabels(["Qi", "Value", "Status"])
        # make register table adapt to window width; many columns — allow stretch
        self.register_table.setMinimumHeight(140)
        self.register_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.register_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
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
        self.step_button = QPushButton("步进")
        self.step_button.clicked.connect(self.step_simulation)
        self.layout.addWidget(self.step_button)

        # Load Instructions button
        self.load_button = QPushButton("从文件加载指令")
        self.load_button.clicked.connect(self.load_instructions)
        self.layout.addWidget(self.load_button)

        # Manual add instruction: Op combo + dynamic operand inputs + Add button
        self.add_instr_layout = QHBoxLayout()
        self.op_combo = QComboBox()
        # supported ops (keep in sync with tomasulo.parse_instruction_text)
        self.supported_ops = ["ADD", "SUB", "MUL", "DIV", "LOAD", "STORE"]
        self.op_combo.addItems(self.supported_ops)
        self.op_combo.currentIndexChanged.connect(self._on_op_changed)

        # container for operand input widgets
        self.operand_widget = QWidget()
        self.operand_layout = QHBoxLayout()
        self.operand_layout.setContentsMargins(0, 0, 0, 0)
        self.operand_widget.setLayout(self.operand_layout)
        self.operand_inputs = []

        self.add_instr_button = QPushButton("Add 指令")
        self.add_instr_button.clicked.connect(self.add_instruction_from_input)

        self.add_instr_layout.addWidget(self.op_combo)
        self.add_instr_layout.addWidget(self.operand_widget)
        self.add_instr_layout.addWidget(self.add_instr_button)
        self.layout.addLayout(self.add_instr_layout)

        # initialize operand fields for default op
        self._on_op_changed(0)

        # Reset button
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_simulation)
        self.layout.addWidget(self.reset_button)

        # Debug checkbox
        from PyQt5.QtWidgets import QCheckBox
        self.debug_checkbox = QCheckBox("Debug")
        # match simulator default (debug False)
        self.debug_checkbox.setChecked(False)
        # ensure simulator debug flag matches checkbox initial state
        self.tomasulo.debug = False
        self.debug_checkbox.stateChanged.connect(self.toggle_debug)
        self.layout.addWidget(self.debug_checkbox)

        # Log view (hidden by default)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(180)
        self.log_view.hide()
        self.layout.addWidget(self.log_view)

        # Track how many log lines we've shown
        self._log_index = 0

        # Ensure tables are updated
        # previous state snapshot for change-highlighting
        self._prev_state = None
        self.update_tables()

    def update_tables(self):
        """Update all tables with the current state of Tomasulo."""
        state = self.tomasulo.get_state()

        # clear previous highlights
        def _clear_table_highlights(table):
            for r in range(table.rowCount()):
                for c in range(table.columnCount()):
                    item = table.item(r, c)
                    if item:
                        item.setBackground(QColor("white"))

        _clear_table_highlights(self.instruction_table)
        _clear_table_highlights(self.reservation_table)
        _clear_table_highlights(self.register_table)

        # --- Instruction table ---
        instrs = state.get("instruction_queue", [])
        self.instruction_table.setRowCount(len(instrs))
        for row, entry in enumerate(instrs):
            text = entry.get("text", "")
            parts = text.split()

            # helper to set and highlight a cell against previous state
            def _set_and_highlight(table, r, c, new_text, prev_val=None):
                item = QTableWidgetItem(new_text)
                changed = False
                if self._prev_state is not None:
                    try:
                        if prev_val is None:
                            prev_instrs = self._prev_state.get("instruction_queue", [])
                            prev_entry = prev_instrs[r] if r < len(prev_instrs) else None
                            if prev_entry is None:
                                changed = True
                            else:
                                # compare by field
                                if c == 0:
                                    prev_v = prev_entry.get("text", "").split()[0] if prev_entry.get("text") else ""
                                elif c == 1:
                                    prev_v = prev_entry.get("text", "").split()[1] if len(prev_entry.get("text", "").split())>1 else ""
                                elif c == 2:
                                    prev_v = prev_entry.get("text", "").split()[2] if len(prev_entry.get("text", "").split())>2 else ""
                                elif c == 3:
                                    prev_v = prev_entry.get("text", "").split()[3] if len(prev_entry.get("text", "").split())>3 else ""
                                elif c == 4:
                                    prev_v = str(prev_entry.get("issue_cycle")) if prev_entry.get("issue_cycle") is not None else ""
                                elif c == 5:
                                    prev_v = str(prev_entry.get("exec_start_cycle")) if prev_entry.get("exec_start_cycle") is not None else ""
                                elif c == 6:
                                    prev_v = str(prev_entry.get("exec_complete")) if prev_entry.get("exec_complete") is not None else ""
                                elif c == 7:
                                    prev_v = str(prev_entry.get("write_cycle")) if prev_entry.get("write_cycle") is not None else ""
                                else:
                                    prev_v = ""
                                changed = (str(prev_v) != str(new_text))
                        else:
                            changed = (str(prev_val) != str(new_text))
                    except Exception:
                        changed = True
                if changed:
                    item.setBackground(QColor("lightyellow"))
                table.setItem(r, c, item)

            _set_and_highlight(self.instruction_table, row, 0, parts[0] if len(parts)>0 else "")
            _set_and_highlight(self.instruction_table, row, 1, parts[1] if len(parts)>1 else "")
            _set_and_highlight(self.instruction_table, row, 2, parts[2] if len(parts)>2 else "")
            _set_and_highlight(self.instruction_table, row, 3, parts[3] if len(parts)>3 else "")

            issue_status = str(entry.get("issue_cycle")) if entry.get("issue_cycle") is not None else ""
            exec_start_status = str(entry.get("exec_start_cycle")) if entry.get("exec_start_cycle") is not None else ""
            exec_comp_status = str(entry.get("exec_complete")) if entry.get("exec_complete") is not None else ""
            write_result_status = str(entry.get("write_cycle")) if entry.get("write_cycle") is not None else ""

            _set_and_highlight(self.instruction_table, row, 4, issue_status)
            _set_and_highlight(self.instruction_table, row, 5, exec_start_status)
            _set_and_highlight(self.instruction_table, row, 6, exec_comp_status)
            _set_and_highlight(self.instruction_table, row, 7, write_result_status)

        # --- Reservation station table ---
        rs_list = state.get("reservation_stations", [])
        self.reservation_table.setRowCount(len(rs_list))
        for r, rs in enumerate(rs_list):
            vals = [
                str(rs.get("time_left", "")),
                rs.get("name", ""),
                str(rs.get("busy", False)),
                rs.get("op", ""),
                str(rs.get("src1_value", "")),
                str(rs.get("src2_value", "")),
                str(rs.get("src1_source", "")),
                str(rs.get("src2_source", "")),
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                changed = False
                if self._prev_state is not None:
                    try:
                        prev_rs = self._prev_state.get("reservation_stations", [])[r]
                        key_map = {0: 'time_left', 1: 'name', 2: 'busy', 3: 'op', 4: 'src1_value', 5: 'src2_value', 6: 'src1_source', 7: 'src2_source'}
                        prev_key = key_map.get(c)
                        prev_val = str(prev_rs.get(prev_key, ""))
                        changed = (prev_val != v)
                    except Exception:
                        changed = True
                if changed:
                    item.setBackground(QColor("lightyellow"))
                self.reservation_table.setItem(r, c, item)

        # --- Register table ---
        regs = state.get("registers", {})
        # set Qi row, Value row, Status row
        for col, reg_name in enumerate(sorted(regs.keys(), key=lambda x: int(x[1:]))):
            reg_data = regs[reg_name]
            # Qi
            qi_item = QTableWidgetItem(reg_data.get("rename", "") or "")
            # Value
            val = reg_data.get("value", "")
            if isinstance(val, float) and val.is_integer():
                val_str = str(int(val))
            else:
                val_str = str(val)
            val_item = QTableWidgetItem(val_str)
            # Status
            if reg_data.get("busy", False):
                status_item = QTableWidgetItem("Busy")
                status_item.setBackground(QColor("yellow"))
            else:
                status_item = QTableWidgetItem("Free")
                status_item.setBackground(QColor("lightgreen"))

            # highlight compares with prev_state
            if self._prev_state is not None:
                try:
                    prev_reg = self._prev_state.get("registers", {}).get(reg_name, {})
                    if prev_reg.get("rename", None) != reg_data.get("rename", None):
                        qi_item.setBackground(QColor("lightyellow"))
                    if str(prev_reg.get("value", "")) != val_str:
                        val_item.setBackground(QColor("lightyellow"))
                    if bool(prev_reg.get("busy", False)) != bool(reg_data.get("busy", False)):
                        status_item.setBackground(QColor("lightyellow"))
                except Exception:
                    pass

            self.register_table.setItem(0, col, qi_item)
            self.register_table.setItem(1, col, val_item)
            self.register_table.setItem(2, col, status_item)

        # Save snapshot for next-step comparison
        try:
            self._prev_state = copy.deepcopy(state)
        except Exception:
            self._prev_state = state

        # (Note: reservation and register tables are updated above with highlighting.)

    def step_simulation(self):
        """Advance the simulation by one clock cycle."""
        self.tomasulo.step()
        self.update_tables()

        # If debug is enabled, pull new logs and append to the log view
        if self.tomasulo.debug:
            new_logs = self.tomasulo.get_logs(self._log_index)
            for line in new_logs:
                self.log_view.appendPlainText(line)
            self._log_index += len(new_logs)
            # ensure visible and scrolled to bottom
            self.log_view.show()
            self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

        # 获取本周期完成的操作并显示
        completed_operations = self.tomasulo.get_completed_operations()
        if completed_operations:
            details = "\n".join(completed_operations)
            QMessageBox.information(self, "周期汇总", f"已完成指令:\n{details}")

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
                lines = [instr.rstrip('\n') for instr in file.readlines()]

            # reset simulator state before loading
            self.tomasulo.reset()

            errors = []
            loaded = 0
            for lineno, raw in enumerate(lines, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    self.tomasulo.add_instruction(line)
                    loaded += 1
                except Exception as e:
                    errors.append(f"Line {lineno}: {line} -> {e}")

            self.update_tables()

            if errors:
                QMessageBox.warning(self, "Load Instructions - Some lines failed",
                                    "Some instruction lines were invalid and skipped:\n" + "\n".join(errors))
            else:
                QMessageBox.information(self, "Load Instructions", f"Loaded {loaded} instructions")

    def add_instruction_from_input(self):
        """Add a single instruction from the QLineEdit into the simulator."""
        # Build instruction string from selected op and operand inputs
        op = self.op_combo.currentText().strip()
        operands = [w.text().strip() for w in self.operand_inputs]
        # basic validation: ensure required operands are provided
        if any(not s for s in operands):
            QMessageBox.warning(self, "Add Instruction", "请填写所有操作数字段。")
            return
        instr_text = " ".join([op] + operands)
        try:
            self.tomasulo.add_instruction(instr_text)
            # clear operand inputs (keep op selection)
            for w in self.operand_inputs:
                w.clear()
            self.update_tables()
            QMessageBox.information(self, "Add Instruction", f"已添加: {instr_text}")
        except Exception as e:
            QMessageBox.warning(self, "Add Instruction Failed", f"添加失败: {e}")

    def _on_op_changed(self, index):
        """Rebuild operand input fields based on selected opcode."""
        # mapping op -> operand placeholders (order matches parse_instruction_text)
        mapping = {
            "ADD": ["dest (e.g. F3)", "src1 (e.g. F1)", "src2 (e.g. F2)"],
            "SUB": ["dest (e.g. F3)", "src1 (e.g. F1)", "src2 (e.g. F2)"],
            "MUL": ["dest (e.g. F3)", "src1 (e.g. F1)", "src2 (e.g. F2)"],
            "DIV": ["dest (e.g. F3)", "src1 (e.g. F1)", "src2 (e.g. F2)"],
            "LOAD": ["dest (e.g. F1)", "address (int)"],
            "STORE": ["address (int)", "src (e.g. F1)"],
        }
        op = self.op_combo.currentText()
        placeholders = mapping.get(op, [])

        # clear existing operand widgets
        for i in reversed(range(self.operand_layout.count())):
            w = self.operand_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.operand_inputs = []

        # create new inputs
        for ph in placeholders:
            le = QLineEdit()
            le.setPlaceholderText(ph)
            self.operand_layout.addWidget(le)
            self.operand_inputs.append(le)

    def reset_simulation(self):
        """Reset the simulator state."""
        self.tomasulo.reset()
        self.update_tables()

    def toggle_debug(self, state):
        """Toggle debug logging in the simulator."""
        enabled = bool(state)
        self.tomasulo.debug = enabled
        # show or hide the log view
        if enabled:
            # populate existing logs
            logs = self.tomasulo.get_logs(0)
            self.log_view.clear()
            for line in logs:
                self.log_view.appendPlainText(line)
            self._log_index = len(logs)
            self.log_view.show()
        else:
            self.log_view.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TomasuloUI()
    window.show()
    sys.exit(app.exec_())