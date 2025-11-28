# Tomasulo 算法可视化（整理版）

这是 `README.md` 的整理版，已去除已完成的 TODO 条目并按模块划分功能与运行说明。

概览

- 语言/框架：Python 3.8+、PyQt5
- 目标：可视化 Tomasulo 算法（乱序执行、重命名、保留站、写回广播）

当前实现

- 支持指令：ADD/SUB/MUL/DIV/LOAD/STORE（每行一条指令）
- 乱序执行：指令在操作数就绪后即可开始执行
- 周期记录：每条指令记录 `issue_cycle`、`exec_start_cycle`、`exec_complete`、`write_cycle`
- 重命名：寄存器 `rename` 使用 `RS:<name>` 格式
- 写回广播：执行完成后在下一周期写回并广播结果
- 单元测试：`test_all.py` 覆盖核心行为与边界情况

模块划分

- `tomasulo.py` — 模拟器核心
  - 指令解析与验证（`parse_instruction_text`, `add_instruction`）
  - 保留站分配（`allocate_reservation_station`）
  - 执行推进与写回（`step`）
  - 状态/日志导出（`get_state`, `get_logs`）

- `main.py` — GUI
  - 三张表：Instruction / Reservation Stations / Registers
  - 控件：Load / Step / Reset / Debug
  - 日志面板（Debug 模式）

- `test_all.py` — 单元测试
  - 包含周期记录、算术结果、STORE 行为、除 0 与重命名冲突等测试

运行

```powershell
pip install PyQt5
python .\main.py
```

运行测试

```powershell
python -m unittest test_all.py -v
```

未完成 / 建议的增强

- ROB（in-order commit）以支持按序提交与回滚
- Store Buffer 以保证内存写入的程序序
- UI 美化：差量刷新、颜色化来源标签、RS 名称显式展示

接下来我可以：

- 把整理后的内容替换到 `README.md`（直接覆盖），或
- 先在新文件上继续扩展为 API 参考/开发者文档

请告诉我是否将 `README_CLEAN.md` 覆盖回 `README.md`。