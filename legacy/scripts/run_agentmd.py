"""
AgentMD Example Script

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
"""

import sys
import os
current_dir = os.getcwd()
REPO_BASE_DIR = os.path.dirname(os.path.abspath(current_dir))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))


from biodsa.agents.agentmd import AgentMD

agent = AgentMD(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

patient_note = """
65-year-old male presenting to the ED with acute chest pain for the past 2 hours.

Chief Complaint: Substernal chest pain, pressure-like, radiating to left arm.

Past Medical History:
- Hypertension (on lisinopril)
- Type 2 Diabetes Mellitus (on metformin)
- Hyperlipidemia (on atorvastatin)
- Former smoker (quit 5 years ago, 30 pack-year history)

Vital Signs:
- BP: 145/90 mmHg
- HR: 88 bpm
- RR: 18/min

ECG: Sinus rhythm, ST depression in leads V4-V6 (1-2mm)

Labs:
- Troponin I: 0.08 ng/mL (elevated, normal <0.04)
"""

results = agent.go(patient_note)
print(results.final_response)
