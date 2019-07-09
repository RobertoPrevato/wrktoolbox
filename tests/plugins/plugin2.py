from logging import Logger
from wrktoolbox.benchmarks import BenchmarkSuite


# in this example, a plugin is used to alter the configuration of each benchmark
def setup(suite: BenchmarkSuite, logger: Logger):

    logger.info('Obtaining an access token for benchmarks')

    # example: obtain an access token for your service
    access_token = 'example!'

    for configuration in suite.configurations:
        if not configuration.headers:
            configuration.headers = {}

        configuration.headers['Authorization'] = f'Bearer {access_token}'



