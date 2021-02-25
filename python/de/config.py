from dataclasses import dataclass, Field, fields
import os
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    get_args,
    get_origin,
    MutableMapping,
    Optional,
    Type,
    Union,
)

from dotenv import load_dotenv

MODULE_DIR = Path(__file__).parent

if "GITHUB_WORKSPACE" in os.environ:
    PROJECT_ROOT = Path(os.environ["GITHUB_WORKSPACE"])
    SRC_ROOT = PROJECT_ROOT / "python"
else:
    SRC_ROOT = MODULE_DIR.parent
    PROJECT_ROOT = SRC_ROOT.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
STUBS_DIR = PROJECT_ROOT / "stubs"
EMOJIS_DIR = PROJECT_ROOT / "emojis"
TESTS_DIR = PROJECT_ROOT / "tests"
DOTENV_PATH = PROJECT_ROOT / ".env"

Environment = MutableMapping[str, str]

Loadable = Union[int, str]

ENV_VAR_LOADERS: Dict[Type[Loadable], Callable[[str], Loadable]] = {
    str: lambda s: s,
    int: int,
}


def is_optional(tp):
    return get_origin(tp) == Union and type(None) in get_args(tp)


def is_env_var(tp):
    return tp != Environment


class ConfigError(Exception):
    pass


class NoEnvVarError(ConfigError):
    pass


class EnvVarLoadError(ConfigError):
    pass


DiscordAPIToken = Optional[str]
DiscordGuildID = int


def _load_env_var(field: Field) -> Any:
    if field.name not in os.environ:
        if is_optional(field.type):
            return None
        elif field.default:
            return field.default
        raise NoEnvVarError(f"Missing environment variable {field.name}!")

    if is_optional(field.type):
        for t in get_args(field.type):
            if t in ENV_VAR_LOADERS:
                loader = ENV_VAR_LOADERS[t]
                break
    elif field.type in ENV_VAR_LOADERS:
        loader = ENV_VAR_LOADERS[field.type]
    else:
        raise EnvVarLoadError(f"Unloadable type {field.type} for field {field.name}!")

    return loader(os.environ[field.name])


@dataclass
class Config:
    DISCORD_API_TOKEN: DiscordAPIToken
    step_env: Environment
    BOT_GUILD_ID: DiscordGuildID = 566333122615181327

    @classmethod
    def load(cls):
        kwargs: Dict[str, Any] = dict()

        load_dotenv(dotenv_path=DOTENV_PATH)

        for field in fields(cls):
            if is_env_var(field.type):
                kwargs[field.name] = _load_env_var(field)

        kwargs["step_env"] = dict(os.environ, MYPYPATH=str(STUBS_DIR))

        return cls(**kwargs)
