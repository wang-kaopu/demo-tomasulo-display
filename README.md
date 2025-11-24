# Tomasulo Algorithm Visualization

This project is a Python + PyQt application to visualize the Tomasulo algorithm, which demonstrates out-of-order execution and interactive explanations.

## Features
- **Visualization**: Displays the state of reservation stations, registers, and instruction queue.
- **Interactive**: Double-click to view detailed information about each component.
- **Step-by-step Execution**: Simulate the algorithm clock cycle by clock cycle with a "Step" button.

## Requirements
- Python 3.8+
- PyQt5

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd demo
   ```
2. Install dependencies:
   ```bash
   pip install PyQt5
   ```

## Usage
Run the application:
```bash
python main.py
```

### Loading Instructions
1. Click the "Load Instructions" button.
2. Select a text file containing instructions (one instruction per line).
3. The instructions will be loaded into the simulation and displayed in the UI.

## File Structure
- `main.py`: Entry point for the PyQt application.
- `tomasulo.py`: Core logic for the Tomasulo algorithm.
- `README.md`: Project documentation.

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

## Future Work
- Add more detailed visualization for registers and instruction execution.
- Implement additional instruction types and execution units.