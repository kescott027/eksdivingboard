from aws_cdk import core as cdk
from compiler import StackCompiler, ConfigsCompiler
# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class InfrastructureStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, configs_root_path, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.configs = None
        self.defaults = None
        self.params = {**kwargs}
        self.stack = None

        defaults_root_path = self.params.pop(
            'defaults_root_path', None)
        self.load_configs(
            configs_path=configs_root_path,
            defaults_path=defaults_root_path)

        self.build_stack()

    def load_configs(self, configs_path, defaults_path=None):
        self.configs = ConfigsCompiler(configs_path)
        if defaults_path:
            self.defaults = ConfigsCompiler(defaults_path)

    def build_stack(self):
        self.stack = StackCompiler(
            stack_configs=self.configs,
            defaults=self.defaults
        )