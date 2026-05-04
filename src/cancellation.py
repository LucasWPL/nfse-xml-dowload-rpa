from threading import Event


class JobCancelled(Exception):
    pass


def ensure_not_cancelled(stop_event: Event | None) -> None:
    if stop_event and stop_event.is_set():
        raise JobCancelled("Execução interrompida pelo usuário.")
