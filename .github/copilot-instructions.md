# Copilot Instructions for Tomasulo Algorithm Visualization

Welcome to the Tomasulo Algorithm Visualization project! This document provides essential guidelines for AI coding agents to contribute effectively to this codebase.

## Project Overview
This project visualizes the Tomasulo algorithm using Python and PyQt. It simulates out-of-order execution and provides an interactive interface for understanding the algorithm's components and behavior.

### Key Components
- **`main.py`**: Entry point for the PyQt application. Manages the GUI and user interactions.
- **`tomasulo.py`**: Implements the core logic of the Tomasulo algorithm, including reservation stations, instruction queues, and execution units.
- **Instruction Files**: Text files containing one instruction per line, loaded via the GUI.

### Features
- Step-by-step simulation of clock cycles.
- Visualization of reservation stations, registers, and instruction queues.
- Interactive exploration of component details.

## Development Guidelines

### Code Structure
- Follow the existing modular structure: keep GUI logic in `main.py` and algorithm logic in `tomasulo.py`.
- Use clear and descriptive function and variable names to maintain readability.

### Adding Features
- Refer to the `README.md` for a list of planned features and TODOs.
- Ensure new features integrate seamlessly with the GUI and algorithm logic.
- Update the `README.md` and this document to reflect new capabilities.

### Testing
- Test new features thoroughly to ensure correctness and stability.
- Use the GUI to verify visual updates and interactions.

### Performance Optimization
- Optimize table updates and other frequent operations to improve responsiveness.
- Profile the application to identify and address bottlenecks.

## Contribution Examples

### Adding a New Instruction Type
1. Update `tomasulo.py` to handle the new instruction in the algorithm logic.
2. Modify the GUI in `main.py` to display the new instruction type.
3. Test the feature with various instruction files.

### Improving Visualization
1. Enhance the GUI to show additional details (e.g., operand sources, execution progress).
2. Ensure the new visual elements are intuitive and non-intrusive.
3. Test the changes with different simulation scenarios.

## Integration Points
- **PyQt5**: Ensure compatibility with PyQt5 for GUI components.
- **Instruction Files**: Maintain a consistent format for instruction files to ensure compatibility.

## Common Pitfalls
- Avoid mixing GUI and algorithm logic to maintain modularity.
- Ensure all user-facing messages are clear and informative.
- Handle edge cases, such as invalid instruction formats, gracefully.

## Future Work
- Expand the instruction set to include more operations (e.g., MUL, DIV).
- Add support for custom instruction sets and multi-cycle execution.
- Implement advanced visualization features, such as data dependency highlighting.

By following these guidelines, you can contribute effectively to the Tomasulo Algorithm Visualization project. Happy coding!