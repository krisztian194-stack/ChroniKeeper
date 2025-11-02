from memory_engine import MemoryEngine

def run_cli():
    engine = MemoryEngine()
    while True:
        cmd = input("ChroniKeeper> ").strip().lower()
        if cmd == "show chars":
            print(engine.memory["characters"])
        elif cmd == "show world":
            print(engine.memory["world"])
        elif cmd == "show events":
            for e in engine.memory["events"]:
                print(e)
        elif cmd == "exit":
            break
        else:
            print("Commands: show chars | show world | show events | exit")
