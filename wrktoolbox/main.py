import click
import logging
from wrktoolbox import version
from wrktoolbox.commands.run import run_command
from wrktoolbox.commands.reports import reports_command
from wrktoolbox.logs import get_app_logger
from .web import disable_ssl_verification


@click.group()
@click.option('--verbose',
              default=False,
              help='Whether to display debug output.',
              is_flag=True)
@click.option('--no-ssl-verify',
              default=False,
              help='Allows to skip ssl verification.',
              is_flag=True)
@click.version_option(version=version)
def main(verbose, no_ssl_verify):
    """
    wrktoolbox is a tool to run HTTP benchmarks with wrk and wrk2 tools, store their output, and generate
    reports.

    For examples and more information, refer to the project in GitHub:
    https://github.com/RobertoPrevato/wrktoolbox
    """
    logger = get_app_logger()
    if verbose:
        logger.setLevel(logging.DEBUG)

    logger.debug('Running in --verbose mode')

    if no_ssl_verify:
        logger.debug('Disabling SSL verification')
        disable_ssl_verification()


main.add_command(run_command)
main.add_command(reports_command)
