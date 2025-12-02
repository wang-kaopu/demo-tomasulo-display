# Tomasulo 算法可视化

一个用 Python + PyQt 实现的 Tomasulo 算法可视化工具，演示乱序执行与寄存器重命名等核心概念。

核心功能概览：

- 支持 `ADD/SUB/MUL/DIV/LOAD/STORE` 的指令解析与加载（每行一条指令）。
- 乱序执行：指令在操作数就绪后即可开始执行（保留站/重命名用于消除 WAR/WAW）。
- 周期记录：每条指令记录 `issue_cycle`、`exec_start_cycle`、`exec_complete`、`write_cycle`，便于在 UI 中展示。
- 寄存器重命名：`rename` 字段以 `RS:<name>` 保存。
- 写回广播：执行完成后在下周期写回并广播结果到等待的保留站。

文件与模块划分：

- `tomasulo.py` — 模拟器核心：解析入队、保留站分配、执行推进、写回与广播、内部日志接口。
- `main.py` — GUI：显示三张表（Instruction / Reservation Stations / Registers），控制加载、逐周期 Step、Reset、Debug 日志视图。
- `test_all.py` — 单元测试集合：覆盖周期记录、运算正确性、STORE/边缘情况测试。
- `instructions.txt` — 示例指令文件（每行一条）。

安装与运行：

```powershell
pip install PyQt5
python .\main.py
```

运行测试：

```powershell
python -m unittest test_all.py -v
```

当前未完成功能（简要）：

- 精确的重排序缓冲区（ROB）与 in-order 提交（可选，支持回滚与精确异常）。
- Store Buffer / 内存按程序序提交保障（可选，保证内存写入的程序顺序）。
"""
# Tomasulo 算法可视化（Python + PyQt）

这是一个用于教学与演示的 Tomasulo 算法可视化工具，使用 Python 与 PyQt5 实现。该工具模拟并可视化乱序执行（out-of-order execution）、保留站（Reservation Stations）、寄存器重命名和写回广播（CDB-like broadcast）。

主要目标：帮助理解 Tomasulo 算法中指令调度、数据相关性消除、以及写回广播如何推动后续指令执行。

---

## 主要功能

- 支持指令：`ADD`, `SUB`, `MUL`, `DIV`, `LOAD`, `STORE`（每行一条指令文本）。
- 指令解析与入队（`add_instruction` / 文件加载）。
- 保留站分配与寄存器重命名：目的寄存器会被标记为 `rename = 'RS:<name>'`。
- 执行计时（可配置延迟），执行完成后在下一个周期写回并广播结果到等待的保留站。
- GUI 可视化三张表格：指令状态、保留站、寄存器状态；支持逐周期（单步）推进与 Debug 日志。
- 已实现的指令延迟默认值（可在代码中调整）：DIV=8、MUL=6、ADD/SUB=5、LOAD/STORE=4。

---

## 文件结构（关键文件）

- `tomasulo.py` — 模拟器核心，包含：
  - 指令解析：`parse_instruction_text`，入队：`add_instruction`。
  - 保留站分配：`allocate_reservation_station`。
  - 执行推进与写回广播：`step`。
  - 状态导出与日志：`get_state`, `get_logs`。
- `main.py` — PyQt 前端，渲染并交互：加载指令、单步（`单步`）、重置（`重置`）、Debug 日志。
- `instructions.txt` — 示例指令（可通过 GUI 加载）。
- `test_step.py`, `test_depend.py` — 简单的验证脚本（演示单条指令与依赖唤醒场景）。

---

## 安装与运行

1. 安装依赖（Windows PowerShell 示例）：

```powershell
pip install PyQt5
```

2. 运行应用：

```powershell
python .\main.py
```

窗口说明（主要控件与操作）：
- `加载指令`：从文本文件逐行加载指令。
- `单步`：推进一个时钟周期，表格会刷新并高亮显示发生变化的单元格。
- `重置`：清空模拟器状态并重置 UI。
- `Debug`：勾选后显示模拟器内部日志面板（便于调试）。

指令示例（每行一条）：
```
ADD F1 F2 F3
LOAD F4 100
STORE 200 F5
```

---

## 运行测试（示例）

当前仓库包含若干简单的测试脚本用于验证核心行为（示例：`test_step.py`, `test_depend.py`）。

在项目根目录运行：

```powershell
python .\test_step.py
python .\test_depend.py
```

如需使用 `unittest` 或 `pytest` 集成测试，可将这些脚本改为标准测试用例并运行：

```powershell
python -m unittest discover -v
# 或
pytest -q
```

---

## 开发说明与扩展建议

- 当前实现已包含基本的派发、执行计时与写回广播机制，但并未实现复杂的提交机制（ROB）和精确异常回滚。以下是常见扩展方向：
  - ROB（重排序缓冲区）：将写回结果先写入 ROB 条目，只有当该 ROB 条目成为头部且无异常时才更新寄存器/内存并释放重命名。这样可实现精确异常与 in-order commit。
  - Store Buffer / Memory Ordering：单独管理 STORE 的提交顺序，保证内存写入按程序顺序或遵循更复杂的内存模型。
  - CDB 仲裁：当前实现简单广播到所有等待 RS；如多个 RS 在同一周期需要写回，可额外实现仲裁策略以决定单条或按优先级写回。
  - UI 优化：更精细的差量渲染、颜色化来源标签（`RS:<name>`、`Reg`、`Imm`）、单元格动画以增强可读性。

---

## 已知限制

- GUI 以教学为目标，未针对大规模指令流优化（如果需要更大规模模拟，建议改为差量更新或更高效的数据绑定）。
- 写回/提交目前较为简化（见上文扩展建议）。

---

## API 参考（`tomasulo.Tomasulo`）

下面列出 `Tomasulo` 类的主要方法、属性和数据结构格式

主要属性（常用）：
- `reservation_stations`: 列表，每项为保留站字典，示例字段：
  - `name`: 保留站名称（如 `RS0`）
  - `busy`: 布尔，是否占用
  - `instruction`: 指令文本（如 `ADD F1 F2 F3`）
  - `op`: 操作码（`ADD`/`MUL`/...）
  - `dest`, `src1`, `src2`: 寄存器或其他操作数字段名称
  - `src1_source`, `src2_source`: 源头标签（`Reg`、`Imm` 或 `RS:<name>`）
  - `src1_value`, `src2_value`: 已就绪的操作数值（若未知则为 None）
  - `time_left`: 剩余执行周期数
  - `exec_time`, `started`, `result`, `write_pending`, `write_ready_cycle` 等其他执行追踪字段
- `registers`: 字典，键为 `F1..F32`，值为 `{"value": number, "busy": bool, "rename": optional tag}`。
- `instruction_queue`: 列表，每项为指令条目字典，结构示例：
  - `{"text": "ADD F1 F2 F3", "parsed": {...}, "issued": False, "issue_cycle": None, "exec_start_cycle": None, "exec_complete": None, "write_cycle": None}`
- `op_latencies`: dict，操作延迟映射（例如 `{"ADD":5, "MUL":6, "DIV":8, "LOAD":4, "STORE":4}`）。
- `memory`: 简单整数键值映射，用作模拟内存。
- `clock`: 当前模拟时钟周期（整型）。
- `completed_operations`: 本周期完成操作列表（字符串描述），`completed_total` 为累计完成计数。

主要方法：
- `add_instruction(instruction_text: str)`
  - 将一条指令文本解析并入队，生成带 `parsed` 的条目供后续派发。
- `parse_instruction_text(text: str) -> dict`
  - 验证并解析指令文本，返回结构化字段（`op`, `dest`, `src1`, `src2` / `addr` 等），遇错抛出 `ValueError`。
- `allocate_reservation_station(instruction)`
  - 尝试为一个指令条目（字典或文本）分配空闲保留站并初始化操作数来源/就绪性；返回布尔表示是否分配成功。
- `step()`
  - 推进一个时钟周期：
    1. 从 `instruction_queue` 调度尚未 `issued` 的条目到空闲保留站（若有）并标记 `issued`。
    2. 对每个 busy 的 RS：当操作数就绪且未开始则开始执行并设置 `time_left`；执行中递减 `time_left`。
    3. 执行完成后计算 `result` 并将 `write_pending` 与 `write_ready_cycle` 设为下周期写回。
    4. 在写回周期，将结果写入目的寄存器或内存，并广播生产者标签（例如 `RS:RS0`）到其他 RS 更新其等待操作数。
    5. 更新 `instruction_queue` 中的 `exec_start_cycle/exec_complete/write_cycle` 字段以及 `completed_operations` 列表。
- `get_state() -> dict`
  - 返回当前可用于 UI 渲染的完整状态字典，包含 `clock`, `reservation_stations`, `registers`, `instruction_queue` 等。
- `get_logs(since=0) -> list[str]`
  - 返回内部日志文本行（用于 Debug 窗格），`since` 可用于增量拉取。
- `get_completed_operations() -> list[str]`
  - 返回当前周期已完成的操作列表（`step()` 调用后读取以显示周期汇总）。
- `reset()`
  - 重置模拟器状态（清空 RS、寄存器、计时器、队列等）。

使用示例：
```
from tomasulo import Tomasulo

t = Tomasulo()
t.add_instruction('ADD F1 F2 F3')
t.add_instruction('ADD F4 F1 F5')
for _ in range(10):
    t.step()
    print(t.get_completed_operations())
```

注意：`t.instruction_queue` 中保留了入队条目，UI 使用该队列展示指令生命周期（因此条目不会在写回后自动删除，除非你手动清理或重置）。