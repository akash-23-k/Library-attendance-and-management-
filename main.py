import sys
from pathlib import Path

# Ensure root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.database import init_db
from ui.app import StudySpaceApp

def main():
    # 1. Initialize SQLite Database
    init_db()

    # 2. Launch Desktop GUI
    app = StudySpaceApp()
    app.mainloop()

if __name__ == "__main__":
    main()
