import yaml
from pathlib import Path

from config.const import *

project_root_dir = Path(__file__).parent.parent

cfg = yaml.safe_load(open(f"{project_root_dir}/config/config.yml", 'r'))

