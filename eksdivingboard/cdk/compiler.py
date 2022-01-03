import os
from os import listdir, getcwd
from os.path import isfile, join, dirname, isabs
import yaml
import glob
import logging

logger = logging.getLogger(__name__)


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

        self.base_path = os.getcwd()
        self.configs = {}
        self.variables = {}
        self.environments = environments if environments else []
        self._environment_files = [self.get_single_file(f) for f in environment_files] if environment_files else []
        self._default_files = [self.get_single_file(f) for f in default_files] if default_files else []
        self._common_files = [self.get_single_file(f) for f in common_files] if common_files else []
        self._deploy_files = [self.get_single_file(f) for f in deploy_files] if deploy_files else []
        self._environment_files_root = self._format_dir_path(
            environments_root, '_environment_files_root') if environments_root else None
        self._defaults_root = self._format_dir_path(
            defaults_root, '_defaults_root') if defaults_root else None
        self._common_files_root = self._format_dir_path(
            common_files_root, '_common_files_root') if common_files_root else None
        self._deploy_root = self._format_dir_path(
            deploy_root, '_deploy_root') if deploy_root else None
        self._magic_methods = []

        self._get_files_by_directory_root()
        self.process_configs()
        logger.info(f"we've generated {self.configs}")

    def process_configs(self):
        config_files = {
            '_environment_files': 'variables',
            '_default_files': 'configs',
            '_common_files': 'configs',
            '_deploy_files': 'configs',
        }
        for file_list, config_store in config_files.items():
            if getattr(self, file_list):
                logger.debug(f'loading {file_list}')
                self.load_config_files(
                    getattr(self, file_list),
                    config_store
                )

    def process_variables(self, values):
        if not self.variables:
            logger.debug('No variables to process')
            return

        logger.debug('processing variables')

        if isinstance(values, str):
            logger.debug(f'processing string variables {values}')
            return self._replace_str_variables(values)
        elif isinstance(values, dict):
            logger.debug(f'processing dictionary variables {values}')
            return self._replace_dict_variable(values)
        elif isinstance(values, list):
            logger.debug(f'processing list variables {values}')
            return self._replace_list_variables(values)
        raise TypeError(f'Could not identify type of object when evaluating variables: {values}')

    def _format_dir_path(self, path, attribute):
        if isabs(path):
            logger.info(f'setting {attribute} attribute to {path}')
            new_path = dirname(path)
            return new_path
        else:
            new_path = os.path.join(self.base_path, path)
            logger.info(f'setting {attribute} attribute to {new_path}')
            return new_path

    def _get_files_by_directory_root(self):
        logger.debug(f'deploy_root: {self._deploy_root}')

        recursive_file_roots = [
            {'source_attribute': self._environment_files_root,
             'source_type': 'environment',
             'destination_attribute': self._environment_files,
             'directory_exclusions': None
             },
            {'source_attribute': self._defaults_root,
             'source_type': 'default',
             'destination_attribute': self._default_files,
             'directory_exclusions': [
                 self._deploy_root,
                 self._environment_files_root,
             ]},
            {'source_attribute': self._common_files_root,
             'source_type': 'common',
             'destination_attribute': self._common_files,
             'directory_exclusions': [
                 self._deploy_root,
                 self._environment_files_root,
             ]},
            {'source_attribute': self._deploy_root,
             'source_type': 'deploy',
             'destination_attribute': self._deploy_files,
             'directory_exclusions': [
                 self._common_files_root,
                 self._defaults_root,
                 self._environment_files_root
             ]}
        ]

        for dir_root in recursive_file_roots:
            source = dir_root['source_attribute']
            source_type = dir_root['source_type']
            destination = dir_root['destination_attribute']
            exclusions = [
                item for item in dir_root['directory_exclusions'] if item] if dir_root.get(
                'directory_exclusions', None) else None
            if source:
                logger.info(f'loading {source_type} files from {source}')
                logger.debug(f'preparing exclusions: {exclusions}')
                all_files_found = self.get_files_recursively(
                        source,
                        exclusions
                    )
                destination.extend(all_files_found)
            else:
                logger.debug(f'no values found for {source_type}')

    @staticmethod
    def get_files_recursively(base_dir, exclusions=None):
        # exclusions = [item for item in maybe_exclude if item] if maybe_exclude else None
        logger.info(f'getting files recursively for directory {base_dir} with exclusions: {str(exclusions)}')
        all_file_list = glob.glob(base_dir + '/**/*.yaml', recursive=True)
        logger.debug(f'initial file lists: {all_file_list}')
        if not exclusions:
            logger.debug(f'no file exclusions, returning file list: {all_file_list}')
            filtered_list = all_file_list
        else:
            logger.info(f'excluding the following directories: {exclusions}')
            filtered_list = [file for file in all_file_list if not any(match in file for match in exclusions)]
            logger.debug(f'returning files: {filtered_list}')
        return filtered_list

    @staticmethod
    def get_single_file(file_name):
        if file_name[0] != '/' or file_name[0] != '\\':
            return join(getcwd(), file_name)
        else:
            return file_name

    @staticmethod
    def get_directory_files(base_dir):
        return [f for f in listdir(base_dir) if isfile(join(base_dir, f)) and '.yaml' in f]

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

    def load_config_files(self, file_list, destination_store):
        logger.debug(f'loading file list {file_list} to {destination_store}')
        destination_dict = getattr(self, destination_store).copy()
        for yaml_file in file_list:
            try:
                with open(yaml_file, "r") as stream:
                    new_configs = yaml.safe_load(stream)
                    logger.info(f" loading the following configs: {new_configs}")
                    destination_dict = {**destination_dict, **new_configs}
                    logger.info(f"combined dict: {destination_dict}")
            except FileNotFoundError:
                raise FileNotFoundError(f'cannot find file {yaml_file} in {str(os.getcwd())}')
        setattr(self, destination_store, destination_dict)
