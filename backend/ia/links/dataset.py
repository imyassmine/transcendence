import json 
from pathlib import Path
from .domains import parent_domains

class DeletionDataset():
    def __init__(self, entries: list[dict]) -> None:
        self.by_domain: dict[str, dict] = {}
        self.by_name: dict[str, dict] = {}
        for entry in entries:
            if not entry.get("url"):
                continue
            for d in entry.get("domains", []):
                self.by_domain.setdefault(d.lower().removeprefix("www."), entry)
            self.by_name.setdefault(entry["name"].strip().lower(), entry)

    @classmethod
    def from_file(cls, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data)

    def lookup(self, domain: str, name: str | None = None, lang: str = "fr") -> dict | None:
        entry = None
        for d in parent_domains(domain):
            entry = self.by_domain.get(d)
            if entry:
                break
        if entry is None and name:
            entry = self.by_name.get(name.strip().lower())
        if entry is None:
            return None
        return {
            "service": entry["name"],
            "url": entry["url"],
            "difficulty": entry.get("difficulty"),
            "instructions": entry.get(f"notes_{lang}") or entry.get("notes"),
            "email": entry.get("email"),
        }