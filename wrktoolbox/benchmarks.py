import os
import yaml
import time
import importlib
import subprocess
import multiprocessing
from collections.abc import Mapping
from uuid import uuid4
from enum import Enum
from logging import Logger
from functools import wraps
from abc import abstractmethod
from typing import Optional, Dict, Sequence, Any
from rocore.exceptions import InvalidArgument, EmptyArgumentException
from rocore.registry import Registry
from rocore.models import Model, String, UInt, Enum as EnumType, Boolean, OfType, Collection, Guid, DateTime
from .wrkoutput import BenchmarkOutput, Result, ParseFailure
from datetime import datetime


class BenchmarkException(Exception):
    """Base class for exceptions happening during benchmarks."""


class ProcessBenchmarkException(BenchmarkException):

    def __init__(self, output: str, exit_code: int):
        super().__init__(f'Process exit code does not indicate success; '
                         f'exit code: {exit_code};'
                         f' output: {output}')


class MissingDependencyException(BenchmarkException):

    def __init__(self):
        super().__init__('Process exit code (127) indicated failure due to missing `wrk` or `wrk2` command; '
                         'please install the necessary dependencies and make sure they are accessible from scripts.')


class BenchmarkPluginException(BenchmarkException):

    def __init__(self, details: str):
        super().__init__(f'Invalid `plugins` configuration; {details}')


class WrkVariant(Enum):
    WRK = 'wrk'
    WRK2 = 'wrk2'


class PerformanceGoalResult(Result):

    def __init__(self,
                 success: bool,
                 goal: str,
                 error: Optional[str] = None):
        self.success = success
        self.goal = goal
        self.error = error

    def to_dict(self):
        data = super().to_dict()
        if not self.error:
            del data['error']
        return data


class PerformanceGoal(Registry):

    @abstractmethod
    def is_satisfied(self, output: BenchmarkOutput) -> bool:
        """Returns a value indicating whether a goal is satisfied."""

    def assert_parsed(self, value: Any):
        assert value is not None
        assert not isinstance(value, ParseFailure)

    @classmethod
    def from_dict(cls, data):
        if 'repr' in data:
            del data['repr']
        return super().from_dict(data)

    def to_dict(self):
        data = self.__dict__.copy()
        data['repr'] = repr(self)
        data['type'] = self.get_class_name()
        return data


class GoalException(BenchmarkException):
    """Base class for performance goal exceptions."""


class BenchmarkConfig(Model):

    test_id = String()
    url = String(nullable=False)
    threads = UInt(nullable=False)
    concurrency = UInt(nullable=False)
    duration = UInt(nullable=False)
    timeout = UInt(nullable=False)
    script = String()
    app_variant = EnumType(WrkVariant)
    responses_per_second = UInt()
    headers = OfType(dict)
    latency_statistics = Boolean()
    repeat = UInt()
    goals = Collection(PerformanceGoal)

    def __init__(self,
                 url: str,
                 threads: int = -1,
                 concurrency: int = 10,
                 duration: int = 20,
                 timeout: int = 20,
                 script: str = None,
                 app_variant: WrkVariant = WrkVariant.WRK,
                 responses_per_second: Optional[int] = None,
                 headers: Optional[Dict[str, str]] = None,
                 latency_statistics: Optional[bool] = True,
                 test_id: str = None,
                 repeat: int = 1,
                 goals: Optional[Sequence[PerformanceGoal]] = None):
        if threads < 1 or threads is None:
            threads = multiprocessing.cpu_count()

        if app_variant == WrkVariant.WRK2 and responses_per_second is None:
            responses_per_second = 10

        if responses_per_second is not None and responses_per_second > 0:
            app_variant = WrkVariant.WRK2

        self.test_id = test_id
        self.url = url
        self.threads = threads
        self.concurrency = concurrency
        self.duration = duration
        self.timeout = timeout
        self.script = script
        self.app_variant = WrkVariant(app_variant or 'wrk')
        self.responses_per_second = responses_per_second
        self.latency_statistics = bool(latency_statistics)
        self.headers = headers
        self.repeat = repeat
        self.goals = goals

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.url}>'

    def _get_responses_per_second(self):
        return f' -R{self.responses_per_second}' \
            if self.responses_per_second and self.app_variant == WrkVariant.WRK2 else ''

    def _get_headers(self):
        if not self.headers:
            return ''
        parts = []
        for key, value in self.headers.items():
            parts.append(f'-H "{key}: {value}"')
        return ' ' + ' '.join(parts)

    def __eq__(self, other):
        if isinstance(other, BenchmarkConfig):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def to_dict(self):
        return {
            'test_id': self.test_id,
            'url': self.url,
            'threads': self.threads,
            'concurrency': self.concurrency,
            'duration': self.duration,
            'timeout': self.timeout,
            'script': self.script,
            'app_variant': self.app_variant.value,
            'responses_per_second': self.responses_per_second,
            'latency_statistics': self.latency_statistics,
            'headers': self.headers
        }

    def get_cmd(self):
        return f'{self.app_variant.value} {self.url} ' \
               f'-c {self.concurrency} ' \
               f'-t {self.threads} ' \
               f'-d {self.duration} ' \
               f'--timeout {self.timeout}' \
               + (' --latency' if self.latency_statistics else '') \
               + (f' -s {self.script}' if self.script else '') \
               + self._get_responses_per_second() \
               + self._get_headers()


class Benchmark(Model):

    id = Guid()
    config = OfType(BenchmarkConfig)

    def __init__(self, config: BenchmarkConfig):
        self.id = uuid4()
        self.config = config

    def run(self, logger=None, suite_id=None) -> BenchmarkOutput:
        config = self.config
        start_time = datetime.utcnow()

        p = subprocess.Popen(config.get_cmd(), shell=True, stdout=subprocess.PIPE)
        p.wait(config.duration + 12)

        end_time = datetime.utcnow()

        output = p.stdout.read().decode()

        if logger and output:
            logger.debug(f'[*] Process output: \n\n{output}\n\n')

        if p.returncode != 0:
            # something went wrong when running the benchmark
            if p.returncode == 127:
                raise MissingDependencyException()

            raise ProcessBenchmarkException(output, p.returncode)

        return BenchmarkOutput.parse(output,
                                     suite_id=suite_id,
                                     start_time=start_time,
                                     end_time=end_time)


class BenchmarkOutputStore(Registry):

    @abstractmethod
    def store(self, config: BenchmarkConfig, output: BenchmarkOutput):
        """Stores the results of a benchmark."""

    @abstractmethod
    def store_suite(self, suite: 'BenchmarkSuite'):
        """Stores information about a suite."""


def exception_handle(catch_exc, exc_type):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except catch_exc as e:
                raise exc_type(str(e))
        return wrapper
    return decorator


class BenchmarkPlugin:

    def __init__(self, module):
        if isinstance(module, Mapping):
            module = module.get('module')
        if isinstance(module, str):
            module = importlib.import_module(module)
        self.module = module

    @property
    def setup(self):
        return getattr(self.module, 'setup')

    @property
    def has_setup(self) -> bool:
        return hasattr(self.module, 'setup')

    @property
    def name(self):
        return self.module.__name__

    def to_dict(self):
        return {'module': self.name,
                'has_setup': self.has_setup}

    def __repr__(self):
        return f'<Plugin {self.name}>'


@exception_handle(ModuleNotFoundError, BenchmarkPluginException)
def handle_plugins(data):
    plugins = data.get('plugins')
    if not plugins:
        return

    for plugin in plugins:
        yield BenchmarkPlugin(plugin)


def _get_goals(array):
    if not array:
        return []
    return [PerformanceGoal.from_configuration(item) for item in array]


class HostData:

    def __init__(self,
                 cpu_count: Optional[int] = None,
                 env: Optional[Mapping] = None):
        if cpu_count is None:
            cpu_count = multiprocessing.cpu_count()
        if env is None:
            env = os.environ.copy()
        self.cpu_count = cpu_count
        self.env = env

    def to_dict(self):
        return self.__dict__.copy()


class BenchmarkSuite(Model):
    id = String(nullable=False)
    public_ip = String()
    location = String()
    scripts_folder = String()
    configurations = Collection(BenchmarkConfig)
    stores = Collection(BenchmarkOutputStore)
    plugins = Collection((str, BenchmarkPlugin))
    goals = Collection(PerformanceGoal)
    benchmarks_ids = Collection(str)
    start_time = DateTime()
    end_time = DateTime()
    think_time = UInt(nullable=False)

    root_settings = {'threads',
                     'concurrency',
                     'duration',
                     'timeout',
                     'responses_per_second',
                     'headers',
                     'latency_statistics',
                     'repeat'}

    def __init__(self,
                 configurations: Sequence[BenchmarkConfig],
                 stores: Sequence[BenchmarkOutputStore],
                 scripts_folder: str,
                 plugins: Optional[Sequence[BenchmarkPlugin]] = None,
                 goals: Optional[Sequence[PerformanceGoal]] = None,
                 think_time: int = 0,
                 _id: Optional[str] = None,
                 benchmarks_ids: Optional[Sequence[str]] = None,
                 public_ip: Optional[str] = None,
                 metadata: Optional[Any] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 host_data: Optional[HostData] = None):
        if host_data is None:
            host_data = HostData()
        if benchmarks_ids is None:
            benchmarks_ids = []
        if think_time is None:
            think_time = 0
        self.id = _id or uuid4()
        self.stores = stores
        self.scripts_folder = scripts_folder
        self.configurations = configurations
        self.plugins = plugins
        self.goals = goals
        self.think_time = think_time
        self.host = host_data
        self.metadata = metadata
        self.public_ip = public_ip
        self.location = self._get_location_from_env(host_data)
        self.start_time = start_time
        self.end_time = end_time
        self.benchmarks_ids = benchmarks_ids
        self._check_configurations_ids(configurations)

        if scripts_folder:
            for configuration in configurations:
                if configuration.script:
                    configuration.script = os.path.join(scripts_folder, configuration.script)

    def load_plugins(self):
        if not self.plugins:
            return
        if any(isinstance(plugin, str) for plugin in self.plugins):
            self.plugins = [BenchmarkPlugin(name) for name in self.plugins]

    def estimated_time(self) -> int:
        """Returns an estimated time required for completion, in seconds.
        This estimate does not count time spent by implementations of output store."""
        i = 0
        for configuration in self.configurations:
            i += configuration.duration * configuration.repeat

            if configuration.app_variant == WrkVariant.WRK2:
                # thread calibration may take about 10 seconds
                i += 10

            i += self.think_time
        # one second margin added, since code execution time is not counted
        return i + 1 - self.think_time

    @staticmethod
    def _check_configurations_ids(configurations: Sequence[BenchmarkConfig]):
        found_ids = set()

        for i, configuration in enumerate(configurations):
            if configuration.test_id in found_ids:
                raise InvalidArgument(f'Duplicated test id: {configuration.test_id}; '
                                      f'change test_id configuration for your benchmarks.')
            if not configuration.test_id:
                configuration.test_id = f'test_{i}'

            found_ids.add(configuration.test_id)

    def __repr__(self):
        return f'<{self.__class__.__name__} {len(self)}>'

    def __str__(self):
        return (f'Suite {self.id}; '
                f'Configurations {", ".join(configuration.test_id for configuration in self.configurations)};')

    def __len__(self):
        return len(self.configurations)

    def run(self, logger: Logger):
        logger.info('Estimated time %s s', self.estimated_time())
        self.start_time = datetime.utcnow()
        configurations_count = len(self.configurations)

        for configuration in self.configurations:
            if not configuration.repeat:
                continue

            for i in range(configuration.repeat):
                benchmark = Benchmark(configuration)
                benchmark.suite_id = self.id

                logger.info(f'Running benchmark...\n{configuration.get_cmd()}')

                output = benchmark.run(logger, self.id)

                self.benchmarks_ids.append(output.id)

                self.check_goals(configuration, output, logger)

                logger.debug(f'Storing output for benchmark {benchmark.id}...')
                self.store_output(configuration, output)

                logger.info('---')

                if self.think_time and i + 1 < configurations_count:
                    logger.debug(f'Waiting for {self.think_time} seconds')
                    time.sleep(self.think_time)

        logger.debug(f'Storing suite data')
        self.end_time = datetime.utcnow()
        self.store_self()

    def check_goals(self, configuration: BenchmarkConfig, output: BenchmarkOutput, logger: Logger):
        if not self.goals and not configuration.goals:
            logger.debug(f'No performance goals are defined for {configuration.test_id}')
        if self.goals:
            self._check_goals(output, self.goals, logger)
        if configuration.goals:
            self._check_goals(output, configuration.goals, logger)

    @staticmethod
    def _check_goals(output: BenchmarkOutput,
                     goals: Sequence[PerformanceGoal],
                     logger: Logger):
        for goal in goals:
            try:
                is_satisfied = goal.is_satisfied(output)
            except (AssertionError, GoalException) as error:
                logger.exception('Error while checking performance goal', exc_info=error)
                result = PerformanceGoalResult(False, repr(goal), str(error))
            else:
                logger.debug(f'--> goal {goal.get_class_name()} satisfied: {is_satisfied}')
                result = PerformanceGoalResult(is_satisfied, repr(goal), None)

            output.goals_results.append(result)

    def store_self(self):
        for store in self.stores:
            store.store_suite(self)

    def store_output(self,
                     configuration: BenchmarkConfig,
                     output: BenchmarkOutput):
        for store in self.stores:
            store.store(configuration, output)

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, mode='rt', encoding='utf8') as settings_file:
            data = yaml.safe_load(settings_file)
        return cls.from_dict(data)

    @staticmethod
    def _get_location_from_env(host: HostData):
        return host.env.get('WRKTOOLBOX_LOCATION', host.env.get('LOCATION', ''))

    def to_dict(self):
        return {
            'id': self.id,
            'scripts_folder': self.scripts_folder,
            'configurations': self.configurations,
            'stores': self.stores,
            'plugins': self.plugins,
            'goals': self.goals,
            'think_time': self.think_time,
            'metadata': self.metadata,
            'host': self.host,
            'public_ip': self.public_ip,
            'benchmarks_ids': self.benchmarks_ids,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location
        }

    @staticmethod
    def use_base_url(data):
        if not data or 'configurations' not in data:
            raise EmptyArgumentException('mapping')

        base_url = data.get('base_url')
        base_url_key = data.get('base_url_key', '$BASEURL')

        if not base_url:
            return

        configurations = data.get('configurations')
        for configuration in configurations:
            url = configuration.get('url')  # type: str

            if not url:
                configuration['url'] = base_url
                continue

            if base_url_key in url:
                configuration['url'] = url.replace(base_url_key, base_url)
                continue

            if not url.startswith('http'):
                configuration['url'] = base_url + url

        metadata = data.get('metadata')
        if not metadata:
            return

        for key, value in metadata.items():
            if base_url_key in value:
                metadata[key] = value.replace(base_url_key, base_url)

    @staticmethod
    def use_root_settings(data):
        if not data or 'configurations' not in data:
            raise EmptyArgumentException('mapping')

        configurations = data.get('configurations')

        for root_name in BenchmarkSuite.root_settings:
            root_value = data.get(root_name)

            if not root_value:
                continue

            for configuration in configurations:
                if root_name not in configuration or configuration.get(root_name) is None:
                    configuration[root_name] = root_value

    @staticmethod
    def normalize_configuration(data):
        configurations_key = 'configurations'
        benchmarks_key = 'benchmarks'
        stores_key = 'stores'

        # support calling configurations 'benchmarks' for user friendliness in configuration files
        if configurations_key not in data:
            if benchmarks_key in data:
                data[configurations_key] = data[benchmarks_key]
                del data[benchmarks_key]
            else:
                raise InvalidArgument(f'Missing benchmarks configuration: either specify '
                                      f'it with `{configurations_key}` or `{benchmarks_key}`')

        for name in {configurations_key, stores_key}:
            if name not in data:
                raise InvalidArgument(f'Missing `{name}` in configuration')

        BenchmarkSuite.use_base_url(data)
        BenchmarkSuite.use_root_settings(data)

    @classmethod
    def from_dict(cls, data):
        cls.normalize_configuration(data)

        # NB: plugins must be first imported, as they might register new types
        plugins = list(handle_plugins(data))

        for benchmark in data.get('configurations'):
            if 'goals' in benchmark:
                benchmark['goals'] = _get_goals(benchmark.get('goals'))

        host_data = HostData(**data.get('host')) if 'host' in data else None

        return cls([BenchmarkConfig(**item) for item in data.get('configurations')],
                   [BenchmarkOutputStore.from_configuration(item) for item in data.get('stores')],
                   data.get('scripts_folder'),
                   plugins,
                   _get_goals(data.get('goals')),
                   data.get('think_time'),
                   _id=data.get('id'),
                   benchmarks_ids=data.get('benchmarks_ids'),
                   public_ip=data.get('public_ip'),
                   metadata=data.get('metadata'),
                   start_time=data.get('start_time'),
                   end_time=data.get('end_time'),
                   host_data=host_data)
