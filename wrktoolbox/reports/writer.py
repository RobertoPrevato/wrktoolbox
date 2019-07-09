import logging
from abc import abstractmethod
from rocore.registry import Registry
from wrktoolbox.results import SuiteReport, BenchmarkOutput


class ReportWriter(Registry):
    """A class that can write a report for a sequence of results."""

    @abstractmethod
    def write(self, report: SuiteReport):
        """Writes a report."""

    @abstractmethod
    def write_output(self, report: SuiteReport, output: BenchmarkOutput):
        """Writes a report output."""


class LogWriter(ReportWriter):
    """A writer that outputs to a logger."""

    type_name = 'log'

    def __init__(self, logger_name: str = 'wrktoolbox'):
        self.logger = logging.getLogger(logger_name)

    def write(self, report: SuiteReport):
        self.logger.info(str(report.suite))

    def write_output(self, report: SuiteReport, output: BenchmarkOutput):
        self.logger.info(str(output))
