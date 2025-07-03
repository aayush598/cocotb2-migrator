import libcst as cst


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

    def mark_modified(self):
        """Call this method inside a transformation to mark the code as modified."""
        self.modified = True

    def has_modified(self) -> bool:
        """Returns True if this transformer made any modifications."""
        return self.modified
