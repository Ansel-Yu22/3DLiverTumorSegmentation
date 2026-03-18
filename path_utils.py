import os
from typing import Optional


def resolve_result_path(raw_path: Optional[str], base_dir: Optional[str] = None) -> Optional[str]:
    if not raw_path:
        return None

    value = str(raw_path)
    root = os.path.abspath(base_dir or os.getcwd())

    # Relative path returned by API.
    if not os.path.isabs(value) and not value.startswith("/"):
        return os.path.abspath(os.path.join(root, value))

    # Container path mapping (/app/...) -> local project path.
    if value.startswith("/app/"):
        relative = value[len("/app/") :].replace("/", os.sep)
        mapped = os.path.abspath(os.path.join(root, relative))
        if os.path.exists(mapped):
            return mapped

    return value
