from aws_cdk import core as cdk
from eksdivingboard.cdk.infrastructure_stack import InfrastructureStack
import logging

logger = logging.getLogger(__name__)


app = cdk.App()
new_stack = InfrastructureStack(
    scope=app,
    id="InfrastructureStack",
    configs_root_path="fixtures/example",
    defaults_root_path="fixtures/defaults",
    environments_root_path="fixtures/example/environments",
    )
print(new_stack.configs)

app.synth()
print(new_stack.stacks)
print(new_stack.stacks.get('InfrastructureStack-default-stack').constructs)