from pathlib import Path
import shlex
import subprocess
from typing import List, Union

from de.config import Config, Environment, PROJECT_ROOT
from de.logger import logger

Step = List[Union[Path, str]]


class StepError(Exception):
    def __init__(self, step: Step, env: Environment):
        self.step = step
        self.env = env


def fmt_step(step: Step):
    return f"`{shlex.join([str(s) for s in step])}`"


def steps(steps: List[Step], config: Config):
    for step in steps:
        logger.info(f"Running {fmt_step(step)}...")
        try:
            subprocess.run(
                [str(s) for s in step],
                check=True,
                cwd=PROJECT_ROOT,
                env=config.step_env,
            )
        except subprocess.CalledProcessError as exc:
            raise StepError(step, config.step_env) from exc
    logger.info("Cool beans!")
