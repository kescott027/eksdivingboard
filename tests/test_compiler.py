from aws_cdk import core as cdk
import logging
from eksdivingboard.cdk.infrastructure_stack import InfrastructureStack
from os import (
    path, getcwd
)
logger = logging.getLogger(__name__)


def test_app(stack):

    assert stack.stacks['InfrastructureStackDefaultStack'].stack_name == "InfrastructureStackDefaultStack"
    assert stack.configs != {}
    assert stack.stacks == ['InfrastructureStackDefaultStack']
