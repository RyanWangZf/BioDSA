"""
Clinical Risk Calculators (RiskCalcs) Toolkit.

This module provides a comprehensive toolkit of clinical calculators for risk
prediction and patient assessment, inspired by the AgentMD project.

The toolkit includes:
- Risk calculator retrieval and embedding
- Clinical calculator execution engine
- Pre-built common clinical calculators
- Custom calculator definition support

Reference:
@article{jin2024agentmd,
  title={AgentMD: Empowering Language Agents for Risk Prediction with Large-Scale Clinical Tool Learning},
  author={Jin, Qiao and Wang, Zhizheng and Yang, Yifan and Zhu, Qingqing and Wright, Donald and 
          Huang, Thomas and Wilbur, W John and He, Zhe and Taylor, Andrew and Chen, Qingyu and others},
  journal={arXiv preprint arXiv:2402.13225},
  year={2024}
}
"""

from biodsa.tools.risk_calculators.calculator_library import (
    COMMON_CALCULATORS,
    get_calculator_by_name,
    get_calculators_by_category,
    list_calculator_names,
    list_categories,
    # Full RiskCalcs dataset (lazy loading with remote fetch)
    get_riskcalcs,
    get_all_calculators,
    get_riskcalc_raw,
    search_riskcalcs,
    RISKCALCS_URL,
)

from biodsa.tools.risk_calculators.retrieval import (
    RiskCalcRetriever,
    encode_query,
    retrieve_calculators,
)

from biodsa.tools.risk_calculators.execution import (
    execute_calculator_code,
    validate_calculator_inputs,
    format_calculator_result,
)

__all__ = [
    # Calculator library (common calculators)
    "COMMON_CALCULATORS",
    "get_calculator_by_name",
    "get_calculators_by_category",
    "list_calculator_names",
    "list_categories",
    # Full RiskCalcs dataset (2,164 calculators with lazy loading)
    "get_riskcalcs",
    "get_all_calculators",
    "get_riskcalc_raw",
    "search_riskcalcs",
    "RISKCALCS_URL",
    # Retrieval
    "RiskCalcRetriever",
    "encode_query",
    "retrieve_calculators",
    # Execution
    "execute_calculator_code",
    "validate_calculator_inputs",
    "format_calculator_result",
]
