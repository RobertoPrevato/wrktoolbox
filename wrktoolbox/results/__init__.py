from abc import abstractmethod
from typing import Sequence, Generator
from rocore.registry import Registry
from wrktoolbox.benchmarks import BenchmarkSuite, BenchmarkOutput


class SuiteReport:
    """A set of results, consisting of the benchmark suite and its results."""

    def __init__(self,
                 suite: BenchmarkSuite,
                 results: Sequence[BenchmarkOutput] = None):
        self.suite = suite
        self.results = results


class ResultsImporter(Registry):
    """A class that can import benchmark results, stored by an implementation of BenchmarkOutputStore"""

    @abstractmethod
    def import_suites(self) -> Generator[SuiteReport, None, None]:
        """Imports all suites stored in the handled source."""

    @abstractmethod
    def import_results(self, report: SuiteReport) -> Generator[BenchmarkOutput, None, None]:
        """Imports the results of a suite."""

