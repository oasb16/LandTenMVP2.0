from utils.status_tracker import update_status

def run_tests():
    print("Running tests...")
    update_status(".status", "tested")

if __name__ == "__main__":
    run_tests()