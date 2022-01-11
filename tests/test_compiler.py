from aws_cdk import core as cdk
import logging
from eksdivingboard.cdk.infrastructure_stack import InfrastructureStack
from eksdivingboard.cdk.infrastructure_stack import EnvironmentStack
from os import (
    path, getcwd
)
logger = logging.getLogger(__name__)


def test_app(stack):

    assert stack.configs != {}
    assert stack.stacks['InfrastructureStackDefaultStack'].stack_name == "InfrastructureStackDefaultStack"
    assert isinstance(stack.stacks, dict)
    assert isinstance(stack.stacks['InfrastructureStackDefaultStack'], EnvironmentStack)
