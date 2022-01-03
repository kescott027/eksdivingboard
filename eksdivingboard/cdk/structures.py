import logging

import aws_cdk.core

logger = logging.getLogger(__name__)


class StackConstruct(object):
    def __init__(self, scope, configs):
        self.scope = scope
        self.configs = configs
        self.config_items = []
        self.constructs = {}

    def normalize_configs(self):
        configs_to_process = self.configs.copy()

    @staticmethod
    def set_defaults(options):
        return options

    def build(self):
        logger.debug(f'building {self.construct_type}s')
        for key, options in self.configs.items():
            logger.debug(f'building {self.construct_type} {key}: {options}')
            params = self._construct_params(options)
            self.constructs[key] = self.base_construct(
                self.scope,
                key,
                **params
            )

        return self.constructs

    def __getattr__(self, attr):
        if not super(StackConstruct, self).__getattribute__(attr):
            return self.options.get(attr, None)
        else:
            return getattr(self, attr)

    def _construct_params(self, params):
        logger.debug(f'parsing params: {params}')
        compiled_params = {}
        for key, values in self.set_defaults(params).items():
            if getattr(self, key, None):
                compiled_params[key] = getattr(self, key)(**values)
            else:
                compiled_params[key] = values
        return compiled_params
