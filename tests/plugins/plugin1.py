# in this example, a plugin is used to register a new type of store
from wrktoolbox.wrkoutput import BenchmarkOutput
from wrktoolbox.benchmarks import BenchmarkSuite, BenchmarkOutputStore, BenchmarkConfig


class FooOutputStore(BenchmarkOutputStore):

    type_name = 'foo'

    def store(self, config: BenchmarkConfig, output: BenchmarkOutput):
        print('fake store')

    def store_suite(self, suite: BenchmarkSuite):
        pass

