# Tomasulo 算法可视化

一个用 Python + PyQt5 实现的 Tomasulo 算法可视化工具，用于教学与演示乱序执行、保留站调度、寄存器重命名和数据依赖消除等核心概念。

## 核心功能

- **指令支持**：`ADD`、`SUB`、`MUL`、`DIV`、`LOAD`、`STORE`
- **乱序执行**：指令在操作数就绪后即可开始执行，通过保留站和寄存器重命名消除 WAR/WAW 冲突
- **周期追踪**：精确记录每条指令的 Issue、Exec Start、Exec Complete、Write Result 周期
- **寄存器重命名**：动态重命名机制（格式：`RS:<name>`），实时展示依赖关系
- **结果广播**：模拟 CDB（Common Data Bus），执行完成后广播结果到等待的保留站
- **可视化界面**：实时显示指令状态、保留站状态、寄存器结果状态三张表格
- **交互功能**：
  - 从文件加载指令
  - 手动添加指令（带输入验证）
  - 逐周期单步执行
  - Debug 日志查看
  - 状态高亮显示

## 项目结构

```
demo/
├── tomasulo.py          # 核心模拟器：指令解析、保留站分配、执行调度、写回广播
├── main.py              # PyQt5 GUI：可视化界面和用户交互
├── test_all.py          # 完整的单元测试套件
├── instructions.txt     # 示例指令文件
├── README.md            # 项目文档
└── .github/
    └── copilot-instructions.md  # AI 协作开发指南
```

## 快速开始

### 环境要求

- Python 3.7+
- PyQt5

### 安装依赖

```powershell
pip install PyQt5
```

### 运行程序

```powershell
python .\main.py
```

### 使用说明

1. **加载指令**
   - 点击「从文件加载指令」按钮，选择 `instructions.txt` 或自定义指令文件
   - 指令格式（每行一条）：
     ```
     ADD F1 F2 F3    # F1 = F2 + F3
     LOAD F4 100     # F4 = Memory[100]
     STORE 200 F5    # Memory[200] = F5
     ```

2. **手动添加指令**
   - 从操作下拉框选择指令类型（ADD/SUB/MUL/DIV/LOAD/STORE）
   - 根据操作类型填写操作数（自动生成对应输入框）
   - 输入验证：寄存器必须为 F1-F32，地址必须为非负整数
   - 点击「Add 指令」添加到队列

3. **单步执行**
   - 点击「步进」按钮推进一个时钟周期
   - 表格自动刷新并高亮变化的单元格（淡黄色）
   - 弹窗显示本周期完成的指令

4. **Debug 模式**
   - 勾选「Debug」复选框查看详细日志
   - 日志面板显示每个周期的内部状态变化

5. **重置模拟**
   - 点击「重置」按钮清空所有状态
# Tomasulo 算法可视化（Python + PyQt）

Tomasulo 算法可视化工具，使用 Python 与 PyQt5 实现。该工具模拟并可视化乱序执行（out-of-order execution）、保留站（Reservation Stations）、寄存器重命名和写回广播（CDB-like broadcast）。
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
- `main.py` — PyQt 前端，渲染并交互：加载指令、步进、重置、Debug 日志。
- `instructions.txt` — 示例指令（可通过 GUI 加载）。
- `test_all.py` — 单元测试脚本。

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

注意：`t.instruction_queue` 中保留了入队条目，UI 使用该队列展示指令生命周期（因此条目不会在写回后自动删除，除非手动清理或重置）。