class Tomasulo:
    def __init__(self):
        # Initialize reservation stations, registers, and instruction queue
        self.reservation_stations = [
            {"name": f"RS{i}", "busy": False, "instruction": None, "time_left": 0}
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
                    rs.update({
                        "busy": True,
                        "instruction": instruction,
                        "time_left": 3,
                        "src1_ready": not self.registers[src1]["busy"],
                        "src2_ready": not self.registers[src2]["busy"],
                        "dest": dest,  # Initialize the destination register
                        "result": None,  # Initialize the result key
                    })
                    return True
        elif op in ["LOAD", "STORE"]:
            for rs in self.reservation_stations:
                if not rs["busy"]:
                    rs.update({
                        "busy": True,
                        "instruction": instruction,
                        "time_left": 3,
                        "src1_ready": True,  # LOAD/STORE do not depend on registers in the same way
                        "src2_ready": True,
                        "dest": parts[1] if op == "LOAD" else None,  # Set dest for LOAD, None for STORE
                        "result": None,  # Initialize the result key
                    })
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

        # Update reservation stations
        for rs in self.reservation_stations:
            if rs["busy"] and rs["src1_ready"] and rs["src2_ready"]:
                rs["time_left"] -= 1
                if rs["time_left"] == 0:
                    # Execute the instruction and store the result in the reservation station
                    parts = rs["instruction"].split()
                    op = parts[0]
                    if op == "ADD":
                        rs["result"] = self.registers[parts[2]]["value"] + self.registers[parts[3]]["value"]
                    elif op == "SUB":
                        rs["result"] = self.registers[parts[2]]["value"] - self.registers[parts[3]]["value"]
                    elif op == "LOAD":
                        rs["result"] = self.memory[int(parts[2])]
                    # Clear reservation station and update register renaming
                    dest = rs["dest"]
                    if dest in self.registers:
                        self.registers[dest].update({"value": rs["result"], "busy": False, "rename": None})
                    rs.update({"busy": False, "instruction": None, "src1_ready": False, "src2_ready": False, "result": None})

                    # Log the completed operation
                    self.completed_operations.append(f"{rs['instruction']} -> {dest} = {rs['result']}")

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