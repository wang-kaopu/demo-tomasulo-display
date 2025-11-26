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
        self.registers = {f"R{i}": {"value": 0, "busy": False} for i in range(8)}
        self.instruction_queue = []
        self.clock = 0
        self.memory = {i: 0 for i in range(256)}  # Simulated memory
        self.completed_operations = []  # Track completed operations

    def add_instruction(self, instruction):
        """Add an instruction to the queue."""
        self.instruction_queue.append(instruction)

    def allocate_reservation_station(self, instruction):
        """Allocate a reservation station for the instruction."""
        parts = instruction.split()
        op = parts[0]
        if op in ["ADD", "SUB"]:
            _, dest, src1, src2 = parts
            for rs in self.reservation_stations:
                if not rs["busy"]:
                    # populate parsed fields
                    rs.update({
                        "busy": True,
                        "instruction": instruction,
                        "op": op,
                        "dest": dest,
                        "src1": src1,
                        "src2": src2,
                        "time_left": 3,
                        "result": None,
                    })

                    # src1 readiness and source mapping
                    if self.registers.get(src1, {}).get("busy"):
                        # producer RS is stored in register.rename (if present)
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
                        self.registers[dest]["rename"] = rs["name"]
                    return True
        elif op in ["LOAD", "STORE"]:
            for rs in self.reservation_stations:
                if not rs["busy"]:
                    # For LOAD: parts = [LOAD, dest, address]
                    # For STORE: parts = [STORE, address, src]
                    rs.update({
                        "busy": True,
                        "instruction": instruction,
                        "op": op,
                        "time_left": 3,
                        "result": None,
                    })
                    if op == "LOAD":
                        dest = parts[1]
                        addr = parts[2]
                        rs["dest"] = dest
                        rs["addr"] = addr
                        rs["src1_source"] = "Imm/Addr"
                        rs["src1_value"] = int(addr)
                        rs["src1_ready"] = True
                        rs["src2_source"] = "N/A"
                        rs["src2_value"] = None
                        rs["src2_ready"] = True
                        if dest in self.registers:
                            self.registers[dest]["busy"] = True
                            self.registers[dest]["rename"] = rs["name"]
                    else:  # STORE
                        addr = parts[1]
                        src = parts[2]
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
        # Attempt to allocate as many as possible (front of queue first)
        for instr in list(self.instruction_queue):
            allocated = self.allocate_reservation_station(instr)
            if allocated:
                try:
                    self.instruction_queue.remove(instr)
                except ValueError:
                    pass

        # Update reservation stations
        for rs in self.reservation_stations:
            if rs.get("busy") and rs.get("src1_ready") and rs.get("src2_ready"):
                rs["time_left"] -= 1
                if rs["time_left"] == 0:
                    # Execute the instruction and store the result in the reservation station
                    instr_text = rs.get("instruction")
                    op = rs.get("op")
                    # compute using operand values saved in RS when possible
                    if op in ["ADD", "SUB"]:
                        a = rs.get("src1_value") if rs.get("src1_value") is not None else self.registers.get(rs.get("src1"), {}).get("value", 0)
                        b = rs.get("src2_value") if rs.get("src2_value") is not None else self.registers.get(rs.get("src2"), {}).get("value", 0)
                        if op == "ADD":
                            rs["result"] = a + b
                        else:
                            rs["result"] = a - b
                    elif op == "LOAD":
                        # src1_value stores the address (as int)
                        addr = int(rs.get("src1_value") if rs.get("src1_value") is not None else rs.get("addr", 0))
                        rs["result"] = self.memory.get(addr, 0)
                    elif op == "STORE":
                        # STORE writes memory at addr using src1_value
                        addr = int(rs.get("addr"))
                        val = rs.get("src1_value") if rs.get("src1_value") is not None else self.registers.get(rs.get("src1"), {}).get("value", 0)
                        self.memory[addr] = val
                        rs["result"] = None

                    # capture writeback info
                    dest = rs.get("dest")
                    result_val = rs.get("result")

                    # writeback to register file if applicable
                    if dest in self.registers and result_val is not None:
                        self.registers[dest].update({"value": result_val, "busy": False, "rename": None})

                    # Broadcast result to other reservation stations waiting on this RS
                    producer = rs.get("name")
                    for other in self.reservation_stations:
                        if other is rs or not other.get("busy"):
                            continue
                        # src1
                        if other.get("src1_source") == producer:
                            other["src1_value"] = result_val
                            other["src1_ready"] = True
                            other["src1_source"] = "Reg"
                        # src2
                        if other.get("src2_source") == producer:
                            other["src2_value"] = result_val
                            other["src2_ready"] = True
                            other["src2_source"] = "Reg"

                    # now clear the reservation station
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
                        "result": None,
                    })

                    # Log the completed operation (use captured values)
                    if instr_text:
                        self.completed_operations.append(f"{instr_text} -> {dest} = {result_val}")

    def get_completed_operations(self):
        """Return the list of completed operations for the current cycle."""
        return self.completed_operations

    def get_state(self):
        """Return the current state for visualization."""
        return {
            "clock": self.clock,
            "reservation_stations": self.reservation_stations,
            "registers": {
                reg: {"value": data["value"], "rename": data.get("rename", None)}
                for reg, data in self.registers.items()
            },
            "instruction_queue": self.instruction_queue,
        }