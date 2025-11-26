from tomasulo import Tomasulo

if __name__ == '__main__':
    t = Tomasulo()
    # produce R1, then consume R1
    t.instruction_queue = [
        "ADD R1 R3 R4",  # will produce R1
        "ADD R2 R1 R5",  # depends on R1
    ]
    print("Initial instruction queue:", t.get_state()["instruction_queue"])
    for cycle in range(1, 8):
        t.step()
        completed = t.get_completed_operations()
        print(f"Cycle {cycle}: completed ->", completed)
        print("Reservation stations:")
        for rs in t.get_state()["reservation_stations"]:
            print(rs)
        print("Registers:")
        for r, data in t.get_state()["registers"].items():
            print(r, data)
        print("---")
