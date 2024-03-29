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
        self._config_compiler = ConfigsCompiler()
        self._defaults_compiler = None
        self.stacks = {}

        self.load_configs(
            configs_path=configs_root_path,
            defaults_root=defaults_root_path,
            environments_root=environments_root_path
        )

        self.build_stacks()

    def load_configs(self, configs_path, **kwargs):
        logger.debug(f"============== Beginning Configuration Load ==================")
        defaults_path = kwargs.get('defaults_root', 'not defined')
        logger.info(f'loading stack configs from {configs_path} with defaults {defaults_path}')
        self._config_compiler.configure(
            deploy_root=configs_path,
            **kwargs
        )
        self._config_compiler.process_configs()
        logger.debug(f"!!!!!! COMPILER CONFIGS !!!!!! {self._config_compiler.get_configs()}")
        self.configs = self._config_compiler.get_configs()
        logger.debug(f"####### configs ##########\n\t{self.configs}")
        bob = """logger.debug(f"")
        if defaults_path:
            logger.debug(f"######## LOAD DEFAULTS ########")
            self._defaults_compiler = ConfigsCompiler()
            self._defaults_compiler.configure()
            self.defaults = ConfigsCompiler(defaults_path)"""
        self.environments = self._config_compiler.environments
        logger.debug(f"================= End Configuration Load =====================")

    def build_stacks(self):
        logger.info('building stack from configs')
        if not self.environments:
            self.environments = [f"{self.id}DefaultStack"]
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
