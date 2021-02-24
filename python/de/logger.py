import logging

from de.config import Environment

logger = logging.getLogger(__name__)


def log_env(env: Environment):
    logger.debug(env)
