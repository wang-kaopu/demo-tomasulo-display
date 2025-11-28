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
- UI 美化与性能优化（差量刷新、颜色化来源标签等）。

如需我继续：
- 我可以把 README 再扩展为函数/API 参考，或
- 直接开始实现 ROB 或 Store Buffer（并附带相应测试）。
请告诉我你的优先级。
# Tomasulo 算法可视化

一个用 Python + PyQt 实现的 Tomasulo 算法教学与可视化工具，演示乱序执行、保留站、寄存器重命名与写回流程。

**当前实现（摘要）**

- 支持指令解析与加载（每行一条指令，支持 `ADD/SUB/MUL/DIV/LOAD/STORE`）。
- 支持乱序执行：指令在操作数就绪后开始执行（保留站/重命名避免 WAR/WAW）。
- 记录并显示每条指令的关键周期：`issue_cycle`、`exec_start_cycle`、`exec_complete`、`write_cycle`。
- 寄存器重命名：寄存器的 `rename` 以 `RS:<name>` 格式保存，用于广播/等待匹配。
- 写回广播：执行完成后在下一个周期写回并广播结果到等待的保留站。
- 单元测试：包含用例覆盖多周期指令、MUL/DIV/STORE、边界情况（除 0、重命名冲突、连续 STORE）并已合并为 `test_all.py`。

**尚未实现 / 可选增强（简要）**

# Tomasulo 算法可视化

一个用 Python + PyQt 实现的 Tomasulo 算法教学与可视化工具，演示乱序执行、保留站、寄存器重命名与写回流程。

**当前实现（摘要）**

- 支持指令解析与加载（每行一条指令，支持 `ADD/SUB/MUL/DIV/LOAD/STORE`）。
- 支持乱序执行：指令在操作数就绪后开始执行（保留站/重命名避免 WAR/WAW）。
- 记录并显示每条指令的关键周期：`issue_cycle`、`exec_start_cycle`、`exec_complete`、`write_cycle`。
- 寄存器重命名：寄存器的 `rename` 以 `RS:<name>` 格式保存，用于广播/等待匹配。
- 写回广播：执行完成后在下一个周期写回并广播结果到等待的保留站。
- 单元测试：包含用例覆盖多周期指令、MUL/DIV/STORE、边界情况（除 0、重命名冲突、连续 STORE）并已合并为 `test_all.py`。

**尚未实现 / 可选增强（简要）**

- 精确的重排序缓冲区（ROB）与 in-order 提交（当前写回即为可见提交，未实现回滚/精确异常）。
- Store Buffer / 内存按程序序提交保障（当前 STORE 在写回时直接写内存，可能导致写入顺序与提交策略需改进）。
- UI 美化：对 `RS:<name>`、`Reg`、`Imm` 等来源做颜色/样式提示；更紧凑的表格更新策略以提升性能。

---

## 功能模块划分

- `tomasulo.py` — 模拟器核心（Simulator Core）
  - 指令解析与入队（`add_instruction`, `parse_instruction_text`）。
  - 保留站管理与分配（`allocate_reservation_station`）。
  - 执行周期推进（`step`）包括开始执行、执行完成、写回与广播。
  - 内部日志与状态导出（`log`, `get_logs`, `get_state`）。
  - 数据结构：保留站 (`reservation_stations`)、寄存器表 (`registers`)、指令队列 (`instruction_queue`)、模拟内存 (`memory`)。

- `main.py` — PyQt 前端（GUI）
  - 负责显示三张主要表：指令状态表、保留站、浮点寄存器状态表。
  - 控件：Load / Step / Reset / Debug 开关；日志面板（Debug 打开时可见）。
  - 从 `tomasulo` 获取状态并渲染表格；支持加载指令文本文件并进行格式校验。

- `test_all.py` — 单元测试集合
  - 合并并包含针对周期记录、算术正确性、STORE 行为及边缘情况的测试。
  - 运行方法见下文“运行测试”。

- `instructions.txt`（示例）
  - 示例指令文件（每行一条）。

---

## 运行

确保安装了 Python（3.8+）和 PyQt5：

```powershell
pip install PyQt5
```

运行应用：

```powershell
python .\\main.py
```

窗口会显示 Instruction/RS/Register 三张表；使用 `Load Instructions` 加载指令文件，`Step` 按周期推进，`Debug` 开启后会显示内部日志。

---

## 运行测试

在项目根目录运行：

```powershell
# 运行合并的单元测试文件
python -m unittest test_all.py -v

# 或使用 discover 自动发现测试
python -m unittest discover -v
```

---

## 开发说明与扩展建议

- 如果需要实现 ROB（in-order commit）：建议在 `tomasulo.py` 中添加 ROB 队列，改写写回流程为先把结果写入 ROB 条目，只有当 ROB 到达头部并且无异常时才真正提交到寄存器/内存并清除重命名。并为 STORE 单独实现按序提交缓冲区。

- UI 性能：当前表格在每次更新时重建，若数据量增大建议改为差量更新或只刷新发生变化的行。

- 日志与调试：前端的 Debug 模式会拉取模拟器内部日志（`get_logs`）；可以加更多结构化日志（JSON）便于筛选和可视化。

---

如果你希望我：
- 把 `README` 中再加入更详细的 API/函数说明，或
- 现在添加 ROB/Store Buffer 的实现草案并一起修改测试，
告诉我你的优先级，我来继续实现。