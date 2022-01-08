# import os
from aws_cdk import core as cdk
from cdk.infrastructure_stack import InfrastructureStack


app = cdk.App()
InfrastructureStack(
    scope=app,
    construct_id="InfrastructureStack",
    configs_root_path="/Users/kylescott/git/eksdivingboard/deployments/example.yaml"
    )
app.synth()
