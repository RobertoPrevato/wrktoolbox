import sys
import click
from wrktoolbox.logs import get_app_logger
from roconfiguration import ConfigurationError
from wrktoolbox.commands import get_configuration, SettingsFileNotFound
from rocore.exceptions import InvalidArgument
# noinspection PyUnresolvedReferences
from wrktoolbox.goals import *
# noinspection PyUnresolvedReferences
from wrktoolbox.stores import *
from wrktoolbox.reports.generation import ReportGeneration


logger = get_app_logger()


def reports_core(settings):
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

    # NB: first use an importer to import

    try:
        generation = ReportGeneration.from_dict(configuration.values)
    except Exception:
        logger.exception('An error occurred while preparing the suite of benchmarks')
        exit(1)
        return

    if generation.plugins:
        logger.info('Loaded plugins:')
        for plugin in generation.plugins:
            logger.info(f' - {plugin.name}')

        logger.info('---')

    generation.run(logger)


@click.command(name='reports')
@click.option('--settings',
              default='reports.yaml',
              help='Settings source (YAML or JSON); can be a file path or an URL.',
              show_default=True)
def reports_command(settings):
    try:
        reports_core(settings)
    except KeyboardInterrupt:
        logger.info('[*] User interrupted')
        exit(1)

