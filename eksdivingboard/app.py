# import os
from os import (
    path, getcwd
)
from aws_cdk import core as cdk
from cdk.infrastructure_stack import InfrastructureStack
import logging

logger = logging.getLogger(__name__)

current_path = getcwd()
configs_root = path.join(current_path, "../deployments/example/")
defaults_root = path.join(current_path, "../deployments/defaults/")
environments_root = path.join(current_path, "../deployments/example/environments/")
app = cdk.App()
InfrastructureStack(
    scope=app,
    id="InfrastructureStack",
    configs_root_path=configs_root,
    defaults_root_path=defaults_root,
    environments_root_path=environments_root,
    )


app.synth()
