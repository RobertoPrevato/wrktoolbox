import os
import uuid
import pickle
from abc import abstractmethod
from base64 import b64encode
from datetime import datetime
from rocore.json import dumps
from rocore.folders import ensure_folder
from wrktoolbox.benchmarks import BenchmarkOutputStore, BenchmarkOutput, BenchmarkConfig, BenchmarkSuite


class FileSystemBenchmarkOutputStore(BenchmarkOutputStore):
    """Base class for file system stores."""

    def __init__(self, output_folder: str = 'out'):
        if output_folder == '$newid':
            output_folder = str(uuid.uuid4())

        ensure_folder(output_folder)
        self.output_folder = output_folder

    def get_file_name(self, prefix: str, suffix: str = '') -> str:
        ts = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        return os.path.join(self.output_folder, f'{prefix}-{ts}-{suffix}') + self.get_file_extension()

    @abstractmethod
    def get_file_extension(self) -> str:
        """Returns the output files extension"""

    @abstractmethod
    def write_output(self, config: BenchmarkConfig, output: BenchmarkOutput) -> str:
        """Writes output to a str"""

    @abstractmethod
    def write_suite(self, suite: BenchmarkSuite):
        """Writes a suite to a string representation"""

    def store(self, config: BenchmarkConfig, output: BenchmarkOutput):
        with open(self.get_file_name(config.test_id, output.id), mode='wt', encoding='utf8') as output_file:
            output_file.write(self.write_output(config, output))

    def store_suite(self, suite: BenchmarkSuite):
        with open(self.get_file_name('suite', suite.id), mode='wt', encoding='utf8') as output_file:
            output_file.write(self.write_suite(suite))

    def to_dict(self):
        return {
            'type': self.get_class_name(),
            'output_folder': self.output_folder
        }


class BinFileSystemBenchmarkOutputStore(FileSystemBenchmarkOutputStore):
    """A file system store that saves data in binary (pickled) format."""
    type_name = 'bin'

    def get_file_extension(self) -> str:
        return '.bin'

    def write_output(self, config: BenchmarkConfig, output: BenchmarkOutput) -> str:
        return b64encode(pickle.dumps(output)).decode('utf8')

    def write_suite(self, suite: BenchmarkSuite):
        suite.plugins = [plugin.name for plugin in suite.plugins]
        return b64encode(pickle.dumps(suite)).decode('utf8')


class JsonFileSystemBenchmarkOutputStore(FileSystemBenchmarkOutputStore):
    """A file system store that saves data in JSON format."""
    type_name = 'json'

    def get_file_extension(self) -> str:
        return '.json'

    def write_output(self, config: BenchmarkConfig, output: BenchmarkOutput) -> str:
        return dumps(output, indent=4)

    def write_suite(self, suite: BenchmarkSuite):
        return dumps(suite, indent=4)
