import functools
from typing import Any, Callable, List

import click
import click_log

from de.config import Config, PROJECT_ROOT, SRC_ROOT
from de.logger import logger
from de.steps import fmt_step, Step, StepError, steps as _steps

click_log.basic_config(logger)


CLIHandler = Callable[..., Any]


def capture(fn: CLIHandler) -> CLIHandler:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except StepError as exc:
            logger.error(f"Step {fmt_step(exc.step)} failed!")
            logger.debug(exc.env)
        except Exception:
            logger.exception("FLAGRANT SYSTEM ERROR")
            raise click.Abort()

    return wrapper


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = Config.load()


def run_steps(name: str, steps: List[Step]):
    def command(config):
        _steps(steps, config)

    command.__name__ = name

    return cli.command()(
        click_log.simple_verbosity_option(logger)(capture(click.pass_obj(command)))
    )


FORMAT_STEP: Step = ["black", PROJECT_ROOT]
LINT_STEP: Step = ["flake8", PROJECT_ROOT]
TYPE_CHECK_STEP: Step = ["mypy", SRC_ROOT]

format_ = run_steps("format", [FORMAT_STEP])
type_check = run_steps("type_check", [TYPE_CHECK_STEP])
lint = run_steps("lint", [TYPE_CHECK_STEP, LINT_STEP])

if __name__ == "__main__":
    cli()
