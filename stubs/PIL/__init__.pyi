from typing import IO, Optional

class Image:
    def save(self, fp: IO[bytes], format: Optional[str] = None, **params) -> None: ...
