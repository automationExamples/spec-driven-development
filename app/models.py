from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True)
class Application:
    id: int
    name: str
    summary: str
    position: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Application":
        return cls(
            id=int(row["id"]),
            name=str(row["name"]),
            summary=str(row["summary"]),
            position=int(row["position"]),
        )
