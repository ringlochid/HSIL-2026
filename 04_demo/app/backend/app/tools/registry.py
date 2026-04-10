from __future__ import annotations

from app.tools.clinvar import ClinvarTool
from app.tools.ensembl_vep import EnsemblVepTool
from app.tools.franklin import FranklinTool
from app.tools.spliceai import SpliceAiTool


def build_tool_registry(settings):
    return {
        "clinvar": ClinvarTool(settings),
        "vep": EnsemblVepTool(settings),
        "franklin": FranklinTool(settings),
        "spliceai": SpliceAiTool(settings),
    }
