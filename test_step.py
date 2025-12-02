from tomasulo import Tomasulo

if __name__ == '__main__':
    t = Tomasulo()
    # setup a simple instruction to exercise allocation and execution
    t.add_instruction("ADD F1 F2 F3")
    print("Initial instruction queue:", [e["text"] for e in t.get_state()["instruction_queue"]]) 
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
