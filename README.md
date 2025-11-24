# Tomasulo 算法可视化

本项目是一个基于 Python 和 PyQt 的应用程序，用于可视化 Tomasulo 算法，展示乱序执行和交互式解释。

## 功能
- **可视化**：显示保留站、寄存器和指令队列的状态。
- **交互式**：双击查看每个组件的详细信息。
- **逐步执行**：通过“Step”按钮模拟算法的时钟周期。

## 环境要求
- Python 3.8+
- PyQt5

## 安装
1. 克隆仓库：
   ```bash
   git clone <repository-url>
   cd demo
   ```
2. 安装依赖：
   ```bash
   pip install PyQt5
   ```

## 使用方法
运行应用程序：
```bash
python main.py
```

### 加载指令
1. 点击“Load Instructions”按钮。
2. 选择一个包含指令的文本文件（每行一条指令）。
3. 指令将被加载到模拟中并显示在界面中。

## 文件结构
- `main.py`：PyQt 应用程序的入口点。
- `tomasulo.py`：Tomasulo 算法的核心逻辑。
- `README.md`：项目文档。

## TODO

### 未满足的功能需求

1. **乱序发射与乱序完成**：
   - 当前实现中，指令是按队列顺序发射的，未实现乱序发射。
   - 需要支持根据操作数的可用性动态调整发射顺序。

2. **指令状态可视化**：
   - 在界面中显示每条指令的状态（等待、执行中、完成）。
   - 高亮当前正在执行的指令。

3. **保留站详细信息**：
   - 双击保留站时，显示更详细的信息，例如操作数的来源（寄存器或保留站）。

4. **时钟同步解释**：
   - 在每个时钟周期结束时，显示当前周期完成的操作及其影响。

5. **重置功能**：
   - 添加一个按钮，允许用户重置模拟状态。

6. **更多指令支持**：
   - 当前仅支持 ADD、SUB、LOAD 和 STORE 指令。
   - 需要扩展支持更多指令类型，例如 MUL、DIV。

7. **错误处理**：
   - 如果加载的指令格式不正确，需在界面中提示错误信息。

8. **性能优化**：
   - 当前的 `update_table` 方法在每次更新时会重置整个表格，可能影响性能。
   - 优化更新逻辑，仅更新发生变化的部分。

1. **寄存器重命名可视化**：
   - 显示寄存器的当前状态，包括值和保留站的映射。

2. **数据相关性处理**：
   - 在界面中高亮显示 RAW（读后写）、WAR（写后读）、WAW（写后写）相关性及其解决方案。

3. **保留站详细信息**：
   - 展示保留站的详细信息，包括当前指令和操作数。

4. **功能单元状态**：
   - 显示功能单元的状态，包括执行进度和延迟。

5. **指令状态更新**：
   - 提供一个详细的指令状态表，每个周期动态更新。

6. **自定义指令集**：
   - 允许用户输入自定义指令集进行模拟。

7. **多周期执行**：
   - 增加一次执行多个周期的功能。

8. **性能统计**：
   - 包括每周期完成的指令数、执行时间等指标。

9. **执行回溯**：
   - 允许用户回退到之前的周期。

10. **帮助和文档**：
    - 在应用程序中添加帮助部分，提供使用说明和常见问题解答。


###详细问题清单（可直接定位与修复建议）

1. 缺失结果广播 / 等待操作数更新（严重）

现状：当某 RS 完成并把值写回寄存器（在 step() 的最后写回 dest），并没有遍历其他 RS 来检查哪些 RS 正在等待该寄存器的结果并把对应的 src*_ready 设为 True，也没有把真正的值/来源传播给它们。
影响：如果 allocate 时源寄存器被标记为 busy（即之前某指令分配了该寄存器为目的），等待该寄存器的保留站将标记 src_ready 为 False，但没有任何机制在写回时把它们唤醒；结果会出现“永远等待”的情况。
建议修复：实现写回广播逻辑：在一个 RS 完成时（或写回寄存器后）：
把寄存器写回并清除 registers[dest]["busy"] / rename。
遍历所有其他 RS：如果某个 RS 引用了该寄存器（最好是通过 src1_source/src2_source 存储为生产该值的 RS 名称或寄存器名），则将它们的 src*_ready = True 并把该 operand 的具体值记录到 RS（例如 src1_value），这样下个周期该 RS 可以被执行。
更好地做法：在 allocate_reservation_station() 中，对源操作数，如果寄存器 busy，则把 srcX_source 赋值为生产者（例如寄存器的 rename 字段或者查找哪个 RS 产生该寄存器），否则标记为来自寄存器并填 srcX_value。

2. 未实现寄存器重命名映射（中等严重）

现状：分配时把目标寄存器的 busy 设为 True，但没有设置 registers[dest]["rename"] 指向哪个 RS 会生成结果（只是在其他地方偶尔使用 rename 键）。因此无法追踪哪个 RS 将在未来生产该寄存器的值。
影响：无法在分配时把 srcX_source 设为生产该值的 RS 名称，也无法在写回时对等待的 RS 做精确更新。
建议修复：在 allocate_reservation_station() 成功分配到某个 RS（比如 RSi）后，设置 self.registers[dest]["busy"] = True 并 self.registers[dest]["rename"] = rs["name"]。写回时把 registers[dest]["rename"] = None 并 busy = False。

3. src1_source/src2_source 的语义与赋值不够清晰（低-中）

现状：代码里把 src1_source = src1 if self.registers[src1]["busy"] else "Reg". 这样当寄存器 busy 时，src1_source 被设置为寄存器名（例如 "R1"），但这并没有告诉 UI 或其他 RS 谁是生产者（应为 RS 名称或重命名映射）。另外 LOAD 分配里设置 src1_source: "Imm/Addr", src2_source: "N/A"，这没问题，但应统一 source 字段的语义（例如："Reg"|"RS:RS0"|"Imm"）。
建议修复：统一约定 srcX_source 存储两类值之一：若来自寄存器立即可用则 "Reg"（并放置 srcX_value），若来自某 RS 则存 RSi 或 rename 字符串，便于在写回时匹配和更新。

4. 写回顺序与日志记录（已部分修复）

现状：我已把日志捕获到变量 instr_text 和 result_val，并在清空 RS 前记录；这是正确的。之前代码曾在清除字段后尝试读取 rs['instruction'] 导致为空。
建议：保持当前做法（先 capture，再 clear，再广播/日志），并确保广播发生在清空前或使用捕获的值进行广播匹配。

5. 不统一的数据结构（字符串 vs dict）（可改进）

现状：指令在队列中以字符串表示，导致在多个地方重复解析（split）并易出错。RS 用 dict 存储字符串 instruction。registers 字段没有统一 rename/value/busy 初始字段（有 value 和 busy，但 rename 在某些时候被引用）。
建议：把指令解析为小 dict/object（{op, dest, src1, src2, imm}）在入队时解析一次；或在 allocate 时解析并把解析结果保存到 RS 的字段里，减少重复 split，也便于错误处理。

6. STORE 指令在 step 中未处理（功能缺失）

现状：execute_instruction() 处理了 STORE，但 step() 中只处理了 ADD/SUB/LOAD 的执行/写回逻辑。STORE 在 RS 完成时没有写内存的逻辑（step 中_LOAD 对 memory 读取，但 STORE 执行未实现）。
建议：在 step() 完成分支中处理 STORE：当 op == 'STORE'，将值写入 memory，并记录完成日志。

7. 操作延迟一律为 3（简化）

现状：所有操作都使用 time_left = 3. 这是可接受的简化，但限制了展示多周期/不同功能单元的差异。
建议：考虑为不同指令类型配置不同执行延迟（例如 MUL 更长，LOAD 可能受内存延迟影响），并把它放在集中配置中。

8. 无错误/格式校验（健壮性）

现状：allocate_reservation_station() 假设 instruction.split() 返回足够字段。若加载格式不对，会抛异常或错误行为。
建议：在 add_instruction 或 load_instructions 时做解析与校验，提示或忽略错误行。

## 未来工作
- 为寄存器和指令执行添加更详细的可视化。
- 实现更多的指令类型和执行单元。