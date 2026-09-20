"""
Single-file staging/temp -> atomic replace, shared by build.py (writes
one dist/gvp.json) and package.py (writes each file inside a staging
package directory before that directory is itself published).
"""
import os
import tempfile
from pathlib import Path


def write_bytes_atomically(output_path: Path, data: bytes) -> None:
    """
    Writes `data` to a temp file in the same directory as `output_path`
    (so the following os.replace() is an atomic rename on the same
    filesystem/volume), then atomically replaces `output_path` with it.
    On any failure, no temp file is left behind and any previously
    existing `output_path` is untouched.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".gvp-build-", suffix=".tmp", dir=str(output_path.parent)
    )
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp_path, output_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
