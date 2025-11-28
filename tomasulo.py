class Tomasulo:
    def __init__(self):
        # Initialize reservation stations, registers, and instruction queue
        # reservation station records include parsed fields and operand bookkeeping
        self.reservation_stations = [
            {
                "name": f"RS{i}",
                "busy": False,
                "instruction": None,
                "op": None,
                "dest": None,
                "src1": None,
                "src2": None,
                "src1_source": None,
                "src2_source": None,
                "src1_value": None,
                "src2_value": None,
                "time_left": 0,
            }
            for i in range(5)
        ]
        # Initialize registers with floating-point names (F1 to F32)
        self.registers = {f"F{i}": {"value": 0, "busy": False, "rename": None} for i in range(1, 33)}
        # instruction_queue holds dicts: {text, issued, issue_cycle, exec_complete, write_cycle}
        self.instruction_queue = []
        # (instruction entries track their own `issued` flag)
        self.clock = 0
        self.memory = {i: 0 for i in range(256)}  # Simulated memory
        self.completed_operations = []  # Track completed operations
        # Cumulative count of instructions that have finished (write-back done)
        self.completed_total = 0
        # debug flag controls printing (default off for tests)
        self.debug = False
        # internal log buffer for UI
        self.log_lines = []

    def log(self, *args, **kwargs):
        # always append to internal log buffer
        try:
            msg = " ".join(str(a) for a in args)
        except Exception:
            msg = str(args)
        self.log_lines.append(msg)
        # print to stdout only when debug enabled
        if self.debug:
            print(msg, **kwargs)

    def get_logs(self, since=0):
        """Return log lines starting from index `since`."""
        return self.log_lines[since:]

    def reset(self):
        """Reset simulation state (clear RS, registers, counters)."""
        for i, rs in enumerate(self.reservation_stations):
            self.reservation_stations[i] = {
                "name": rs["name"],
                "busy": False,
                "instruction": None,
                "op": None,
                "dest": None,
                "src1": None,
                "src2": None,
                "src1_source": None,
                "src2_source": None,
                "src1_value": None,
                "src2_value": None,
                "time_left": 0,
            }
        # reset registers
        for reg in list(self.registers.keys()):
            self.registers[reg].update({"value": 0, "busy": False, "rename": None})
        # clear instruction queue and counters
        self.instruction_queue = []
        self.completed_operations = []
        self.completed_total = 0
        self.clock = 0

    def add_instruction(self, instruction):
        """Add an instruction (text) to the queue as a state dict."""
        # parse and validate instruction early to avoid repeated parsing later
        parsed = self.parse_instruction_text(instruction)

        entry = {
            "text": instruction,
            "parsed": parsed,
            "issued": False,
            "issue_cycle": None,
            "exec_start_cycle": None,
            "exec_complete": None,
            "write_cycle": None,
        }
        self.instruction_queue.append(entry)
        # entry contains its own `issued` flag

    def parse_instruction_text(self, text):
        """Parse instruction text into a structured dict.

        Supported forms:
        - ADD F3 F1 F2
        - SUB F3 F1 F2
        - MUL F3 F1 F2
        - DIV F3 F1 F2
        - LOAD F1 100
        - STORE 100 F1

        Returns dict with keys depending on op. Raises ValueError on format error.
        """
        if not isinstance(text, str):
            raise ValueError("Instruction must be a string")
        # normalize separators: replace commas with spaces, then split
        tokens = [tok.strip() for tok in text.replace(',', ' ').split() if tok.strip()]
        if len(tokens) == 0:
            raise ValueError("Empty instruction")
        op = tokens[0].upper()
        if op in ("ADD", "SUB", "MUL", "DIV"):
            if len(tokens) != 4:
                raise ValueError(f"{op} requires 3 operands: dest src1 src2: '{text}'")
            _, dest, src1, src2 = tokens
            # basic register name validation
            if dest not in self.registers:
                raise ValueError(f"Invalid destination register: {dest}")
            if src1 not in self.registers:
                raise ValueError(f"Invalid src1 register: {src1}")
            if src2 not in self.registers:
                raise ValueError(f"Invalid src2 register: {src2}")
            return {"op": op, "dest": dest, "src1": src1, "src2": src2}
        elif op == "LOAD":
            if len(tokens) != 3:
                raise ValueError(f"LOAD requires dest and address: '{text}'")
            _, dest, addr = tokens
            if dest not in self.registers:
                raise ValueError(f"Invalid destination register: {dest}")
            try:
                addr_i = int(addr)
            except Exception:
                raise ValueError(f"Invalid LOAD address: {addr}")
            return {"op": op, "dest": dest, "addr": addr_i}
        elif op == "STORE":
            if len(tokens) != 3:
                raise ValueError(f"STORE requires address and src: '{text}'")
            _, addr, src = tokens
            if src not in self.registers:
                raise ValueError(f"Invalid STORE source register: {src}")
            try:
                addr_i = int(addr)
            except Exception:
                raise ValueError(f"Invalid STORE address: {addr}")
            return {"op": op, "addr": addr_i, "src": src}
        else:
            raise ValueError(f"Unsupported operation: {op}")

    def allocate_reservation_station(self, instruction):
        """Allocate a reservation station for the instruction."""
        # Accept either instruction text or an instruction entry dict
        if isinstance(instruction, dict):
            instruction_text = instruction.get("text")
            parsed = instruction.get("parsed")
        else:
            instruction_text = instruction
            parsed = None

        # parse if needed
        if parsed is None:
            parsed = self.parse_instruction_text(instruction_text)

        op = parsed.get("op")
        # execution durations per op (cycles)
        durations = {
            "ADD": 2,
            "SUB": 2,
            "MUL": 10,
            "DIV": 20,
            "LOAD": 2,
            "STORE": 2,
        }

        if op in ["ADD", "SUB", "MUL", "DIV"]:
            dest = parsed.get("dest")
            src1 = parsed.get("src1")
            src2 = parsed.get("src2")

            self.log(f"Allocating RS for instruction: {instruction_text}, dest={dest}, src1={src1}, src2={src2}")

            for rs in self.reservation_stations:
                if not rs["busy"]:
                    rs.update({
                        "busy": True,
                        "instruction": instruction_text,
                        "op": op,
                        "dest": dest,
                        "src1": src1,
                        "src2": src2,
                        "exec_time": durations.get(op, 1),
                        "time_left": durations.get(op, 1),
                        "started": False,
                        "result": None,
                        "write_pending": False,
                        "write_ready_cycle": None,
                        "src1_ready": False,
                        "src2_ready": False,
                    })

                    # src1 readiness and source mapping
                    if self.registers.get(src1, {}).get("busy"):
                        producer = self.registers[src1].get("rename")
                        rs["src1_source"] = producer if producer else src1
                        rs["src1_value"] = None
                        rs["src1_ready"] = False
                    else:
                        rs["src1_source"] = "Reg"
                        rs["src1_value"] = self.registers[src1]["value"]
                        rs["src1_ready"] = True

                    # src2 readiness and source mapping
                    if self.registers.get(src2, {}).get("busy"):
                        producer = self.registers[src2].get("rename")
                        rs["src2_source"] = producer if producer else src2
                        rs["src2_value"] = None
                        rs["src2_ready"] = False
                    else:
                        rs["src2_source"] = "Reg"
                        rs["src2_value"] = self.registers[src2]["value"]
                        rs["src2_ready"] = True

                    # mark destination register as renamed/busy
                    if dest in self.registers:
                        self.registers[dest]["busy"] = True
                        # store rename as standardized tag: "RS:<name>"
                        self.registers[dest]["rename"] = f"RS:{rs['name']}"
                    # if caller passed an instruction entry dict, mark it issued
                    if isinstance(instruction, dict):
                        instruction["issued"] = True
                        instruction["issue_cycle"] = self.clock
                    return True

        elif op in ["LOAD", "STORE"]:
            for rs in self.reservation_stations:
                if not rs["busy"]:
                    rs.update({
                        "busy": True,
                        "instruction": instruction_text,
                        "op": op,
                        "exec_time": durations.get(op, 1),
                        "time_left": durations.get(op, 1),
                        "started": False,
                        "result": None,
                        "write_pending": False,
                        "write_ready_cycle": None,
                    })
                    if op == "LOAD":
                        dest = parsed.get("dest")
                        addr = parsed.get("addr")
                        rs["dest"] = dest
                        rs["addr"] = addr
                        # immediate/address source standardized tag
                        rs["src1_source"] = "Imm"
                        rs["src1_value"] = addr
                        rs["src1_ready"] = True
                        rs["src2_source"] = "N/A"
                        rs["src2_value"] = None
                        rs["src2_ready"] = True
                        if dest in self.registers:
                            self.registers[dest]["busy"] = True
                            # store rename as standardized tag: "RS:<name>"
                            self.registers[dest]["rename"] = f"RS:{rs['name']}"
                    else:  # STORE
                        addr = parsed.get("addr")
                        src = parsed.get("src")
                        rs["addr"] = addr
                        rs["src1"] = src
                        # src operand readiness for STORE
                        if self.registers.get(src, {}).get("busy"):
                            producer = self.registers[src].get("rename")
                            rs["src1_source"] = producer if producer else src
                            rs["src1_value"] = None
                            rs["src1_ready"] = False
                        else:
                            rs["src1_source"] = "Reg"
                            rs["src1_value"] = self.registers[src]["value"]
                            rs["src1_ready"] = True
                        rs["src2_source"] = "N/A"
                        rs["src2_value"] = None
                        rs["src2_ready"] = True
                    # if caller passed an instruction entry dict, mark it issued
                    if isinstance(instruction, dict):
                        instruction["issued"] = True
                        instruction["issue_cycle"] = self.clock
                    return True
        return False

    def execute_instruction(self, instruction):
        """Execute a single instruction."""
        parts = instruction.split()
        op = parts[0]

        if op == "ADD":
            dest, src1, src2 = parts[1:]
            self.registers[dest]["value"] = self.registers[src1]["value"] + self.registers[src2]["value"]
        elif op == "SUB":
            dest, src1, src2 = parts[1:]
            self.registers[dest]["value"] = self.registers[src1]["value"] - self.registers[src2]["value"]
        elif op == "MUL":
            dest, src1, src2 = parts[1:]
            self.registers[dest]["value"] = self.registers[src1]["value"] * self.registers[src2]["value"]
        elif op == "DIV":
            dest, src1, src2 = parts[1:]
            denom = self.registers[src2]["value"]
            self.registers[dest]["value"] = (self.registers[src1]["value"] / denom) if denom != 0 else 0
        elif op == "LOAD":
            dest, address = parts[1:]
            self.registers[dest]["value"] = self.memory[int(address)]
        elif op == "STORE":
            address, src = parts[1:]
            self.memory[int(address)] = self.registers[src]["value"]

    def step(self):
        """Simulate one clock cycle."""
        self.clock += 1
        self.completed_operations = []  # Reset completed operations for this cycle

        # Dispatch instructions from the instruction queue into free reservation stations
        # Attempt to allocate as many as possible (front of queue first).
        # We keep instructions in `instruction_queue` for UI display, so track issuance
        # using `issued_flags` to avoid re-issuing the same instruction repeatedly.
        # Ensure issued_flags length matches the queue
        for entry in self.instruction_queue:
            if entry.get("issued"):
                continue
            allocated = self.allocate_reservation_station(entry)
            if allocated:
                entry["issued"] = True

        # Update reservation stations: start execution when operands ready, decrement time_left when started
        for rs in self.reservation_stations:
            if not rs.get("busy"):
                continue
            # if execution hasn't started but operands are ready, mark started
            if not rs.get("started") and rs.get("src1_ready") and rs.get("src2_ready"):
                rs["started"] = True
                # set time_left to exec_time (already set at allocation)
                rs["time_left"] = rs.get("exec_time", 1)
                # record instruction exec start into instruction_queue entry if present
                instr_text = rs.get("instruction")
                for entry in self.instruction_queue:
                    if entry["text"] == instr_text and entry.get("exec_start_cycle") is None:
                        entry["exec_start_cycle"] = self.clock
                        break

            # decrement if started
            if rs.get("started"):
                rs["time_left"] = max(rs.get("time_left", 1) - 1, 0)

            # if finished executing (time_left == 0) and not yet pending writeback, compute result and mark exec complete
            if rs.get("started") and rs.get("time_left", 1) == 0 and not rs.get("write_pending"):
                instr_text = rs.get("instruction")
                op = rs.get("op")
                # compute using operand values saved in RS when possible
                if op in ["ADD", "SUB", "MUL", "DIV"]:
                    a = rs.get("src1_value") if rs.get("src1_value") is not None else self.registers.get(rs.get("src1"), {}).get("value", 0)
                    b = rs.get("src2_value") if rs.get("src2_value") is not None else self.registers.get(rs.get("src2"), {}).get("value", 0)
                    if op == "ADD":
                        rs["result"] = a + b
                    elif op == "SUB":
                        rs["result"] = a - b
                    elif op == "MUL":
                        rs["result"] = a * b
                    elif op == "DIV":
                        rs["result"] = (a / b) if b != 0 else 0
                elif op == "LOAD":
                    addr = int(rs.get("src1_value") if rs.get("src1_value") is not None else rs.get("addr", 0))
                    rs["result"] = self.memory.get(addr, 0)
                elif op == "STORE":
                    addr = int(str(rs.get("addr")).strip(','))
                    val = rs.get("src1_value") if rs.get("src1_value") is not None else self.registers.get(rs.get("src1"), {}).get("value", 0)
                    # For STORE, defer memory write until actual writeback
                    rs["result"] = val

                # mark exec complete on this cycle and schedule writeback in next cycle
                for entry in self.instruction_queue:
                    if entry["text"] == instr_text and entry.get("exec_complete") is None:
                        entry["exec_complete"] = self.clock
                        break

                rs["write_pending"] = True
                rs["write_ready_cycle"] = self.clock + 1
                # execution finished; clear started flag
                rs["started"] = False
                # continue to next RS (writeback will happen when ready)
                continue

            # handle pending writebacks scheduled for this cycle
            if rs.get("write_pending") and rs.get("write_ready_cycle", 0) <= self.clock:
                instr_text = rs.get("instruction")
                dest = rs.get("dest")
                result_val = rs.get("result")

                # perform actual writeback: registers or memory
                if rs.get("op") == "STORE":
                    # STORE writes memory now
                    try:
                        addr = int(str(rs.get("addr")).strip(','))
                    except Exception:
                        addr = 0
                    if result_val is not None:
                        self.memory[addr] = result_val
                else:
                    if dest in self.registers and result_val is not None:
                        self.registers[dest].update({"value": result_val, "busy": False, "rename": None})

                # Broadcast result to other reservation stations waiting on this RS
                producer_tag = f"RS:{rs.get('name')}"
                for other in self.reservation_stations:
                    if other is rs or not other.get("busy"):
                        continue
                    if other.get("src1_source") == producer_tag:
                        other["src1_value"] = result_val
                        other["src1_ready"] = True
                        other["src1_source"] = "Reg"
                    if other.get("src2_source") == producer_tag:
                        other["src2_value"] = result_val
                        other["src2_ready"] = True
                        other["src2_source"] = "Reg"

                # record write cycle into instruction entry
                for entry in self.instruction_queue:
                    if entry["text"] == instr_text and entry.get("write_cycle") is None:
                        entry["write_cycle"] = self.clock
                        break

                # increment cumulative completed count and record completed operation
                self.completed_operations.append(f"{instr_text} -> {dest} = {result_val}")
                self.completed_total += 1
                self.log(f"Total completed instructions: {self.completed_total}")

                # clear the reservation station
                rs.update({
                    "busy": False,
                    "instruction": None,
                    "op": None,
                    "dest": None,
                    "src1": None,
                    "src2": None,
                    "src1_source": None,
                    "src2_source": None,
                    "src1_value": None,
                    "src2_value": None,
                    "time_left": 0,
                    "started": False,
                    "exec_time": None,
                    "result": None,
                    "write_pending": False,
                    "write_ready_cycle": None,
                })
                

        # Check if all instructions are completed.
        # Note: we intentionally keep `instruction_queue` contents for UI display,
        # so termination must rely on how many instructions have been written back.
        all_rs_idle = all(not rs.get("busy") for rs in self.reservation_stations)
        if all_rs_idle and self.completed_total >= len(self.instruction_queue) and len(self.instruction_queue) > 0:
            self.log("All instructions have been written back. Simulation stopping.")
            return

    def get_completed_operations(self):
        """Return the list of completed operations for the current cycle."""
        return self.completed_operations

    def get_state(self):
        """Return the current state for visualization."""
        return {
            "clock": self.clock,
            "reservation_stations": self.reservation_stations,
            "registers": {
                reg: {"value": data["value"], "rename": data.get("rename", None), "busy": data.get("busy", False)}
                for reg, data in self.registers.items()
            },
            "instruction_queue": self.instruction_queue,
        }