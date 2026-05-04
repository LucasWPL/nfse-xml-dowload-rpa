class AppLogger:
    def __init__(self, debug_mode: bool = False) -> None:
        self.debug_mode = debug_mode

    def info(self, message: str) -> None:
        print(message)

    def debug(self, message: str) -> None:
        if self.debug_mode:
            print(message)
