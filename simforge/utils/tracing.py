from functools import cache
from importlib.util import find_spec
from os import environ


@cache
def with_rich() -> bool:
    if find_spec("rich") is None or (
        environ.get("RICH_TRACEBACK") or environ.get("SF_RICH_TRACEBACK", "true")
    ).lower() not in ("true", "1"):
        return False

    from rich import traceback

    # isort: split

    import pydantic

    traceback.install(
        width=120,
        show_locals=(
            environ.get("RICH_TRACEBACK_LOCALS")
            or environ.get("SF_RICH_TRACEBACK_LOCALS", "false")
        ).lower()
        in ("true", "1"),
        suppress=(pydantic,),
    )

    return True


@cache
def with_logfire() -> bool:
    if find_spec("logfire") is None or (
        environ.get("LOGFIRE_ENABLE") or environ.get("SF_LOGFIRE_ENABLE", "true")
    ).lower() not in ("true", "1"):
        return False

    import logfire

    logfire.configure(
        send_to_logfire=environ.get("LOGFIRE_SEND_TO_LOGFIRE", "false").lower()
        in ("true", "1"),
        service_name="simforge",
        console=False,
    )
    logfire.instrument_pydantic()

    return True
