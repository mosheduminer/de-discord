from dataclasses import dataclass
import os
from pathlib import Path
from typing import MutableMapping

MODULE_DIR = Path(__file__).parent
SRC_ROOT = MODULE_DIR.parent
PROJECT_ROOT = SRC_ROOT.parent
STUBS_DIR = PROJECT_ROOT / "stubs"


Environment = MutableMapping[str, str]


@dataclass
class Config:
    step_env: Environment

    @classmethod
    def load(cls):
        return cls(step_env=dict(os.environ, MYPYPATH=str(STUBS_DIR)))