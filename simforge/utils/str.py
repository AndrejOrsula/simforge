import functools
import re

_REGEX_CANONICALIZE_STR_PATTERN = re.compile(r"[\W_]+")
_REGEX_SNAKE_CASE_PATTERN = (
    re.compile(r"(.)([A-Z][a-z]+)"),
    re.compile(r"__([A-Z])"),
    re.compile(r"([a-z0-9])([A-Z])"),
)


@functools.cache
def canonicalize_str(input: str) -> str:
    return _REGEX_CANONICALIZE_STR_PATTERN.sub("", input).lower()


@functools.cache
def convert_to_snake_case(input: str) -> str:
    input = _REGEX_SNAKE_CASE_PATTERN[0].sub(r"\1_\2", input)
    input = _REGEX_SNAKE_CASE_PATTERN[1].sub(r"_\1", input)
    return _REGEX_SNAKE_CASE_PATTERN[2].sub(r"\1_\2", input).lower()
