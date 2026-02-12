from .coder_agent import CoderAgent
from .react_agent import ReactAgent
from .dswizard.agent import DSWizardAgent
from .deepevidence.agent import DeepEvidenceAgent
from .virtuallab.agent import VirtualLabAgent
from .slr_meta import SLRMetaAgent
from .scientific_skills_creator import ScientificSkillsCreator

# Deprecated: use ScientificSkillsCreator
RWDSkillsAgent = ScientificSkillsCreator

__all__ = [
    "CoderAgent",
    "ReactAgent",
    "DSWizardAgent",
    "DeepEvidenceAgent",
    "VirtualLabAgent",
    "SLRMetaAgent",
    "ScientificSkillsCreator",
    "RWDSkillsAgent",
]