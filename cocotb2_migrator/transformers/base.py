import libcst as cst
from typing import List


class BaseCocotbTransformer(cst.CSTTransformer):
    """
    Base class for all cocotb migration transformers.
    Each transformer should inherit from this class.
    """

    #: Name of the transformer (used for logging and tracking)
    name: str = "BaseCocotbTransformer"

    def __init__(self):
        # Used to track whether this transformer applied any changes
        self.modified = False
        # Collects migration warnings (rendered as top-of-file comments)
        self.warnings: List[str] = []

    def mark_modified(self):
        """Call this method inside a transformation to mark the code as modified."""
        self.modified = True

    def has_modified(self) -> bool:
        """Returns True if this transformer made any modifications."""
        return self.modified

    def add_warning(self, message: str) -> None:
        """Record a migration warning (deduplicated)."""
        if message not in self.warnings:
            self.warnings.append(message)

    def prepend_warnings(self, module: cst.Module) -> cst.Module:
        """
        Insert the collected warnings as top-of-file comments.
        Returns the module unchanged if there are no warnings.
        """
        if not self.warnings:
            return module
        header = list(module.header)
        header.extend(
            cst.EmptyLine(comment=cst.Comment(f"# WARNING: {msg}")) for msg in self.warnings
        )
        return module.with_changes(header=header)
