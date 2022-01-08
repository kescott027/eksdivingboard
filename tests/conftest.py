import pytest
from aws_cdk import core as cdk
import logging
from eksdivingboard.cdk.infrastructure_stack import InfrastructureStack
from os import (
    path, getcwd
)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def app():
    return cdk.App()


@pytest.fixture(scope="session")
def stack(app):
    current_path = getcwd()
    configs_root = path.join(current_path, "tests/fixtures/example")
    defaults_root = path.join(current_path, "tests/fixtures/defaults")
    environments_root = path.join(current_path, "tests/fixtures/example/environments")

    return InfrastructureStack(
        scope=app,
        id="InfrastructureStack",
        configs_root_path=configs_root,
        # defaults_root_path=defaults_root,
        environments_root_path=environments_root,
    )


@pytest.fixture(scope="session")
def synth(app, stack):
    if stack:
        return app.synth()
