from tomasulo import Tomasulo

if __name__ == '__main__':
    t = Tomasulo()
    # Use the public API to add instructions (use F-register naming)
    t.add_instruction("ADD F1 F3 F4")
    t.add_instruction("ADD F2 F1 F5")

    print("Initial instruction queue:", [e.get("text") for e in t.instruction_queue])

    # Run for a bounded number of cycles and display state
    for cycle in range(1, 11):
        print(f"Cycle {cycle}: completed -> {t.get_completed_operations()}")
        t.step()
        print("RS state:")
        for rs in t.reservation_stations:
            print(rs)
        print("Registers:")
        for rname in sorted(t.registers.keys()):
            print(rname, t.registers[rname])
        print("---")
