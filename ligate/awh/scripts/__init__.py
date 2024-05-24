from pathlib import Path

"""
This directory contains the original hard-coded CADD workflow scripts.
"""

SCRIPTS_DIR = Path(__file__).parent.absolute()

CREATE_HYBRID_LIGANDS_SCRIPT = SCRIPTS_DIR / "create-hybrid-ligands.sh"
