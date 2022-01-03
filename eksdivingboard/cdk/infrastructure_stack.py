import logging
from aws_cdk.core import Stack
from .compiler import ConfigsCompiler

logger = logging.getLogger(__name__)


class InfrastructureStack(Stack):

    def __init__(self, scope, id, configs_root_path, defaults_root_path=None, environments_root_path=None, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.scope = scope
        self.id = id
        self.configs = None
        self.environments = []
        self.defaults = None
        self._config_compiler = None
        self.stacks = {}

        self.load_configs(
            configs_path=configs_root_path,
            defaults_root=defaults_root_path,
            environments_root=environments_root_path
        )

        self.build_stacks()

    def load_configs(self, configs_path, **kwargs):
        defaults_path = kwargs.get('defaults_path', 'not defined')
        logger.info(f'loading stack configs from {configs_path} with defaults {defaults_path}')
        self._config_compiler = ConfigsCompiler(
            deploy_root=configs_path,
            **kwargs
        )

        self.configs = self._config_compiler.configs
        if defaults_path:
            self.defaults = ConfigsCompiler(defaults_path)
        self.environments = self._config_compiler.environments

    def build_stacks(self):
        logger.info('building stack from configs')
        if not self.environments:
            self.environments = [f"{self.id}-default-stack"]
        logger.info(f"building environments: {self.environments}")
        for environment in self.environments:
            stack = EnvironmentStack(self.scope, environment, self.configs)
            stack.build_stack()
            self.stacks[environment] = stack


class EnvironmentStack(Stack):
    def __init__(self, scope, id, configs, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.scope = scope
        self.id = id
        self.configs = configs
        self.constructs = {}

    def build_stack(self):
        logger.debug(f"configs: {self.configs}")
        for key, value in self.configs.items():
            self.constructs[key] = getattr(self, key)(self.configs[key])

    def vpc(self, configs):
        logger.debug('beginning processing vpc items')
        from .vpc import AwsVpc
        return AwsVpc(self, configs)

    def eks_cluster(self, configs):
        logger.debug('beginning processing eks clusters')
        from .eks_cluster import EKSCluster
        return EKSCluster(self, configs)
