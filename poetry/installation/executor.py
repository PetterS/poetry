from poetry.puzzle.operations import Install
from poetry.puzzle.operations import Uninstall
from poetry.puzzle.operations import Update
from poetry.puzzle.operations.operation import Operation


class Executor:
    def __init__(self, installer, io, execute_operations, dry_run, verbose):
        self._installer = installer
        self._io = io
        self._execute_operations = execute_operations
        self._dry_run = dry_run
        self._verbose = verbose

    def execute(self, ops):
        for op in ops:
            self._execute_single(op)

    def _execute_single(self, operation):  # type: (Operation) -> None
        """
        Execute a given operation.
        """
        method = operation.job_type

        getattr(self, "_execute_{}".format(method))(operation)

    def _execute_update(self, operation):  # type: (Update) -> None
        source = operation.initial_package
        target = operation.target_package

        if operation.skipped:
            if self._verbose and (self._execute_operations or self._dry_run):
                self._io.write_line(
                    "  - Skipping <c1>{}</c1> (<c2>{}</c2>) {}".format(
                        target.pretty_name,
                        target.full_pretty_version,
                        operation.skip_reason,
                    )
                )

            return

        if self._execute_operations or self._dry_run:
            self._io.write_line(
                "  - Updating <c1>{}</c1> (<c2>{}</c2> -> <c2>{}</c2>)".format(
                    target.pretty_name,
                    source.full_pretty_version,
                    target.full_pretty_version,
                )
            )

        if not self._execute_operations:
            return

        self._installer.update(source, target)

    def _execute_install(self, operation):  # type: (Install) -> None
        if operation.skipped:
            if self._verbose and (self._execute_operations or self.is_dry_run()):
                self._io.write_line(
                    "  - Skipping <c1>{}</c1> (<c2>{}</c2>) {}".format(
                        operation.package.pretty_name,
                        operation.package.full_pretty_version,
                        operation.skip_reason,
                    )
                )

            return

        if self._execute_operations or self.is_dry_run():
            self._io.write_line(
                "  - Installing <c1>{}</c1> (<c2>{}</c2>)".format(
                    operation.package.pretty_name, operation.package.full_pretty_version
                )
            )

        if not self._execute_operations:
            return

        self._installer.install(operation.package)

    def _execute_uninstall(self, operation):  # type: (Uninstall) -> None
        if operation.skipped:
            if self._verbose and (self._execute_operations or self._dry_run):
                self._io.write_line(
                    "  - Not removing <c1>{}</c1> (<c2>{}</c2>) {}".format(
                        operation.package.pretty_name,
                        operation.package.full_pretty_version,
                        operation.skip_reason,
                    )
                )

            return

        if self._execute_operations or self._dry_run:
            self._io.write_line(
                "  - Removing <c1>{}</c1> (<c2>{}</c2>)".format(
                    operation.package.pretty_name, operation.package.full_pretty_version
                )
            )

        if not self._execute_operations:
            return

        self._installer.remove(operation.package)
