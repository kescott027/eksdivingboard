from os import walk, listdir, getcwd
from os.path import dirname, isfile, join
import yaml
from structures import StackAccessor, ConstructCollection, StackConstruct
from vpc import AwsVpc


class StackCompiler(object):

    def __init__(self, scope, stack_id, stack_configs):
        self.stack_configs = stack_configs
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

    def __init__(self,
                 defaults_root=None,
                 default_files=None,
                 common_files_root=None,
                 common_files=None,
                 deploy_root=None,
                 deploy_files=None,
                 environments=None,
                 environments_root=None,
                 environment_files=None
                 ):

        self.configs = {}
        self.variables = {}
        self.environments = environments if environments else []
        self._environment_files = [self.get_single_file(f) for f in environment_files] if default_files else []
        self._environment_files_root = dirname(environments_root) if environments_root else None
        self._default_files = [self.get_single_file(f) for f in default_files] if default_files else []
        self._defaults_root = dirname(defaults_root) if defaults_root else None
        self._common_files = [self.get_single_file(f) for f in common_files] if default_files else []
        self._common_files_root = dirname(common_files_root) if common_files_root else None
        self._deploy_files = [self.get_single_file(f) for f in deploy_files] if default_files else []
        self._deploy_root = dirname(deploy_root) if deploy_root else None
        self._magic_methods = []

        self.process_configs()

    def process_configs(self):
        if self._environment_files_root:
            self._environment_files.extend(self.get_files_recursively(self._environment_files_root))
        if self._defaults_root:
            self._default_files.extend(self.get_files_recursively(self._defaults_root))
        if self._common_files_root:
            self._common_files.extend(self.get_files_recursively(self._common_files_root))
        if self._deploy_root:
            self._deploy_files.extend(self.get_files_recursively(self._deploy_root))
        if self._environment_files:
            self.load_config_files(self._environment_files, self.variables)
        if self._default_files:
            self.load_config_files(self._default_files, self.configs)
        if self._common_files:
            self.load_config_files(self._common_files, self.configs)
        if self._deploy_files:
            self.load_config_files(self._deploy_files, self.configs)
        if self.variables:
            self.configs = self.process_variables(self.configs)

    def process_variables(self, values):
        if isinstance(values, str):
            return self._replace_str_variables(values)
        elif isinstance(values, dict):
            return self._replace_dict_variable(values)
        elif isinstance(values, list):
            return self._replace_list_variables(values)
        raise TypeError(f'Could not identify type of object when evaluating variables: {values}')

    def _replace_str_variables(self, value: str) -> str:
        if '${' not in value:
            return value
        left_delimiter = value.find('${')
        extract = value[left_delimiter + 2]
        if '${' in extract:
            substring = extract[extract.find('${'):]
            value = value.replace(substring, self._replace_str_variables(substring))
        right_delimiter = value.find('}') + 1
        string_to_replace = value[left_delimiter: right_delimiter]
        variable_key = string_to_replace[2:-1]
        try:
            replacement_value = self.variables[variable_key]
        except KeyError:
            raise ValueError(f'Could not locate environment variable {variable_key} referenced.')
        value = value.replace(string_to_replace, replacement_value)
        return value

    def _replace_dict_variable(self, config_dict):
        for key, value in config_dict.items():
            config_dict[key] = self.process_variables(value)
        return config_dict

    def _replace_list_variables(self, config_list):
        for i in range(len(config_list)):
            config_list[i] = self.process_variables(config_list[i])
        return config_list

    def load_config_files(self, file_list, destination_dict):
        for yaml_file in file_list:
            with open(yaml_file, "r") as stream:
                new_configs = yaml.safe_load(stream)
                self.configs = {**destination_dict, **new_configs}

    @staticmethod
    def get_single_file(file_name):
        if file_name[0] != '/' or file_name[0] != '\\':
            return join(getcwd(), file_name)
        else:
            return file_name

    @staticmethod
    def get_directory_files(base_dir):
        return [f for f in listdir(base_dir) if isfile(join(base_dir, f)) and '.yaml' in f]

    @staticmethod
    def get_files_recursively(base_dir):
        file_list = []
        for pathname, dirs, files in walk(base_dir):
            if files:
                if type(files) == str and '.yaml' in files:
                    file_list.extend(files)
                elif type(files) == list:
                    for file in files:
                        if '.yaml' in file:
                            file_list.extend(files)

        return file_list


