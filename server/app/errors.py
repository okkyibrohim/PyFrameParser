from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar

T = TypeVar("T", bound=Enum)


# TODO: replace with enummeta implementation
def index_enum(field_name: str):
    """
    Hack to initialize an index on enum members based on a specified field.
    This decorator act as static initialization for enum values with 'field_name' as key.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        index: Dict[Any, T] = {}
        for member in cls:
            if key := getattr(member, field_name, None):
                index[key] = member

        cls._index = MappingProxyType(index)  # ty:ignore[unresolved-attribute]

        return cls

    return decorator


@index_enum(field_name="status_code")
class HTTPError(Enum):
    _ignore_: ClassVar[List[str]] = ["_index", "status_code", "code", "message"]

    UNAUTHORIZED = (401, "UNAUTHORIZED", "Unauthorized.")
    TOO_MANY_REQUESTS = (429, "TOO_MANY_REQUESTS", "Too Many Requests.")
    BAD_REQUEST = (400, "BAD_REQUEST", "Bad Request.")
    INTERNAL_SERVER_ERROR = (500, "INTERNAL_SERVER_ERROR", "Internal Server Error.")

    _index: ClassVar[Dict[Any, HTTPError]]

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return self.message

    @classmethod
    def get_from_index(cls, key: Any) -> Optional[HTTPError]:
        return cls._index.get(key)

    @classmethod
    def from_status_code(cls, status_code: int) -> HTTPError:
        if err := cls.get_from_index(status_code):
            return err

        return cls.BAD_REQUEST


class APIError(Exception):
    def __init__(self, status_code: int = 400, message: str = ""):
        err = HTTPError.from_status_code(status_code)

        super().__init__(err.message)

        self.message = message or err.message
        self.code = err.code
        self.status_code = err.status_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "message": self.message,
            }
        }
