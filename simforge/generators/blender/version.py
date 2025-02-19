from importlib.util import find_spec
from typing import Tuple

from simforge.utils import is_semver_compatible, logging

BPY_SEMVER_MIN: Tuple[int, int, int] = (4, 3, 0)


def verify_bpy_version() -> bool:
    if not find_spec("bpy"):
        logging.critical("Unable to find 'bpy' module")
        return False

    import bpy

    if not is_semver_compatible(
        required=BPY_SEMVER_MIN,
        current=bpy.app.version,
    ):
        logging.critical(
            f"Current version of Blender 'bpy={bpy.app.version_string}' is not semantically compatible with requirement 'bpy^{'.'.join(map(str, BPY_SEMVER_MIN))}' (assets might need to be generated inside a subprocess)"
        )
        return False

    return True
