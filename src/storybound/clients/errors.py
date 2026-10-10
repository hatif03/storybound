class ClientError(Exception):
    """A model or tool call failed after retries."""

    def __init__(self, message: str, *, retryable: bool = False, status: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status = status


class ParseError(ClientError):
    """The model answered but the answer was not the JSON we asked for."""
