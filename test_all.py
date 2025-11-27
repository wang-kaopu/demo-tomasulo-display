import unittest
from tomasulo import Tomasulo

# Merged tests from test_tomasulo_cycles.py, test_tomasulo_more_ops.py, test_tomasulo_edge_cases.py

class TestTomasuloCycles(unittest.TestCase):
    def test_exec_and_write_cycles(self):
        t = Tomasulo()
        t.debug = False
        # simple program: two loads then an add
        instrs = ["LOAD F1 10", "LOAD F2 11", "ADD F3 F1 F2"]
        for ins in instrs:
            t.add_instruction(ins)

        # run until all instructions have been written back or timeout
        max_cycles = 200
        while t.completed_total < len(t.instruction_queue) and t.clock < max_cycles:
            t.step()

        self.assertEqual(t.completed_total, len(t.instruction_queue), msg=f"Completed {t.completed_total} vs expected {len(t.instruction_queue)}")

        for entry in t.instruction_queue:
            self.assertIsNotNone(entry.get('exec_start_cycle'), msg=f"Missing exec_start for {entry}")
            self.assertIsNotNone(entry.get('exec_complete'), msg=f"Missing exec_complete for {entry}")
            self.assertIsNotNone(entry.get('write_cycle'), msg=f"Missing write_cycle for {entry}")
            # ordering: start <= complete <= write
            self.assertLessEqual(entry['exec_start_cycle'], entry['exec_complete'])
            self.assertLessEqual(entry['exec_complete'], entry['write_cycle'])

        # verify arithmetic correctness for ADD (by end of simulation)
        self.assertIn('F3', t.registers)
        self.assertEqual(t.registers['F3']['value'], t.registers['F1']['value'] + t.registers['F2']['value'])


class TestTomasuloMoreOps(unittest.TestCase):
    def test_mul_div_store_cycles_and_results(self):
        t = Tomasulo()
        t.debug = False
        # prepare memory values for loads
        t.memory[10] = 6
        t.memory[11] = 3

        # program: LOAD F1 10; LOAD F2 11; MUL F3 F1 F2; DIV F4 F3 F2; STORE 12 F4
        instrs = ["LOAD F1 10", "LOAD F2 11", "MUL F3 F1 F2", "DIV F4 F3 F2", "STORE 12 F4"]
        for ins in instrs:
            t.add_instruction(ins)

        # run until all instructions written back or timeout
        max_cycles = 500
        while t.completed_total < len(t.instruction_queue) and t.clock < max_cycles:
            t.step()

        # all instructions should have completed
        self.assertEqual(t.completed_total, len(t.instruction_queue))

        # Check each instruction recorded cycles in order
        for entry in t.instruction_queue:
            self.assertIsNotNone(entry.get('exec_start_cycle'))
            self.assertIsNotNone(entry.get('exec_complete'))
            self.assertIsNotNone(entry.get('write_cycle'))
            self.assertLessEqual(entry['exec_start_cycle'], entry['exec_complete'])
            self.assertLessEqual(entry['exec_complete'], entry['write_cycle'])

        # Validate arithmetic results: F3 = F1 * F2 = 6 * 3 = 18; F4 = F3 / F2 = 18 / 3 = 6
        self.assertAlmostEqual(t.registers['F3']['value'], 18)
        self.assertAlmostEqual(t.registers['F4']['value'], 6)

        # Validate STORE wrote memory[12] == F4
        self.assertIn(12, t.memory)
        self.assertAlmostEqual(t.memory[12], t.registers['F4']['value'])


class TestTomasuloEdgeCases(unittest.TestCase):
    def test_divide_by_zero(self):
        t = Tomasulo()
        t.debug = False
        # prepare registers so that divisor is zero
        t.registers['F2']['value'] = 5
        t.registers['F3']['value'] = 0
        t.add_instruction('DIV F4 F2 F3')

        # run
        while t.completed_total < len(t.instruction_queue) and t.clock < 200:
            t.step()

        self.assertEqual(t.completed_total, 1)
        # per implementation, DIV by zero yields 0
        self.assertIn('F4', t.registers)
        self.assertEqual(t.registers['F4']['value'], 0)

    def test_rename_conflict_last_writer_wins(self):
        t = Tomasulo()
        t.debug = False
        # prepare registers
        t.registers['F2']['value'] = 2
        t.registers['F3']['value'] = 3
        t.registers['F4']['value'] = 4
        t.registers['F5']['value'] = 5
        # two back-to-back writes to F1
        t.add_instruction('ADD F1 F2 F3')  # 2+3 = 5
        t.add_instruction('ADD F1 F4 F5')  # 4+5 = 9

        while t.completed_total < len(t.instruction_queue) and t.clock < 200:
            t.step()

        self.assertEqual(t.completed_total, 2)
        # The final value in F1 should be from the second ADD (last writer wins)
        self.assertEqual(t.registers['F1']['value'], 9)

    def test_consecutive_stores_last_store_wins(self):
        t = Tomasulo()
        t.debug = False
        # prepare register values to store
        t.registers['F6']['value'] = 42
        t.registers['F7']['value'] = 99
        # two stores to same address 20
        t.add_instruction('STORE 20 F6')
        t.add_instruction('STORE 20 F7')

        while t.completed_total < len(t.instruction_queue) and t.clock < 200:
            t.step()

        self.assertEqual(t.completed_total, 2)
        # Last store should determine memory[20]
        self.assertIn(20, t.memory)
        self.assertEqual(t.memory[20], t.registers['F7']['value'])


if __name__ == '__main__':
    unittest.main()
