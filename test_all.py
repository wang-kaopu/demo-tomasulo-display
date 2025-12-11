import unittest
from tomasulo import Tomasulo

# 合并自 test_tomasulo_cycles.py, test_tomasulo_more_ops.py, test_tomasulo_edge_cases.py 的测试

class TestTomasuloCycles(unittest.TestCase):
    def test_exec_and_write_cycles(self):
        t = Tomasulo()
        t.debug = False
        # 简单程序：两个加载然后一个加法
        instrs = ["LOAD F1 10", "LOAD F2 11", "ADD F3 F1 F2"]
        for ins in instrs:
            t.add_instruction(ins)

        # 运行直到所有指令写回或超时
        max_cycles = 200
        while t.completed_total < len(t.instruction_queue) and t.clock < max_cycles:
            t.step()

        self.assertEqual(t.completed_total, len(t.instruction_queue), msg=f"Completed {t.completed_total} vs expected {len(t.instruction_queue)}")

        for entry in t.instruction_queue:
            self.assertIsNotNone(entry.get('exec_start_cycle'), msg=f"Missing exec_start for {entry}")
            self.assertIsNotNone(entry.get('exec_complete'), msg=f"Missing exec_complete for {entry}")
            self.assertIsNotNone(entry.get('write_cycle'), msg=f"Missing write_cycle for {entry}")
            # 顺序：开始 <= 完成 <= 写回
            self.assertLessEqual(entry['exec_start_cycle'], entry['exec_complete'])
            self.assertLessEqual(entry['exec_complete'], entry['write_cycle'])

        # 验证 ADD 的算术正确性（在模拟结束时）
        self.assertIn('F3', t.registers)
        self.assertEqual(t.registers['F3']['value'], t.registers['F1']['value'] + t.registers['F2']['value'])


class TestTomasuloMoreOps(unittest.TestCase):
    def test_mul_div_store_cycles_and_results(self):
        t = Tomasulo()
        t.debug = False
        # 为加载准备内存值
        t.memory[10] = 6
        t.memory[11] = 3

        # 程序：LOAD F1 10; LOAD F2 11; MUL F3 F1 F2; DIV F4 F3 F2; STORE 12 F4
        instrs = ["LOAD F1 10", "LOAD F2 11", "MUL F3 F1 F2", "DIV F4 F3 F2", "STORE 12 F4"]
        for ins in instrs:
            t.add_instruction(ins)

        # 运行直到所有指令写回或超时
        max_cycles = 500
        while t.completed_total < len(t.instruction_queue) and t.clock < max_cycles:
            t.step()

        # 所有指令应该已完成
        self.assertEqual(t.completed_total, len(t.instruction_queue))

        # 检查每条指令按顺序记录的周期
        for entry in t.instruction_queue:
            self.assertIsNotNone(entry.get('exec_start_cycle'))
            self.assertIsNotNone(entry.get('exec_complete'))
            self.assertIsNotNone(entry.get('write_cycle'))
            self.assertLessEqual(entry['exec_start_cycle'], entry['exec_complete'])
            self.assertLessEqual(entry['exec_complete'], entry['write_cycle'])

        # 验证算术结果：F3 = F1 * F2 = 6 * 3 = 18; F4 = F3 / F2 = 18 / 3 = 6
        self.assertAlmostEqual(t.registers['F3']['value'], 18)
        self.assertAlmostEqual(t.registers['F4']['value'], 6)

        # 验证 STORE 将 memory[12] 写为 F4
        self.assertIn(12, t.memory)
        self.assertAlmostEqual(t.memory[12], t.registers['F4']['value'])


class TestTomasuloEdgeCases(unittest.TestCase):
    def test_divide_by_zero(self):
        t = Tomasulo()
        t.debug = False
        # 准备寄存器使除数为零
        t.registers['F2']['value'] = 5
        t.registers['F3']['value'] = 0
        t.add_instruction('DIV F4 F2 F3')

        # 运行
        while t.completed_total < len(t.instruction_queue) and t.clock < 200:
            t.step()

        self.assertEqual(t.completed_total, 1)
        # 根据实现，除以零得到 0
        self.assertIn('F4', t.registers)
        self.assertEqual(t.registers['F4']['value'], 0)

    def test_rename_conflict_last_writer_wins(self):
        t = Tomasulo()
        t.debug = False
        # 准备寄存器
        t.registers['F2']['value'] = 2
        t.registers['F3']['value'] = 3
        t.registers['F4']['value'] = 4
        t.registers['F5']['value'] = 5
        # 连续两次写入 F1
        t.add_instruction('ADD F1 F2 F3')  # 2+3 = 5
        t.add_instruction('ADD F1 F4 F5')  # 4+5 = 9

        while t.completed_total < len(t.instruction_queue) and t.clock < 200:
            t.step()

        self.assertEqual(t.completed_total, 2)
        # F1 的最终值应该来自第二个 ADD（最后写入者胜出）
        self.assertEqual(t.registers['F1']['value'], 9)

    def test_consecutive_stores_last_store_wins(self):
        t = Tomasulo()
        t.debug = False
        # 准备要存储的寄存器值
        t.registers['F6']['value'] = 42
        t.registers['F7']['value'] = 99
        # 两次存储到相同地址 20
        t.add_instruction('STORE 20 F6')
        t.add_instruction('STORE 20 F7')

        while t.completed_total < len(t.instruction_queue) and t.clock < 200:
            t.step()

        self.assertEqual(t.completed_total, 2)
        # 最后的存储应该决定 memory[20] 的值
        self.assertIn(20, t.memory)
        self.assertEqual(t.memory[20], t.registers['F7']['value'])


class TestTomasuloDependencies(unittest.TestCase):
    """测试指令依赖关系处理 (from test_depend.py)"""
    def test_data_dependency_handling(self):
        """测试数据依赖：第二条指令依赖第一条指令的结果"""
        t = Tomasulo()
        t.debug = False
        # 初始化寄存器
        t.registers['F3']['value'] = 3
        t.registers['F4']['value'] = 4
        t.registers['F5']['value'] = 5
        
        # ADD F1 F3 F4: F1 = 3 + 4 = 7
        # ADD F2 F1 F5: F2 = F1 + 5 = 7 + 5 = 12 (依赖F1)
        t.add_instruction("ADD F1 F3 F4")
        t.add_instruction("ADD F2 F1 F5")

        # 运行直到完成
        max_cycles = 200
        while t.completed_total < len(t.instruction_queue) and t.clock < max_cycles:
            t.step()

        # 验证所有指令完成
        self.assertEqual(t.completed_total, 2)
        
        # 验证结果
        self.assertEqual(t.registers['F1']['value'], 7)
        self.assertEqual(t.registers['F2']['value'], 12)
        
        # 验证第二条指令的 exec_start 在第一条指令的 write_cycle 之后
        entry1 = t.instruction_queue[0]
        entry2 = t.instruction_queue[1]
        self.assertIsNotNone(entry1.get('write_cycle'))
        self.assertIsNotNone(entry2.get('exec_start_cycle'))
        # 第二条指令必须等待第一条指令写回后才能开始执行
        self.assertGreaterEqual(entry2['exec_start_cycle'], entry1['write_cycle'])


class TestTomasuloStepByStep(unittest.TestCase):
    """测试逐步执行和状态追踪 (from test_step.py)"""
    def test_step_by_step_execution(self):
        """测试逐周期执行并验证状态变化"""
        t = Tomasulo()
        t.debug = False
        # 初始化寄存器
        t.registers['F2']['value'] = 10
        t.registers['F3']['value'] = 20
        
        # ADD F1 F2 F3: F1 = 10 + 20 = 30
        t.add_instruction("ADD F1 F2 F3")
        
        # 验证初始状态
        self.assertEqual(len(t.instruction_queue), 1)
        self.assertFalse(t.instruction_queue[0].get('issued', False))
        
        # 逐步执行并验证
        initial_state_checked = False
        execution_started = False
        
        max_cycles = 20
        for cycle in range(1, max_cycles + 1):
            t.step()
            state = t.get_state()
            
            # 第一个周期后，指令应该被发射
            if cycle == 1:
                self.assertTrue(t.instruction_queue[0].get('issued'))
                # 检查是否有RS被占用
                busy_rs = [rs for rs in state['reservation_stations'] if rs.get('busy')]
                self.assertGreater(len(busy_rs), 0)
                initial_state_checked = True
            
            # 检查是否开始执行
            if not execution_started:
                for rs in state['reservation_stations']:
                    if rs.get('started'):
                        execution_started = True
                        break
            
            # 如果完成，验证结果
            if t.completed_total > 0:
                self.assertEqual(t.registers['F1']['value'], 30)
                self.assertFalse(t.registers['F1'].get('busy', True))
                break
        
        # 确保指令完成
        self.assertEqual(t.completed_total, 1)
        self.assertTrue(initial_state_checked)


if __name__ == '__main__':
    unittest.main()
