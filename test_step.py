from tomasulo import Tomasulo

if __name__ == '__main__':
    t = Tomasulo()
    # setup a simple instruction to exercise allocation and execution
    t.instruction_queue = ["ADD R0 R1 R2"]
    print("Initial instruction queue:", t.get_state()["instruction_queue"]) 
    for cycle in range(1, 6):
        t.step()
        completed = t.get_completed_operations()
        print(f"Cycle {cycle}: completed ->", completed)
        print("RS state:")
        for rs in t.get_state()["reservation_stations"]:
            print(rs)
        print("Registers:")
        for r, data in t.get_state()["registers"].items():
            print(r, data)
        if completed:
            break
