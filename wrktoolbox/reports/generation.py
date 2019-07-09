from typing import Optional, Sequence, List
from logging import Logger
from rocore.models import Model, Collection, Boolean
from rocore.exceptions import InvalidArgument
from wrktoolbox.benchmarks import BenchmarkPlugin, handle_plugins, BenchmarkOutput
from wrktoolbox.results import ResultsImporter, SuiteReport
from wrktoolbox.reports import ReportWriter
# noinspection PyUnresolvedReferences
from wrktoolbox.results.importers.fs import JsonResultsImporter, BinResultsImporter


class ReportGeneration(Model):
    importers = Collection(ResultsImporter, nullable=False)
    writers = Collection(ReportWriter, nullable=False)
    plugins = Collection((str, BenchmarkPlugin))
    sort = Boolean()

    def __init__(self,
                 importers: Sequence[ResultsImporter],
                 writers: Sequence[ReportWriter],
                 plugins: Optional[Sequence[BenchmarkPlugin]] = None,
                 sort: bool = True):
        if sort is None:
            sort = True
        self.importers = importers
        self.writers = writers
        self.plugins = plugins
        self.sort = sort

    def _get_reports(self, importer):
        if self.sort:
            items = list(importer.import_suites())
            items.sort(key=lambda item: item.suite.location)

            yield from items
        else:
            yield from importer.import_suites()

    def _get_results(self, importer, report):
        if self.sort:
            items = list(importer.import_results(report))  # type: List[BenchmarkOutput]
            items.sort(key=lambda item: item.url)

            yield from items
        else:
            yield from importer.import_results(report)

    def run(self, logger: Logger):
        if not self.importers:
            raise InvalidArgument('no configured importers')

        if not self.writers:
            raise InvalidArgument('no configured writers')

        for importer in self.importers:

            for report in self._get_reports(importer):  # type: SuiteReport
                logger.info('Imported suite %s', report.suite.id)

                for writer in self.writers:
                    writer.write(report)

                for result in self._get_results(importer, report):  # type: BenchmarkOutput
                    for writer in self.writers:
                        writer.write_output(report, result)

        for writer in self.writers:
            if hasattr(writer, 'close'):
                logger.info('Closing writer %s', writer.get_class_name())
                writer.close()

        logger.debug('Finished processing report')

    @classmethod
    def from_dict(cls, data):
        plugins = list(handle_plugins(data))

        return cls(
            [ResultsImporter.from_configuration(item) for item in data.get('importers')],
            [ReportWriter.from_configuration(item) for item in data.get('writers')],
            plugins
        )
