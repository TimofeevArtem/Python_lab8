import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TextIO

from src.contracts.task import Task
from src.sources.repository import register_source


def extract_tasks(lines: list[str], line_no: int) -> tuple[str, str]:
    """
    Извлекает id и payload из строки ввода.
    Формат: id:payload[:priority[:status]]
    """
    try:
        return lines[0], lines[1]
    except IndexError:
        raise ValueError(
            f"Line: {line_no}. Task must contain at least 2 items (id:payload), separated by ':'"
        )


@dataclass(frozen=True)
class StdinLineSource:
    stream: TextIO = sys.stdin
    name: str = "stdin"

    def fetch(self) -> Iterable[Task]:
        for line_no, line in enumerate(self.stream, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            
            id, payload = extract_tasks(parts, line_no)
            priority = 3
            status = "создана"
            
            if len(parts) >= 3:
                try:
                    priority = int(parts[2])
                except ValueError:
                    pass
            
            if len(parts) >= 4:
                status = parts[3]
            
            yield Task(
                id=id,
                payload=payload,
                priority=priority,
                status=status
            )


@register_source("stdin")
def create_source() -> StdinLineSource:
    return StdinLineSource()