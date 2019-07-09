import os
import json
import yaml
import urllib.request
from enum import Enum
from typing import Tuple, Mapping
from abc import ABC, abstractmethod
from wrktoolbox.logs import get_app_logger
from rocore.decorators import retry
from rocore.exceptions import InvalidArgument, EmptyArgumentException
from roconfiguration import Configuration, ConfigurationError
from wrktoolbox.web import get_ssl_context


logger = get_app_logger()


class SettingsFormat(Enum):
    JSON = 'json'
    YAML = 'yaml'


class SettingsFileNotFound(InvalidArgument):

    def __init__(self, file_name):
        super().__init__(f'`{file_name}` not found')


def log_retry(exc, attempt):
    if attempt > 3:
        return
    logger.exception('Attempt to downlad settings failed; %s', attempt, exc_info=exc)


class SettingsSource(ABC):

    @abstractmethod
    def is_match(self, value: str) -> bool:
        """Returns a value indicating whether a settings source is handled by this class."""

    @abstractmethod
    def handle(self, value: str) -> Tuple[Mapping, SettingsFormat]:
        """Obtains settings mapping and format from a value."""

    @staticmethod
    def parse(value: str, settings_format: SettingsFormat) -> Mapping:
        # NB: this function violates SRP
        # better code would define a class for each format (low priority here since we support only YAML and JSON)
        if settings_format == SettingsFormat.JSON:
            return json.loads(value)
        if settings_format == SettingsFormat.YAML:
            return yaml.safe_load(value)

        raise RuntimeError(f'Settings format not handled {settings_format}')


class SettingsHttpSource(SettingsSource):

    def is_match(self, value: str) -> bool:
        return value.startswith('http://') or value.startswith('https://')

    @retry(delay=0.5, on_exception=log_retry)
    def _fetch_response(self, source_url):
        return urllib.request.urlopen(source_url, context=get_ssl_context())

    def handle(self, value: str) -> Mapping:
        response = self._fetch_response(value)
        content_type = response.headers['content-type']

        if 'json' in content_type:
            settings_format = SettingsFormat.JSON
        elif 'yaml' in content_type:
            settings_format = SettingsFormat.YAML
        elif '.json' in value:
            settings_format = SettingsFormat.JSON
        elif '.yaml' in value:
            settings_format = SettingsFormat.YAML
        else:
            raise ConfigurationError('Settings must be yaml or json')

        content = response.read().decode('utf8')
        return self.parse(content, settings_format)


class SettingsFileSource(SettingsSource):

    def is_match(self, value: str) -> bool:
        return value.endswith('.json') or value.endswith('.yaml')

    def handle(self, value: str) -> Mapping:
        if not os.path.exists(value):
            raise SettingsFileNotFound(value)

        if not os.path.isfile(value):
            raise InvalidArgument('Invalid settings path: not a file')

        settings_format = SettingsFormat.YAML if value.endswith('.yaml') else SettingsFormat.JSON

        with open(value, mode='rt', encoding='utf8') as settings_file:
            content = settings_file.read()
        return self.parse(content, settings_format)


def normalize_settings(settings_file: str) -> Mapping:
    if not settings_file:
        raise EmptyArgumentException('settings_name')

    for source in [SettingsHttpSource(), SettingsFileSource()]:
        if source.is_match(settings_file):
            return source.handle(settings_file)

    raise InvalidArgument(f'Settings argument `{settings_file}` is not handled.')


def get_configuration(settings_file: str) -> Configuration:
    settings = normalize_settings(settings_file)

    configuration = Configuration(settings)
    configuration.add_environmental_variables('WRKTOOLBOX_', strip_prefix=True)
    return configuration
