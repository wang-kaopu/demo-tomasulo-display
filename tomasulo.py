class Tomasulo:
    def __init__(self):
        # 初始化保留站、寄存器和指令队列
        # 保留站记录包括解析后的字段和操作数记账
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
        # 初始化浮点寄存器（F1到F32）
        self.registers = {f"F{i}": {"value": 0, "busy": False, "rename": None} for i in range(1, 33)}
        # instruction_queue 保存字典: {text, issued, issue_cycle, exec_complete, write_cycle}
        self.instruction_queue = []
        # (指令条目跟踪自己的 `issued` 标志)
        self.clock = 0
        self.memory = {i: 0 for i in range(256)}  # 模拟内存
        self.completed_operations = []  # 跟踪已完成的操作
        # 操作延迟（周期数）- 默认教学/演示值
        # 用户可调: DIV=8, MUL=6, ADD/SUB=5, LOAD/STORE=4
        self.op_latencies = {
            "ADD": 5,
            "SUB": 5,
            "MUL": 6,
            "DIV": 8,
            "LOAD": 4,
            "STORE": 4,
        }
        # 已完成（写回完成）指令的累积计数
        self.completed_total = 0
        # 调试标志控制打印（测试时默认为关闭）
        self.debug = False
        # 用于UI的内部日志缓冲区
        self.log_lines = []

    def log(self, *args, **kwargs):
        # 总是附加到内部日志缓冲区
        try:
            msg = " ".join(str(a) for a in args)
        except Exception:
            msg = str(args)
        self.log_lines.append(msg)
        # 仅在启用调试时打印到标准输出
        if self.debug:
            print(msg, **kwargs)

    def get_logs(self, since=0):
        """返回从索引 `since` 开始的日志行。"""
        return self.log_lines[since:]

    def reset(self):
        """重置模拟状态（清空保留站、寄存器、计数器）。"""
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
        # 重置寄存器
        for reg in list(self.registers.keys()):
            self.registers[reg].update({"value": 0, "busy": False, "rename": None})
        # 清空指令队列和计数器
        self.instruction_queue = []
        self.completed_operations = []
        self.completed_total = 0
        self.clock = 0

    def add_instruction(self, instruction):
        """将一条指令（文本）作为状态字典添加到队列中。"""
        # 尽早解析和验证指令，以避免以后重复解析
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
        # 条目包含自己的 `issued` 标志

    def parse_instruction_text(self, text):
        """将指令文本解析为结构化字典。

        支持的格式:
        - ADD F3 F1 F2
        - SUB F3 F1 F2
        - MUL F3 F1 F2
        - DIV F3 F1 F2
        - LOAD F1 100
        - STORE 100 F1

        返回一个字典，其键取决于操作。格式错误时引发 ValueError。
        """
        if not isinstance(text, str):
            raise ValueError("指令必须是字符串")
        # 规范化分隔符：将逗号替换为空格，然后拆分
        tokens = [tok.strip() for tok in text.replace(',', ' ').split() if tok.strip()]
        if len(tokens) == 0:
            raise ValueError("空指令")
        op = tokens[0].upper()
        if op in ("ADD", "SUB", "MUL", "DIV"):
            if len(tokens) != 4:
                raise ValueError(f"{op} 需要3个操作数: dest src1 src2: '{text}'")
            _, dest, src1, src2 = tokens
            # 基本的寄存器名称验证
            if dest not in self.registers:
                raise ValueError(f"无效的目标寄存器: {dest}")
            if src1 not in self.registers:
                raise ValueError(f"无效的源寄存器1: {src1}")
            if src2 not in self.registers:
                raise ValueError(f"无效的源寄存器2: {src2}")
            return {"op": op, "dest": dest, "src1": src1, "src2": src2}
        elif op == "LOAD":
            if len(tokens) != 3:
                raise ValueError(f"LOAD 需要目标寄存器和地址: '{text}'")
            _, dest, addr = tokens
            if dest not in self.registers:
                raise ValueError(f"无效的目标寄存器: {dest}")
            try:
                addr_i = int(addr)
            except Exception:
                raise ValueError(f"无效的LOAD地址: {addr}")
            return {"op": op, "dest": dest, "addr": addr_i}
        elif op == "STORE":
            if len(tokens) != 3:
                raise ValueError(f"STORE 需要地址和源寄存器: '{text}'")
            _, addr, src = tokens
            if src not in self.registers:
                raise ValueError(f"无效的STORE源寄存器: {src}")
            try:
                addr_i = int(addr)
            except Exception:
                raise ValueError(f"无效的STORE地址: {addr}")
            return {"op": op, "addr": addr_i, "src": src}
        else:
            raise ValueError(f"不支持的操作: {op}")

    def allocate_reservation_station(self, instruction):
        """为指令分配一个保留站。"""
        # 接受指令文本或指令条目字典
        if isinstance(instruction, dict):
            instruction_text = instruction.get("text")
            parsed = instruction.get("parsed")
        else:
            instruction_text = instruction
            parsed = None

        # 如果需要，进行解析
        if parsed is None:
            parsed = self.parse_instruction_text(instruction_text)

        op = parsed.get("op")
        # 每个操作的执行持续时间（周期）- 使用配置的 op_latencies

        if op in ["ADD", "SUB", "MUL", "DIV"]:
            dest = parsed.get("dest")
            src1 = parsed.get("src1")
            src2 = parsed.get("src2")

            self.log(f"为指令分配保留站: {instruction_text}，目标={dest}，源1={src1}，源2={src2}")

            for rs in self.reservation_stations:
                if not rs["busy"]:
                    rs.update({
                        "busy": True,
                        "instruction": instruction_text,
                        "op": op,
                        "dest": dest,
                        "src1": src1,
                        "src2": src2,
                        "exec_time": self.op_latencies.get(op, 3),
                        "time_left": self.op_latencies.get(op, 3),
                        "started": False,
                        "result": None,
                        "write_pending": False,
                        "write_ready_cycle": None,
                        "src1_ready": False,
                        "src2_ready": False,
                    })

                    # src1 的就绪状态和源映射
                    if self.registers.get(src1, {}).get("busy"):
                        producer = self.registers[src1].get("rename")
                        rs["src1_source"] = producer if producer else src1
                        rs["src1_value"] = None
                        rs["src1_ready"] = False
                    else:
                        rs["src1_source"] = "Reg"
                        rs["src1_value"] = self.registers[src1]["value"]
                        rs["src1_ready"] = True

                    # src2 的就绪状态和源映射
                    if self.registers.get(src2, {}).get("busy"):
                        producer = self.registers[src2].get("rename")
                        rs["src2_source"] = producer if producer else src2
                        rs["src2_value"] = None
                        rs["src2_ready"] = False
                    else:
                        rs["src2_source"] = "Reg"
                        rs["src2_value"] = self.registers[src2]["value"]
                        rs["src2_ready"] = True

                    # 将目标寄存器标记为重命名/繁忙
                    if dest in self.registers:
                        self.registers[dest]["busy"] = True
                        # 将重命名存储为标准化标签: "RS:<name>"
                        self.registers[dest]["rename"] = f"RS:{rs['name']}"
                    # 如果调用者传递了一个指令条目字典，则将其标记为已发射
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
                        "exec_time": self.op_latencies.get(op, 3),
                        "time_left": self.op_latencies.get(op, 3),
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
                        # 立即数/地址源的标准化标签
                        rs["src1_source"] = "Imm"
                        rs["src1_value"] = addr
                        rs["src1_ready"] = True
                        rs["src2_source"] = "N/A"
                        rs["src2_value"] = None
                        rs["src2_ready"] = True
                        if dest in self.registers:
                            self.registers[dest]["busy"] = True
                            # 将重命名存储为标准化标签: "RS:<name>"
                            self.registers[dest]["rename"] = f"RS:{rs['name']}"
                    else:  # STORE
                        addr = parsed.get("addr")
                        src = parsed.get("src")
                        rs["addr"] = addr
                        rs["src1"] = src
                        # STORE 的源操作数就绪状态
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
                    # 如果调用者传递了一个指令条目字典，则将其标记为已发射
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
                self.log(f"已完成指令总数：{self.completed_total}")

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
            self.log("所有指令已写回，模拟停止。")
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