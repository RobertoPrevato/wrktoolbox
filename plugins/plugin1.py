# in this example, a plugin is used to register a new type of store
from wrktoolbox.wrkoutput import BenchmarkOutput
from wrktoolbox.benchmarks import BenchmarkOutputStore, BenchmarkConfig


class FooOutputStore(BenchmarkOutputStore):

    type_name = 'foo'

    def store(self, config: BenchmarkConfig, output: BenchmarkOutput):
        """implement here your method to store data"""

    def store_suite(self, suite: 'BenchmarkSuite'):
        pass
