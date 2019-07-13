import json
import pickle
import fnmatch
from base64 import b64decode
from abc import abstractmethod
from pathlib import Path
from typing import Generator, Optional, Sequence
from rocore.exceptions import InvalidArgument
from rocore.typesutils.dateutils import parse_datetime
from wrktoolbox.benchmarks import BenchmarkSuite, PerformanceGoalResult
from wrktoolbox.results import ResultsImporter, SuiteReport, BenchmarkOutput


class FileSystemResultsImporter(ResultsImporter):
    """Base class for importers that can read results from file system"""

    def __init__(self,
                 root_folder: str,
                 filter_urls: Optional[Sequence[str]] = None):
        self._root_path = None
        self.root_path = root_folder
        self._ext_glob_pattern = '*' + self.get_file_extension()
        self.filter_urls = list(filter_urls) if filter_urls else None

    @property
    def root_path(self) -> Path:
        return self._root_path

    @root_path.setter
    def root_path(self, value):
        root_path = Path(value)

        if not root_path.exists():
            raise InvalidArgument('given root path does not exist')

        if not root_path.is_dir():
            raise InvalidArgument('given root path is not a directory')

        self._root_path = root_path

    @abstractmethod
    def parse_suite(self, data: str) -> SuiteReport:
        """Parses a suite"""

    @abstractmethod
    def parse_output(self, data: str) -> BenchmarkOutput:
        """Parses a benchmark output"""

    @abstractmethod
    def get_file_extension(self) -> str:
        """Returns the handled files extension"""

    def _load_suite(self, item: Path) -> SuiteReport:
        with open(str(item), mode='rt', encoding='utf8') as file:
            return self.parse_suite(file.read())

    def _load_output(self, item: Path) -> BenchmarkOutput:
        with open(str(item), mode='rt', encoding='utf8') as file:
            return self.parse_output(file.read())

    def _suites_from_dir(self, folder_path: Path) -> Generator[SuiteReport, None, None]:
        for item in folder_path.iterdir():
            if item.is_symlink():
                continue

            if item.is_dir():
                yield from self._suites_from_dir(item)

            if 'suite' in item.name:
                yield self._load_suite(item)
        return

    def _should_import(self, item: BenchmarkOutput) -> bool:
        if self.filter_urls:
            return any(fnmatch.fnmatch(item.url, pattern) for pattern in self.filter_urls)
        return True

    def _results_from_dir(self, folder_path: Path, report: SuiteReport) -> Generator[BenchmarkOutput, None, None]:
        benchmarks_ids = report.suite.benchmarks_ids

        for item in folder_path.iterdir():
            if item.is_symlink():
                continue

            if item.is_file():
                file_name = str(item)
                if fnmatch.fnmatch(file_name, self._ext_glob_pattern) \
                        and any(benchmark_id in file_name for benchmark_id in benchmarks_ids):
                    result = self._load_output(item)
                    if self._should_import(result):
                        yield result
            else:
                yield from self._results_from_dir(item, report)

    def import_suites(self) -> Generator[SuiteReport, None, None]:
        yield from self._suites_from_dir(self.root_path)

    def import_results(self, report: SuiteReport) -> Generator[BenchmarkOutput, None, None]:
        yield from self._results_from_dir(self.root_path, report)


class BinResultsImporter(FileSystemResultsImporter):

    type_name = 'bin'

    def get_file_extension(self) -> str:
        return '.bin'

    def parse_suite(self, data: str) -> SuiteReport:
        suite = pickle.loads(b64decode(data))  # type: BenchmarkSuite
        return SuiteReport(suite)

    def parse_output(self, data: str) -> BenchmarkOutput:
        output = pickle.loads(b64decode(data))  # type: BenchmarkOutput
        return output


class JsonResultsImporter(FileSystemResultsImporter):

    type_name = 'json'

    def get_file_extension(self) -> str:
        return '.json'

    def parse_suite(self, data: str) -> SuiteReport:
        suite = json.loads(data)
        return SuiteReport(BenchmarkSuite.from_dict(suite))

    def parse_output(self, data: str) -> BenchmarkOutput:
        data = json.loads(data)
        output = BenchmarkOutput.parse('\n'.join(data.get('raw_output')),
                                       data.get('id'),
                                       data.get('suite_id'),
                                       parse_datetime(data.get('start_time')),
                                       parse_datetime(data.get('end_time')))
        output.__dict__['goals_results'] = [PerformanceGoalResult(**item) for item in data.get('goals_results')]
        return output
