import os
import sys
import click
# noinspection PyUnresolvedReferences
from wrktoolbox import stores, version
from wrktoolbox.benchmarks import BenchmarkSuite
# noinspection PyUnresolvedReferences
from wrktoolbox.goals import *
from wrktoolbox.logs import get_app_logger
from wrktoolbox.commands import get_configuration, SettingsFileNotFound
from rocore.exceptions import InvalidArgument
from roconfiguration import ConfigurationError


logger = get_app_logger()


def run_core(settings):
    sys.path.insert(0, '.')

    try:
        configuration = get_configuration(settings)
    except SettingsFileNotFound as e:
        logger.info(f'[*] Error: {e}')
        exit(1)
    except (InvalidArgument, ConfigurationError):
        logger.exception('An error occurred while loading configuration')
        exit(2)
        return

    logger.info(f'Using settings file {settings}')

    try:
        suite = BenchmarkSuite.from_dict(configuration.values)
    except Exception:
        logger.exception('An error occurred while preparing the suite of benchmarks')
        exit(1)
        return

    suite.configuration = configuration

    if 'metadata' in configuration:
        suite.metadata = configuration.metadata.values

    if not suite.configurations:
        logger.error('Missing benchmark configurations, exiting')
        exit(1)
        return

    if suite.plugins:
        logger.info('Loaded plugins:')
        for plugin in suite.plugins:
            logger.info(f' - {plugin.name}')

        logger.info('---')

    if not suite.goals and not any(configuration.goals for configuration in suite.configurations):
        logger.info('No performance goals are defined for this suite of benchmarks')

    if any(plugin.has_setup for plugin in suite.plugins):
        logger.info('Running setup functions for plugins:')
        for plugin in suite.plugins:
            if plugin.has_setup:
                logger.info(f' - {plugin.name}')
                plugin.setup(suite, logger)

        logger.info('---')

    if 'scripts_folder' in configuration.values:
        scripts_folder = configuration.scripts_folder
        if scripts_folder:
            if not os.path.exists(scripts_folder):
                logger.error('Invalid scripts_folder: path not found')
                exit(2)
            if not os.path.isdir(scripts_folder):
                logger.error('Invalid scripts folder: ')
                exit(2)

    suite.run(logger)

    logger.info('Suite completed successfully')


@click.command(name='run')
@click.option('--settings',
              default='settings.yaml',
              help='Settings source (YAML or JSON); can be a file path or an URL.',
              show_default=True)
def run_command(settings):
    try:
        run_core(settings)
    except KeyboardInterrupt:
        logger.info('[*] User interrupted')
        exit(1)
