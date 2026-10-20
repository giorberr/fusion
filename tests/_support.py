"""Small Fusion stand-ins for local unit tests, not live API verification."""

from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


class Collection:
    def __init__(self, items=()):
        self.items = tuple(items)

    @property
    def count(self):
        return len(self.items)

    def item(self, index):
        return self.items[index]


class Design(SimpleNamespace):
    @staticmethod
    def cast(product):
        return product if isinstance(product, Design) else None


def load_script(filename, *, app=None, point_type=None):
    """Execute the complete source without importing Fusion or caching script bytecode."""
    adsk = ModuleType("adsk")
    adsk.__path__ = []
    adsk.core = ModuleType("adsk.core")
    adsk.fusion = ModuleType("adsk.fusion")
    adsk.core.Application = SimpleNamespace(get=lambda: app)
    adsk.core.Point3D = point_type
    adsk.fusion.Design = Design
    adsk.fusion.DesignTypes = SimpleNamespace(
        ParametricDesignType=1, DirectDesignType=0
    )
    path = Path(__file__).resolve().parents[1] / "scripts" / filename
    script = ModuleType(path.stem)
    script.__file__ = str(path)
    with patch.dict(
        sys.modules,
        {
            "adsk": adsk,
            "adsk.core": adsk.core,
            "adsk.fusion": adsk.fusion,
        },
    ):
        exec(
            compile(path.read_text(encoding="utf-8"), str(path), "exec"),
            script.__dict__,
        )
    return script
