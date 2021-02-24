from pathlib import Path
import shlex
import subprocess
from typing import List, Union

from de.config import Config, Environment

Step = List[Union[Path, str]]


class StepError(Exception):
    def __init__(self, step: Step, env: Environment):
        self.step = step
        self.env = env


def fmt_step(step: Step):
    return shlex.join([str(s) for s in step])


def steps(steps: List[Step], config: Config):
    for step in steps:
        try:
            subprocess.run([str(s) for s in step], check=True, env=config.step_env)
        except subprocess.CalledProcessError as exc:
            raise StepError(step, config.step_env) from exc
