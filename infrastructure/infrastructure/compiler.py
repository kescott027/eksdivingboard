from structures import StackAccessor, ConstructCollection, StackConstruct
from vpc import AwsVpc


class StackCompiler(object):

    def __init__(self, scope, stack_id, stack_configs, defaults=None):

        self.stack_configs = stack_configs
        self.defaults = defaults
        self.stack = StackAccessor(
            scope=scope,
            id=stack_id,
        )
        self.vpc = None

    def build_stack(self):

        self.construct_builder('vpc', AwsVpc)

    def construct_builder(self, stack_key, builder):
        collection = self.stack.new(stack_key)
        configs = self.stack_configs.get(stack_key, None)
        if configs:
            for construct_id, params in configs:
                collection.new(
                    id=construct_id,
                    base_construct=builder.base_construct,
                    **params
                )


class ConfigsCompiler(object):

    def __init__(self, root_location):
        self.root_locations = root_location
        self.directory_tree = None
        self.configs = {}


