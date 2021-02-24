from dataclasses import dataclass
from pathlib import Path

MODULE_DIR = Path(__file__).parent
SRC_ROOT = MODULE_DIR.parent
PROJECT_ROOT = SRC_ROOT.parent


@dataclass
class Config:
    @classmethod
    def load(cls):
        return cls()
