"""
AgentMD: Clinical Risk Prediction Agent

AgentMD is an LLM-based autonomous agent capable of applying clinical calculators
for risk prediction across various clinical contexts.

Based on:
@article{jin2025agentmd,
  title={Agentmd: Empowering language agents for risk prediction with large-scale clinical tool learning},
  author={Jin, Qiao and Wang, Zhizheng and Yang, Yifan and Zhu, Qingqing and Wright, Donald and Huang, Thomas and Khandekar, Nikhil and Wan, Nicholas and Ai, Xuguang and Wilbur, W John and others},
  journal={Nature Communications},
  volume={16},
  number={1},
  pages={9377},
  year={2025},
  publisher={Nature Publishing Group UK London}
}

Example usage:
    ```python
    from biodsa.agents.agentmd import AgentMD
    
    agent = AgentMD(
        model_name="gpt-4o",
        api_type="azure",
        api_key="your-api-key",
        endpoint="your-endpoint"
    )
    
    patient_note = '''
    65-year-old male with chest pain. History of hypertension and diabetes.
    ECG shows ST depression. Troponin elevated.
    '''
    
    results = agent.go(patient_note)
    print(results.final_response)
    ```
"""

from biodsa.agents.agentmd.agent import AgentMD

__all__ = [
    "AgentMD",
]
