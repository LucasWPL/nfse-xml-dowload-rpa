from collections.abc import Callable


class AppLogger:
    def __init__(self, debug_mode: bool = False, sink: Callable[[str], None] | None = None) -> None:
        self.debug_mode = debug_mode
        self.sink = sink or print

    def info(self, message: str) -> None:
        self.sink(message)

    def debug(self, message: str) -> None:
        if self.debug_mode:
            self.sink(message)
