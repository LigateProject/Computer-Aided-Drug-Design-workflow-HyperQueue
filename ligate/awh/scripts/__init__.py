from pathlib import Path

"""
This directory contains the original hard-coded CADD workflow scripts and MDP files.
"""

SCRIPTS_DIR = Path(__file__).parent.absolute()
MDP_DIR = SCRIPTS_DIR / "mdp"

EM_L0_MDP = MDP_DIR / "em_l0.mdp"
EQ_NVT_L0_MDP = MDP_DIR / "eq_nvt_l0.mdp"
PRODUCTION_MDP = MDP_DIR / "production.mdp"

CREATE_HYBRID_LIGANDS_SCRIPT = SCRIPTS_DIR / "create-hybrid-ligands.sh"
