import sys
from src.config import project_root_dir

sys.path.append(f"{project_root_dir}/booker")

from src.app import *


if __name__ == "__main__":
    AppContext().run()
