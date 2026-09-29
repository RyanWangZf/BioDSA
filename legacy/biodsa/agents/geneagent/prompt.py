"""
Prompt templates for the GeneAgent gene set analysis agent.

These prompts are adapted from the original GeneAgent implementation
to guide the cascade verification workflow:
1. Initial analysis generation
2. Topic claim generation and verification
3. Analysis claim generation and verification
4. Final summary refinement

Reference: https://github.com/ncbi-nlp/GeneAgent
"""

# =============================================================================
# Stage 1: Initial Analysis Generation
# =============================================================================

BASELINE_SYSTEM_PROMPT = """You are an efficient and insightful assistant to a molecular biologist."""

BASELINE_USER_PROMPT = """Write a critical analysis of the biological processes performed by this system of interacting proteins.
Propose a brief name for the most prominent biological process performed by the system. 
Put the name at the top of the analysis as "Process: ".
Be concise, do not use unnecessary words.
Be textual, do not use any format symbols such as "*", "-" or other tokens.
Be specific, avoid overly general statements such as "the proteins are involved in various cellular processes".
Be factual, do not editorialize.
For each important point, describe your reasoning and supporting information.
For each biological function name, show the corresponding gene names.
Here is the gene set: {genes}"""

# =============================================================================
# Stage 2: Topic Verification (Process Name)
# =============================================================================

TOPIC_VERIFICATION_SYSTEM_PROMPT = """You are a helpful and objective fact-checker to verify the summary of gene set."""

TOPIC_CLAIM_GENERATION_PROMPT = """Here is the original process name for the gene set {genes}:
{process}
However, the process name might be false. Please generate decontextualized claims for the process name that need to be verified.
Only Return a list type that contain all generated claim strings, for example, ["claim_1", "claim_2"]"""

TOPIC_CLAIM_INSTRUCTION = """
Only generate claims with affirmative sentence for the entire gene set.
The gene set should only be separated by comma, e.g., "a,b,c".
Don't generate claims for the single gene or incomplete gene set.
Don't generate hypotheis claims over the previous analysis.
Please replace the statement like 'these genes', 'this system' with the core genes in the given gene set."""

TOPIC_MODIFICATION_PROMPT = """I have finished the verification for process name. Here is the verification report:
{verification_report}
You should only consider the successfully verified claims.
If claims are supported, you should retain the original process name and only can make a minor grammar revision. 
if claims are partially supported, you should discard the unsupported part.
If claims are refuted, you must replace the original process name with the most significant (i.e., top-1) biological function term summarized from the verification report.
Meanwhile, revise the original summaries using the verified (or updated) process name. Do not use sentence like "There are no direct evidence to..." """

TOPIC_MODIFICATION_INSTRUCTION = """
Put the updated process name at the top of the analysis as "Process: ".
Be concise, do not use unnecessary words.
Be textual, do not use any format symbols such as "*", "-" or other tokens. All modified sentence should encoded into utf-8.
Be specific, avoid overly general statements such as "the proteins are involved in various cellular processes".
Be factual, do not editorialize.
You must retain the gene names of each updated biological functions in the new summary."""

# =============================================================================
# Stage 3: Analysis Verification (Gene Functions)
# =============================================================================

ANALYSIS_CLAIM_GENERATION_PROMPT = """Here is the summary of the given gene set:
{summary}
However, the gene analysis in the summary might not support the updated process name. 
Please generate several decontextualized claims for the analytical narratives that need to be verified.
Only Return a list type that contain all generated claim strings, for example, ["claim_1", "claim_2"]"""

ANALYSIS_CLAIM_INSTRUCTION = """
Generate claims for genes and their biological functions around the updated process name.
Don't generate claims for the entire gene set or 'this system'.
Don't generate unworthy claims such as the summarization and reasoning over the previous analysis. 
Claims must contain the gene names and their biological process functions."""

ANALYSIS_SUMMARIZATION_PROMPT = """I have finished the verification for the revised summary. Here is the verification report:
{verification_report}
Please modify the summary according to the verification report again."""

ANALYSIS_SUMMARIZATION_INSTRUCTION = """ 
If the analytical narratives of genes can't directly support or related to the updated process name, you must propose a new brief biological process name from the analytical texts. 
Otherwise, you must retain the updated process name and only can make a grammar revision.
IF the claim is supported, you must complement the narratives by using the standard evidence of gene set functions (or gene summaries) in the verification report but don't change the updated process name. 
IF the claim is not supported, do not mention any statement like "... was not directly confirmed by..."
Be concise, do not use unnecessary format like **, only return the concise texts."""

# =============================================================================
# Verification Worker (Fact-Checker)
# =============================================================================

VERIFICATION_WORKER_SYSTEM_PROMPT = """You are a helpful fact-checker. 
Your task is to verify the claim using the provided tools. 
If there are evidences in your contents, please start a message with "Report:" and return your findings along with evidences."""

VERIFICATION_WORKER_USER_PROMPT = """Here is the claim needed to be verified:
{claim}
Try to use multiple tools to verify a claim and the verification process should be factual and objective.
Put your decision at the beginning of the evidences.
Don't use any format symbols such as '*', '-' or other tokens."""

VERIFICATION_REPORT_REQUEST = """Please start a message with "Report:" and return your findings if you have obtained the verification information."""

# =============================================================================
# Helper function to format prompts
# =============================================================================

def format_baseline_prompt(genes: str) -> str:
    """Format the baseline analysis prompt."""
    return BASELINE_USER_PROMPT.format(genes=genes)


def format_topic_claim_prompt(genes: str, process: str) -> str:
    """Format the topic claim generation prompt."""
    prompt = TOPIC_CLAIM_GENERATION_PROMPT.format(genes=genes, process=process)
    return prompt + TOPIC_CLAIM_INSTRUCTION


def format_topic_modification_prompt(verification_report: str) -> str:
    """Format the topic modification prompt."""
    prompt = TOPIC_MODIFICATION_PROMPT.format(verification_report=verification_report)
    return prompt + TOPIC_MODIFICATION_INSTRUCTION


def format_analysis_claim_prompt(summary: str) -> str:
    """Format the analysis claim generation prompt."""
    prompt = ANALYSIS_CLAIM_GENERATION_PROMPT.format(summary=summary)
    return prompt + ANALYSIS_CLAIM_INSTRUCTION


def format_analysis_summarization_prompt(verification_report: str) -> str:
    """Format the analysis summarization prompt."""
    prompt = ANALYSIS_SUMMARIZATION_PROMPT.format(verification_report=verification_report)
    return prompt + ANALYSIS_SUMMARIZATION_INSTRUCTION


def format_verification_prompt(claim: str) -> str:
    """Format the verification worker prompt."""
    return VERIFICATION_WORKER_USER_PROMPT.format(claim=claim)
