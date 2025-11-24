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

    def add_instruction(self, instruction):
        """Add an instruction to the queue."""
        self.instruction_queue.append(instruction)

    def allocate_reservation_station(self, instruction):
        """Allocate a reservation station for the instruction."""
        op, dest, src1, src2 = instruction.split()
        for rs in self.reservation_stations:
            if not rs["busy"]:
                rs.update({
                    "busy": True,
                    "instruction": instruction,
                    "time_left": 3,
                    "src1_ready": not self.registers[src1]["busy"],
                    "src2_ready": not self.registers[src2]["busy"],
                })
                return True
        return False

    def execute_instruction(self, instruction):
        """Execute a single instruction."""
        op, dest, src1, src2 = instruction.split()
        if op == "ADD":
            self.registers[dest]["value"] = self.registers[src1]["value"] + self.registers[src2]["value"]
        elif op == "SUB":
            self.registers[dest]["value"] = self.registers[src1]["value"] - self.registers[src2]["value"]
        elif op == "LOAD":
            self.registers[dest]["value"] = self.memory[int(src1)]
        elif op == "STORE":
            self.memory[int(dest)] = self.registers[src1]["value"]

    def step(self):
        """Simulate one clock cycle."""
        self.clock += 1

        # Update reservation stations
        for rs in self.reservation_stations:
            if rs["busy"] and rs["src1_ready"] and rs["src2_ready"]:
                rs["time_left"] -= 1
                if rs["time_left"] == 0:
                    self.execute_instruction(rs["instruction"])
                    rs.update({"busy": False, "instruction": None, "src1_ready": False, "src2_ready": False})

        # Issue instructions out of order
        for instruction in list(self.instruction_queue):
            op, dest, src1, src2 = instruction.split()
            if not self.registers[src1]["busy"] and not self.registers[src2]["busy"]:
                if self.allocate_reservation_station(instruction):
                    self.instruction_queue.remove(instruction)

    def get_state(self):
        """Return the current state for visualization."""
        return {
            "clock": self.clock,
            "reservation_stations": self.reservation_stations,
            "registers": self.registers,
            "instruction_queue": self.instruction_queue,
        }