from aws_cdk import core as cdk
from compiler import StackCompiler, ConfigsCompiler


class InfrastructureStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, configs_root_path, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.configs = None
        self.id = construct_id
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
            scope=self,
            stack_id=self.id,
            stack_configs=self.configs,
        )