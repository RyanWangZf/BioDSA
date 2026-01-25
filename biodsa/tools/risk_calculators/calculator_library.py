"""
Library of common clinical calculators.

This module provides a collection of validated clinical calculators
commonly used in clinical practice. Each calculator includes:
- Name and description
- Required input variables
- Calculation logic (Python code)
- Result interpretation guidelines

The module supports lazy loading of the full RiskCalcs toolkit (2,164 calculators)
from the original AgentMD repository when tools are triggered.
"""

import os
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# URL for the full RiskCalcs dataset from the original AgentMD repository
RISKCALCS_URL = "https://raw.githubusercontent.com/ncbi-nlp/Clinical-Tool-Learning/main/riskqa_evaluation/tools/riskcalcs.json"

# Default cache location: biomedical_data/agentmd/ relative to project root
# Can be overridden via BIODSA_DATA_DIR environment variable
def _get_default_cache_dir() -> Path:
    """Get the default cache directory for AgentMD data."""
    # Check for environment variable override
    if os.environ.get("BIODSA_DATA_DIR"):
        return Path(os.environ["BIODSA_DATA_DIR"]) / "agentmd"
    
    # Find project root by looking for biodsa package
    current = Path(__file__).resolve()
    # Go up from biodsa/tools/risk_calculators/calculator_library.py to project root
    project_root = current.parent.parent.parent.parent
    return project_root / "biomedical_data" / "agentmd"


DEFAULT_CACHE_DIR = _get_default_cache_dir()
RISKCALCS_CACHE_FILE = DEFAULT_CACHE_DIR / "riskcalcs.json"

# Thread lock for safe lazy loading
_riskcalcs_lock = threading.Lock()
_riskcalcs_cache: Optional[Dict[str, Any]] = None


def _download_riskcalcs(url: str = RISKCALCS_URL, cache_path: Path = RISKCALCS_CACHE_FILE) -> Dict[str, Any]:
    """
    Download the riskcalcs.json file from the remote repository.
    
    Args:
        url: URL to download the riskcalcs.json file from.
        cache_path: Path to save the downloaded file.
        
    Returns:
        Dictionary of calculators loaded from the JSON.
        
    Raises:
        RuntimeError: If download fails.
    """
    import urllib.request
    import urllib.error
    
    logger.info(f"Downloading riskcalcs.json from {url}...")
    
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read().decode('utf-8')
            calculators = json.loads(data)
            
            # Cache the file locally
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(calculators, f)
            
            logger.info(f"Successfully downloaded and cached {len(calculators)} calculators to {cache_path}")
            return calculators
            
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to download riskcalcs.json: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse riskcalcs.json: {e}")


def _load_riskcalcs_from_cache(cache_path: Path = RISKCALCS_CACHE_FILE) -> Optional[Dict[str, Any]]:
    """
    Load the riskcalcs.json file from the local cache.
    
    Args:
        cache_path: Path to the cached riskcalcs.json file.
        
    Returns:
        Dictionary of calculators if cache exists, None otherwise.
    """
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                calculators = json.load(f)
                logger.info(f"Loaded {len(calculators)} calculators from cache at {cache_path}")
                return calculators
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache from {cache_path}: {e}")
            return None
    return None


def get_riskcalcs(
    force_download: bool = False,
    cache_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Get the full RiskCalcs dataset with lazy loading and caching.
    
    This function implements lazy loading: the first call will either load
    from cache or download from the remote repository. Subsequent calls
    return the cached in-memory data.
    
    Args:
        force_download: If True, force re-download even if cache exists.
        cache_path: Optional custom path for the cache file.
        
    Returns:
        Dictionary mapping calculator IDs to calculator data.
        
    Example:
        ```python
        calcs = get_riskcalcs()
        print(f"Loaded {len(calcs)} calculators")
        
        # Access a specific calculator
        chads2 = calcs.get("11401607")
        print(chads2["title"])
        ```
    """
    global _riskcalcs_cache
    
    if cache_path is None:
        cache_path = RISKCALCS_CACHE_FILE
    
    # Fast path: return cached data if available
    if _riskcalcs_cache is not None and not force_download:
        return _riskcalcs_cache
    
    with _riskcalcs_lock:
        # Double-check after acquiring lock
        if _riskcalcs_cache is not None and not force_download:
            return _riskcalcs_cache
        
        # Try to load from local cache first
        if not force_download:
            cached = _load_riskcalcs_from_cache(cache_path)
            if cached is not None:
                _riskcalcs_cache = cached
                return _riskcalcs_cache
        
        # Download from remote repository
        _riskcalcs_cache = _download_riskcalcs(cache_path=cache_path)
        return _riskcalcs_cache


def convert_riskcalc_to_calculator(calc_id: str, calc_data: Dict[str, Any]) -> "Calculator":
    """
    Convert a RiskCalc JSON entry to a Calculator dataclass.
    
    Args:
        calc_id: The calculator ID (PMID or unique identifier).
        calc_data: The calculator data from riskcalcs.json.
        
    Returns:
        Calculator dataclass instance.
    """
    # Extract the computation section which contains Python code
    computation = calc_data.get("computation", "")
    
    # Parse variables from the computation if available
    # The computation section typically includes a function definition
    variables = []
    
    return Calculator(
        id=calc_id,
        name=calc_data.get("title", "").strip(),
        category=calc_data.get("specialty", "general").split(",")[0].strip().lower(),
        purpose=calc_data.get("purpose", "").strip(),
        variables=variables,  # Variables are embedded in the computation
        formula=computation,
        interpretation={
            "description": calc_data.get("interpretation", ""),
            "utility": calc_data.get("utility", ""),
        },
        reference=calc_data.get("example", ""),
        pmid=calc_id,
    )


def get_all_calculators(include_common: bool = True) -> Dict[str, "Calculator"]:
    """
    Get all available calculators, including both built-in common calculators
    and the full RiskCalcs dataset.
    
    Args:
        include_common: If True, include the COMMON_CALCULATORS.
        
    Returns:
        Dictionary mapping calculator IDs to Calculator instances.
    """
    all_calcs = {}
    
    if include_common:
        all_calcs.update(COMMON_CALCULATORS)
    
    # Load the full RiskCalcs dataset
    try:
        riskcalcs = get_riskcalcs()
        for calc_id, calc_data in riskcalcs.items():
            if calc_id not in all_calcs:  # Don't override common calculators
                all_calcs[calc_id] = convert_riskcalc_to_calculator(calc_id, calc_data)
    except Exception as e:
        logger.warning(f"Failed to load RiskCalcs dataset: {e}. Using only common calculators.")
    
    return all_calcs


def get_riskcalc_raw(calc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the raw data for a specific calculator from the RiskCalcs dataset.
    
    This returns the original JSON data without conversion to Calculator class,
    which is useful for accessing the full computation code and examples.
    
    Args:
        calc_id: The calculator ID.
        
    Returns:
        Raw calculator data dictionary, or None if not found.
    """
    try:
        riskcalcs = get_riskcalcs()
        return riskcalcs.get(calc_id)
    except Exception as e:
        logger.warning(f"Failed to load RiskCalcs for ID {calc_id}: {e}")
        return None


def search_riskcalcs(
    query: str,
    fields: Optional[List[str]] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search the RiskCalcs dataset using keyword matching.
    
    Args:
        query: Search query string.
        fields: Fields to search in. Defaults to title, purpose, specialty.
        limit: Maximum number of results to return.
        
    Returns:
        List of matching calculator data dictionaries with their IDs.
    """
    if fields is None:
        fields = ["title", "purpose", "specialty"]
    
    query_lower = query.lower()
    query_terms = set(query_lower.split())
    
    results = []
    
    try:
        riskcalcs = get_riskcalcs()
        
        for calc_id, calc_data in riskcalcs.items():
            # Combine searchable text from specified fields
            searchable = " ".join(
                str(calc_data.get(field, "")).lower() 
                for field in fields
            )
            
            # Calculate match score based on term overlap
            searchable_terms = set(searchable.split())
            overlap = len(query_terms & searchable_terms)
            
            if overlap > 0 or query_lower in searchable:
                # Boost score if query appears as substring
                score = overlap
                if query_lower in searchable:
                    score += 5
                
                results.append({
                    "id": calc_id,
                    "score": score,
                    **calc_data
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
        
    except Exception as e:
        logger.warning(f"Search failed: {e}")
        return []


@dataclass
class Calculator:
    """Represents a clinical calculator."""
    id: str
    name: str
    category: str
    purpose: str
    variables: List[Dict[str, Any]]
    formula: str  # Python code string
    interpretation: Dict[str, str]
    reference: str
    pmid: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "purpose": self.purpose,
            "variables": self.variables,
            "formula": self.formula,
            "interpretation": self.interpretation,
            "reference": self.reference,
            "pmid": self.pmid,
        }


# ============================================================================
# CARDIOVASCULAR CALCULATORS
# ============================================================================

HEART_SCORE = Calculator(
    id="heart_score",
    name="HEART Score",
    category="cardiovascular",
    purpose="Risk stratification for patients with chest pain to predict major adverse cardiac events (MACE) at 6 weeks",
    variables=[
        {"name": "history", "type": "int", "range": [0, 2], "description": "0=slightly suspicious, 1=moderately suspicious, 2=highly suspicious"},
        {"name": "ecg", "type": "int", "range": [0, 2], "description": "0=normal, 1=non-specific repolarization, 2=significant ST depression"},
        {"name": "age", "type": "int", "range": [0, 2], "description": "0=<45, 1=45-64, 2=≥65"},
        {"name": "risk_factors", "type": "int", "range": [0, 2], "description": "0=no factors, 1=1-2 factors, 2=≥3 factors or history of atherosclerotic disease"},
        {"name": "troponin", "type": "int", "range": [0, 2], "description": "0=normal, 1=1-3x normal, 2=>3x normal"},
    ],
    formula='''
def calculate_heart_score(history, ecg, age, risk_factors, troponin):
    """Calculate HEART score for chest pain risk stratification."""
    score = history + ecg + age + risk_factors + troponin
    
    if score <= 3:
        risk = "Low risk (0.9-1.7% MACE)"
        recommendation = "Consider early discharge with outpatient follow-up"
    elif score <= 6:
        risk = "Moderate risk (12-16.6% MACE)"
        recommendation = "Admit for observation, consider non-invasive testing"
    else:
        risk = "High risk (50-65% MACE)"
        recommendation = "Early invasive measures"
    
    return {"score": score, "risk": risk, "recommendation": recommendation}
''',
    interpretation={
        "0-3": "Low risk (0.9-1.7% 6-week MACE) - Consider early discharge",
        "4-6": "Moderate risk (12-16.6% 6-week MACE) - Admit for observation",
        "7-10": "High risk (50-65% 6-week MACE) - Early invasive strategy"
    },
    reference="Six et al. Chest pain in the emergency room: value of the HEART score. Neth Heart J. 2008",
    pmid="19949000"
)

CHA2DS2_VASC = Calculator(
    id="cha2ds2_vasc",
    name="CHA2DS2-VASc Score",
    category="cardiovascular",
    purpose="Estimate stroke risk in patients with atrial fibrillation to guide anticoagulation decisions",
    variables=[
        {"name": "chf", "type": "bool", "description": "Congestive heart failure (1 point)"},
        {"name": "hypertension", "type": "bool", "description": "Hypertension (1 point)"},
        {"name": "age_75_plus", "type": "bool", "description": "Age ≥75 years (2 points)"},
        {"name": "diabetes", "type": "bool", "description": "Diabetes mellitus (1 point)"},
        {"name": "stroke_tia", "type": "bool", "description": "Prior stroke/TIA/thromboembolism (2 points)"},
        {"name": "vascular_disease", "type": "bool", "description": "Vascular disease (1 point)"},
        {"name": "age_65_74", "type": "bool", "description": "Age 65-74 years (1 point)"},
        {"name": "female", "type": "bool", "description": "Female sex (1 point)"},
    ],
    formula='''
def calculate_cha2ds2_vasc(chf, hypertension, age_75_plus, diabetes, stroke_tia, vascular_disease, age_65_74, female):
    """Calculate CHA2DS2-VASc score for stroke risk in AF."""
    score = 0
    score += 1 if chf else 0
    score += 1 if hypertension else 0
    score += 2 if age_75_plus else 0
    score += 1 if diabetes else 0
    score += 2 if stroke_tia else 0
    score += 1 if vascular_disease else 0
    score += 1 if age_65_74 else 0
    score += 1 if female else 0
    
    # Annual stroke risk estimates
    risk_table = {
        0: 0.2, 1: 0.6, 2: 2.2, 3: 3.2, 4: 4.8,
        5: 7.2, 6: 9.7, 7: 11.2, 8: 10.8, 9: 12.2
    }
    annual_risk = risk_table.get(score, 12.2)
    
    if score == 0:
        recommendation = "No anticoagulation recommended"
    elif score == 1:
        recommendation = "Consider anticoagulation (especially if male)"
    else:
        recommendation = "Anticoagulation recommended (unless contraindicated)"
    
    return {"score": score, "annual_stroke_risk_percent": annual_risk, "recommendation": recommendation}
''',
    interpretation={
        "0": "Low risk (0.2%/year) - No anticoagulation",
        "1": "Low-moderate risk (0.6%/year) - Consider anticoagulation",
        "2+": "Moderate-high risk (≥2.2%/year) - Anticoagulation recommended"
    },
    reference="Lip et al. Refining clinical risk stratification for predicting stroke and thromboembolism in atrial fibrillation. Chest. 2010",
    pmid="20299623"
)

WELLS_PE = Calculator(
    id="wells_pe",
    name="Wells' Criteria for Pulmonary Embolism",
    category="cardiovascular",
    purpose="Estimate pre-test probability of pulmonary embolism",
    variables=[
        {"name": "clinical_signs_dvt", "type": "bool", "description": "Clinical signs/symptoms of DVT (3 points)"},
        {"name": "pe_most_likely", "type": "bool", "description": "PE is #1 diagnosis or equally likely (3 points)"},
        {"name": "heart_rate_over_100", "type": "bool", "description": "Heart rate > 100 bpm (1.5 points)"},
        {"name": "immobilization_surgery", "type": "bool", "description": "Immobilization/surgery in previous 4 weeks (1.5 points)"},
        {"name": "previous_dvt_pe", "type": "bool", "description": "Previous DVT/PE (1.5 points)"},
        {"name": "hemoptysis", "type": "bool", "description": "Hemoptysis (1 point)"},
        {"name": "malignancy", "type": "bool", "description": "Malignancy (treatment within 6 months, palliative) (1 point)"},
    ],
    formula='''
def calculate_wells_pe(clinical_signs_dvt, pe_most_likely, heart_rate_over_100, 
                       immobilization_surgery, previous_dvt_pe, hemoptysis, malignancy):
    """Calculate Wells' score for PE probability."""
    score = 0.0
    score += 3.0 if clinical_signs_dvt else 0
    score += 3.0 if pe_most_likely else 0
    score += 1.5 if heart_rate_over_100 else 0
    score += 1.5 if immobilization_surgery else 0
    score += 1.5 if previous_dvt_pe else 0
    score += 1.0 if hemoptysis else 0
    score += 1.0 if malignancy else 0
    
    if score <= 4:
        probability = "PE unlikely (<4 points)"
        recommendation = "Check D-dimer. If negative, PE excluded. If positive, consider CTPA."
    else:
        probability = "PE likely (>4 points)"
        recommendation = "Proceed directly to CTPA (or V/Q scan if CTPA contraindicated)"
    
    return {"score": score, "probability": probability, "recommendation": recommendation}
''',
    interpretation={
        "≤4": "PE unlikely - D-dimer to exclude; if positive, imaging",
        ">4": "PE likely - Proceed to imaging (CTPA or V/Q scan)"
    },
    reference="Wells et al. Derivation of a simple clinical model to categorize patients probability of pulmonary embolism. Thromb Haemost. 2000",
    pmid="10744147"
)


# ============================================================================
# MORTALITY/SEVERITY CALCULATORS
# ============================================================================

QSOFA = Calculator(
    id="qsofa",
    name="qSOFA (Quick SOFA) Score",
    category="mortality",
    purpose="Rapid bedside screening for sepsis and risk of poor outcomes in suspected infection",
    variables=[
        {"name": "altered_mental_status", "type": "bool", "description": "Altered mental status (GCS <15)"},
        {"name": "respiratory_rate_22_plus", "type": "bool", "description": "Respiratory rate ≥22/min"},
        {"name": "systolic_bp_100_or_less", "type": "bool", "description": "Systolic blood pressure ≤100 mmHg"},
    ],
    formula='''
def calculate_qsofa(altered_mental_status, respiratory_rate_22_plus, systolic_bp_100_or_less):
    """Calculate qSOFA score for sepsis screening."""
    score = 0
    score += 1 if altered_mental_status else 0
    score += 1 if respiratory_rate_22_plus else 0
    score += 1 if systolic_bp_100_or_less else 0
    
    if score >= 2:
        risk = "High risk of poor outcomes"
        recommendation = "Consider full SOFA assessment, ICU-level care, and sepsis workup"
    else:
        risk = "Lower risk, but clinical judgment required"
        recommendation = "Continue monitoring; consider sepsis if clinical suspicion remains"
    
    return {"score": score, "risk": risk, "recommendation": recommendation}
''',
    interpretation={
        "0-1": "Lower risk - Continue monitoring",
        "2-3": "High risk - Associated with >10% in-hospital mortality"
    },
    reference="Seymour et al. Assessment of Clinical Criteria for Sepsis. JAMA. 2016",
    pmid="26903338"
)

CURB65 = Calculator(
    id="curb65",
    name="CURB-65 Score",
    category="respiratory",
    purpose="Assess severity of community-acquired pneumonia and guide site-of-care decisions",
    variables=[
        {"name": "confusion", "type": "bool", "description": "Confusion (new disorientation)"},
        {"name": "bun_over_19", "type": "bool", "description": "BUN > 19 mg/dL (>7 mmol/L)"},
        {"name": "respiratory_rate_30_plus", "type": "bool", "description": "Respiratory rate ≥30/min"},
        {"name": "sbp_under_90_or_dbp_under_60", "type": "bool", "description": "SBP <90 or DBP ≤60 mmHg"},
        {"name": "age_65_plus", "type": "bool", "description": "Age ≥65 years"},
    ],
    formula='''
def calculate_curb65(confusion, bun_over_19, respiratory_rate_30_plus, sbp_under_90_or_dbp_under_60, age_65_plus):
    """Calculate CURB-65 score for pneumonia severity."""
    score = 0
    score += 1 if confusion else 0
    score += 1 if bun_over_19 else 0
    score += 1 if respiratory_rate_30_plus else 0
    score += 1 if sbp_under_90_or_dbp_under_60 else 0
    score += 1 if age_65_plus else 0
    
    mortality_30day = {0: 0.6, 1: 2.7, 2: 6.8, 3: 14.0, 4: 27.8, 5: 27.8}
    mortality = mortality_30day.get(score, 27.8)
    
    if score <= 1:
        recommendation = "Consider outpatient treatment"
        disposition = "Low risk"
    elif score == 2:
        recommendation = "Consider short inpatient stay or hospital-supervised outpatient"
        disposition = "Moderate risk"
    else:
        recommendation = "Manage as severe pneumonia; consider ICU admission if score 4-5"
        disposition = "High risk"
    
    return {"score": score, "30_day_mortality_percent": mortality, 
            "disposition": disposition, "recommendation": recommendation}
''',
    interpretation={
        "0-1": "Low risk (mortality <3%) - Consider outpatient treatment",
        "2": "Moderate risk (mortality ~6%) - Short inpatient or supervised outpatient",
        "3+": "High risk (mortality >14%) - Hospitalize; consider ICU if 4-5"
    },
    reference="Lim et al. Defining community acquired pneumonia severity. Thorax. 2003",
    pmid="12728155"
)

MELD = Calculator(
    id="meld",
    name="MELD Score (Model for End-Stage Liver Disease)",
    category="hepatic",
    purpose="Assess severity of chronic liver disease and prioritize organ allocation for liver transplant",
    variables=[
        {"name": "creatinine", "type": "float", "unit": "mg/dL", "description": "Serum creatinine (capped at 4.0)"},
        {"name": "bilirubin", "type": "float", "unit": "mg/dL", "description": "Total bilirubin"},
        {"name": "inr", "type": "float", "description": "INR"},
        {"name": "on_dialysis", "type": "bool", "description": "On dialysis (at least twice in past week)"},
    ],
    formula='''
import math

def calculate_meld(creatinine, bilirubin, inr, on_dialysis=False):
    """Calculate MELD score for liver disease severity."""
    # Apply constraints
    if on_dialysis:
        creatinine = 4.0
    creatinine = max(1.0, min(creatinine, 4.0))
    bilirubin = max(1.0, bilirubin)
    inr = max(1.0, inr)
    
    # MELD formula
    meld = (
        0.957 * math.log(creatinine) +
        0.378 * math.log(bilirubin) +
        1.120 * math.log(inr) +
        0.643
    ) * 10
    
    meld = round(min(40, max(6, meld)))
    
    # 3-month mortality estimates
    if meld < 10:
        mortality = "~2%"
    elif meld < 20:
        mortality = "~6%"
    elif meld < 30:
        mortality = "~20%"
    elif meld < 40:
        mortality = "~52%"
    else:
        mortality = ">70%"
    
    return {"meld_score": meld, "3_month_mortality": mortality}
''',
    interpretation={
        "6-9": "Low (~2% 3-month mortality)",
        "10-19": "Moderate (~6% 3-month mortality)",
        "20-29": "High (~20% 3-month mortality)",
        "30-39": "Very high (~52% 3-month mortality)",
        "40": "Maximum score (>70% 3-month mortality)"
    },
    reference="Kamath et al. A model to predict survival in patients with end-stage liver disease. Hepatology. 2001",
    pmid="11172350"
)


# ============================================================================
# RENAL CALCULATORS
# ============================================================================

EGFR_CKDEPI = Calculator(
    id="egfr_ckdepi",
    name="eGFR (CKD-EPI 2021)",
    category="renal",
    purpose="Estimate glomerular filtration rate for CKD staging and drug dosing",
    variables=[
        {"name": "creatinine", "type": "float", "unit": "mg/dL", "description": "Serum creatinine"},
        {"name": "age", "type": "int", "unit": "years", "description": "Patient age"},
        {"name": "sex", "type": "str", "description": "Sex (male or female)"},
    ],
    formula='''
def calculate_egfr_ckdepi(creatinine, age, sex):
    """Calculate eGFR using CKD-EPI 2021 equation (race-free)."""
    sex = sex.lower()
    
    if sex == 'female':
        if creatinine <= 0.7:
            egfr = 142 * (creatinine / 0.7) ** (-0.241) * (0.9938 ** age)
        else:
            egfr = 142 * (creatinine / 0.7) ** (-1.200) * (0.9938 ** age)
    else:  # male
        if creatinine <= 0.9:
            egfr = 142 * (creatinine / 0.9) ** (-0.302) * (0.9938 ** age)
        else:
            egfr = 142 * (creatinine / 0.9) ** (-1.200) * (0.9938 ** age)
    
    egfr = round(egfr, 1)
    
    # CKD staging
    if egfr >= 90:
        stage = "G1 (Normal or high)"
    elif egfr >= 60:
        stage = "G2 (Mildly decreased)"
    elif egfr >= 45:
        stage = "G3a (Mildly to moderately decreased)"
    elif egfr >= 30:
        stage = "G3b (Moderately to severely decreased)"
    elif egfr >= 15:
        stage = "G4 (Severely decreased)"
    else:
        stage = "G5 (Kidney failure)"
    
    return {"egfr": egfr, "unit": "mL/min/1.73m²", "ckd_stage": stage}
''',
    interpretation={
        "≥90": "G1 - Normal or high",
        "60-89": "G2 - Mildly decreased",
        "45-59": "G3a - Mildly to moderately decreased",
        "30-44": "G3b - Moderately to severely decreased",
        "15-29": "G4 - Severely decreased",
        "<15": "G5 - Kidney failure"
    },
    reference="Inker et al. New Creatinine- and Cystatin C-Based Equations. N Engl J Med. 2021",
    pmid="34554658"
)


# ============================================================================
# BLEEDING RISK CALCULATORS
# ============================================================================

HAS_BLED = Calculator(
    id="has_bled",
    name="HAS-BLED Score",
    category="bleeding",
    purpose="Estimate risk of major bleeding in patients on anticoagulation for atrial fibrillation",
    variables=[
        {"name": "hypertension", "type": "bool", "description": "Hypertension (uncontrolled, SBP >160)"},
        {"name": "renal_disease", "type": "bool", "description": "Abnormal renal function (dialysis, transplant, Cr >2.3)"},
        {"name": "liver_disease", "type": "bool", "description": "Abnormal liver function (cirrhosis, bili >2x, AST/ALT >3x)"},
        {"name": "stroke_history", "type": "bool", "description": "Stroke history"},
        {"name": "bleeding_history", "type": "bool", "description": "Prior major bleeding or predisposition"},
        {"name": "labile_inr", "type": "bool", "description": "Labile INR (TTR <60%)"},
        {"name": "elderly", "type": "bool", "description": "Age >65"},
        {"name": "drugs", "type": "bool", "description": "Drugs (antiplatelet agents, NSAIDs)"},
        {"name": "alcohol", "type": "bool", "description": "Alcohol use (≥8 drinks/week)"},
    ],
    formula='''
def calculate_has_bled(hypertension, renal_disease, liver_disease, stroke_history,
                       bleeding_history, labile_inr, elderly, drugs, alcohol):
    """Calculate HAS-BLED score for bleeding risk."""
    score = 0
    score += 1 if hypertension else 0
    score += 1 if renal_disease else 0
    score += 1 if liver_disease else 0
    score += 1 if stroke_history else 0
    score += 1 if bleeding_history else 0
    score += 1 if labile_inr else 0
    score += 1 if elderly else 0
    score += 1 if drugs else 0
    score += 1 if alcohol else 0
    
    # Annual major bleeding risk
    risk_percent = {0: 1.13, 1: 1.02, 2: 1.88, 3: 3.74, 4: 8.70, 5: 12.5}.get(min(score, 5), 12.5)
    
    if score >= 3:
        risk = "High bleeding risk"
        recommendation = "Caution with anticoagulation; address modifiable risk factors"
    else:
        risk = "Low to moderate bleeding risk"
        recommendation = "Anticoagulation generally appropriate if indicated"
    
    return {"score": score, "annual_bleeding_risk_percent": risk_percent,
            "risk": risk, "recommendation": recommendation}
''',
    interpretation={
        "0-2": "Low to moderate bleeding risk - Anticoagulation generally safe",
        "3+": "High bleeding risk - Caution; address modifiable factors"
    },
    reference="Pisters et al. A novel user-friendly score (HAS-BLED). Chest. 2010",
    pmid="20299623"
)


# ============================================================================
# REGISTRY OF ALL CALCULATORS
# ============================================================================

COMMON_CALCULATORS: Dict[str, Calculator] = {
    # Cardiovascular
    "heart_score": HEART_SCORE,
    "cha2ds2_vasc": CHA2DS2_VASC,
    "wells_pe": WELLS_PE,
    # Mortality/Severity
    "qsofa": QSOFA,
    "curb65": CURB65,
    "meld": MELD,
    # Renal
    "egfr_ckdepi": EGFR_CKDEPI,
    # Bleeding
    "has_bled": HAS_BLED,
}


def get_calculator_by_name(name: str) -> Optional[Calculator]:
    """Get a calculator by its name/id."""
    return COMMON_CALCULATORS.get(name.lower())


def get_calculators_by_category(category: str) -> List[Calculator]:
    """Get all calculators in a category."""
    return [c for c in COMMON_CALCULATORS.values() if c.category == category.lower()]


def list_calculator_names() -> List[str]:
    """List all available calculator names."""
    return list(COMMON_CALCULATORS.keys())


def list_categories() -> List[str]:
    """List all calculator categories."""
    return list(set(c.category for c in COMMON_CALCULATORS.values()))


def get_calculator_summary(calc: Calculator) -> str:
    """Get a formatted summary of a calculator."""
    variables_str = ", ".join([v["name"] for v in calc.variables])
    return f"""
**{calc.name}** ({calc.id})
- Category: {calc.category}
- Purpose: {calc.purpose}
- Variables: {variables_str}
- Reference: {calc.reference}
"""
