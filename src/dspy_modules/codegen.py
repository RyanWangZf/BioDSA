import pdb
import re
import random
from typing import Literal
from tqdm import tqdm
import dspy
from bs4 import BeautifulSoup

from src.dspy_modules.llm import get_openai_model, get_vertexai_model, get_aws_model
from src.dspy_modules.parallel import batch_call_dspy_module
from src.google_search import query_google_search
from src.api import extract_code
    

class PythonCodeGeneration(dspy.Signature):
    """Generate Python code from a question and a dataset schema."""
    question = dspy.InputField(desc="The question to ask.")
    dataset_schema = dspy.InputField(desc="The schema of the data.")
    output_code = dspy.OutputField(
        desc="The generated Python code. The output code should be in HTML format, i.e., wrapped by <code> and </code> tags, e.g., <code>print('Hello, World!')</code>",
        prefix="<code>")

class RCodeGeneration(dspy.Signature):
    """Generate R code from a question and a dataset schema."""
    question = dspy.InputField(desc="The question to ask.")
    dataset_schema = dspy.InputField(desc="The schema of the data.")
    output_code = dspy.OutputField(desc="The generated R code. The output code should be in HTML format, i.e., wrapped by <code> and </code> tags, e.g., <code>print('Hello, World!')</code>.")

def validate_code_format(output_code):
    """Validate the code format."""
    # try to parse and extract the code
    extracted = extract_code(output_code)
    if len(extracted) == 0:
        return False
    return True

class DSPyCodeGeneration(dspy.Module):
    def __init__(self, language):
        super().__init__()
        if language == "python":
            self.prog = dspy.Predict(signature=PythonCodeGeneration)
        elif language == "R":
            self.prog = dspy.Predict(signature=RCodeGeneration)
        else:
            raise ValueError("The language should be either 'python' or 'R'.")
    
    def forward(self, question, dataset_schema="", temperature=0.7):
        """Args:

        question (str): the question to ask
        dataset_schema (str): the schema of the data
        """
        response = self.prog(question=question, 
                                dataset_schema=dataset_schema,
                                **{
                                    "temperature": temperature,
                                }
                                )

        output_code = extract_code(response.output_code)

        # add assertions to check the output code format
        dspy.Assert(validate_code_format(output_code), f"The output code format is invalid. Get {response.output_code}.")

        return {
            "output_code": output_code,
        }

def extract_searh_query(_raw_output: str) -> str:
    # Using 'html.parser' to parse the content
    try:
        soup = BeautifulSoup(_raw_output, "html.parser")
        _raw_output = soup.find("query").text
        _raw_output = _raw_output
    except:
        _raw_output = None
    return _raw_output

class RAGPythonCodeGeneration(dspy.Signature):
    """Generate Python code from a question and a dataset schema."""
    context = dspy.InputField(desc="The additional context to provide more information.")
    question = dspy.InputField(desc="The question to ask.")
    dataset_schema = dspy.InputField(desc="The schema of the data.")
    output_code = dspy.OutputField(
        desc="The generated Python code. The output code should be in HTML format, i.e., wrapped by <code> and </code> tags, e.g., <code>print('Hello, World!')</code>",
        prefix="<code>")

class GenerateSearchQuery(dspy.Signature):
    """Write a google search query that obtains additional information from Google to help generate the right biomedical and medical data science code.
Quesions you can ask include but not limited to:
- coding questions such as how to use specific libraries
- data science questions such as how to preprocess data
- biomedical and medical questions to bridge the knowledge gap required to generate the right code.
"""
    dataset_schema = dspy.InputField(desc="The schema of the dataset.")
    user_question = dspy.InputField(desc="The user's raw input question.")
    google_search_query = dspy.OutputField(
        desc="The generated query for Google search. Wrap the query in <query> and </query> tags, e.g., <query>How to read a CSV file in Python?</query>.",
        prefix="<query>"
        )

class DSPyRAGCodeGeneration(dspy.Module):
    def __init__(self, language, max_tokens=2048):
        super().__init__()
        self.generate_query = dspy.Predict(signature=GenerateSearchQuery)

        if language == "python":
            self.prog = dspy.Predict(signature=RAGPythonCodeGeneration, max_tokens=max_tokens)
        elif language == "R":
            raise NotImplementedError("RAG for R code generation is not implemented yet.")
            # self.prog = dspy.RAG(signature=RCodeGeneration, max_tokens=max_tokens)
        else:
            raise ValueError("The language should be either 'python' or 'R'.")
    
    def forward(self, question, dataset_schema="", temperature=0.2):
        """Args:

        question (str): the question to ask
        dataset_schema (str): the schema of the data
        """
        search_query = self.generate_query(
            dataset_schema=dataset_schema, 
            user_question=question,
            temperature=temperature
            )
        parsed_search_query = search_query.google_search_query
        parsed_search_query = extract_searh_query(parsed_search_query)
        if parsed_search_query is not None:
            context = query_google_search(parsed_search_query, top_k=10)
            if len(context) > 0:
                context = [c.page_content for c in context]
                context = "\n".join(context)
            else: context = ""
        else: context = ""

        if len(context) == 0: print("No context found. The generated search query is:", parsed_search_query)
        
        # print("Context found:", context)
        # print("Search query:", parsed_search_query)

        response = self.prog(
            question=question,
            context=context,
            dataset_schema=dataset_schema,
            **{
                "temperature": temperature,
            }
            )

        output_code = extract_code(response.output_code)

        # add assertions to check the output code format
        dspy.Assert(validate_code_format(output_code), f"The output code format is invalid. Get {response.output_code}.")

        return {
            "generated_search_query": search_query.google_search_query,
            "context_found": context,
            "output_code": output_code,
        }


# Set up the evaluation metric
class Assess(dspy.Signature):
    """Evaluate the quality of the generated code.
"""
    output_code = dspy.InputField(desc="The generated code.")
    reference_answer = dspy.InputField()
    assessment_question = dspy.InputField()
    quality_score = dspy.OutputField(desc="Score ranging from 0 to 5, the higher the better. Return the score directly in the HTML format wrapped by <score> and </score>, e.g., <score>5</score>.")

def extract_score(_raw_output: str) -> str:
    # Using 'html.parser' to parse the content
    try:
        soup = BeautifulSoup(_raw_output, "html.parser")
        _raw_output = soup.find("score").text
        _raw_output = int(_raw_output)
    except:
        _raw_output = None
    return _raw_output

def check_code_correctness_llm(example, output_code, trace=None):
    """Score the quality of the generated code referring to the reference answer."""
    generated_code = output_code["output_code"]
    # llm = get_vertexai_model("gemini-pro")
    llm = get_openai_model("azure-gpt-4o")
    with dspy.context(lm=llm):
        assessment_question = "Referring to the reference answer, how good does the output code answer the user's question? Return the score directly in the HTML format wrapped by <score> and </score>, e.g., <score>4</score>."
        results = dspy.Predict(Assess)(
            output_code=generated_code, 
            reference_answer=example["output_code"], 
            assessment_question=assessment_question,
            question=example["question"]
            )
    score = extract_score(results.quality_score)
    indicator = score/5 if score is not None else 0
    return indicator

def check_code_correctness_exec(question, dataset_schema, output_code, reference_answer):
    """Check if the output code will lead to the same output as the reference answer by executing the code."""
    # TODO
    pass

def run_dspy_codegen(
    batch_inputs: list[dict],
    llm: str,
    language: Literal["python", "R"],
    batch_size: int = None,
    mode: Literal["Vanilla", "Optimized", "RAG", "FewShot"] = "Vanilla",
    temperature: float = 0.7
    ):
    if llm in ["openai-gpt-4o", "openai-gpt-4o-mini", "azure-gpt-4o", "azure-gpt-4", "azure-gpt-35", "azure-gpt-4o-mini"]:
        llm = get_openai_model(llm, temperature=temperature)
    elif llm in ["gemini-pro", "gemini-flash"]:
        llm = get_vertexai_model(llm, temperature=temperature)
    elif llm in ["opus", "sonnet"]:
        llm = get_aws_model(llm, temperature=temperature)
    else:
        raise ValueError(f"Model name {llm} is not supported.")

    import os
    REPO_BASE_DIR = os.environ.get("REPO_BASE_DIR", None)
    if REPO_BASE_DIR is None:
        raise ValueError("Please set the `REPO_BASE_DIR` environment variable.")

    dspy.settings.configure(lm=llm)
    if mode.lower() == "vanilla":
        codegen = DSPyCodeGeneration(language=language)
    elif mode.lower() == "optimized":
        codegen = DSPyCodeGeneration(language=language)
        if language == "python":
            # load the optimized model configuration
            codegen.load(f"{REPO_BASE_DIR}/dspy_config/compiled_codegen_gpt4o_demos.json")
        elif language == "R":
            # load the optimized model configuration
            codegen.load(f"{REPO_BASE_DIR}/dspy_config/compiled_codegen_gpt4o_demos_R.json")
        else:
            raise ValueError("The language should be either 'python' or 'R'.")
    elif mode.lower() == "rag":
        codegen = DSPyRAGCodeGeneration(language=language)
        # load the optimized RAG model configuration
        codegen.load(f"{REPO_BASE_DIR}/dspy_config/compiled_codegen_gpt4o_rag.json")
    elif mode.lower() == "fewshot":
        codegen = DSPyCodeGeneration(language=language)
        # load the optimized few-shot model configuration
        codegen.load(f"{REPO_BASE_DIR}/dspy_config/compiled_codegen_gpt4o_fewshot.json")
    else:
        raise ValueError(f"Mode {mode} is not supported for DSPy based code generation.")

    all_results = []
    if batch_size is not None:
        for i in tqdm(range(0, len(batch_inputs), batch_size), desc="Code generation batch"):
            batch_call = batch_inputs[i:i+batch_size]
            results = batch_call_dspy_module(batch_call, codegen)
            all_results.extend(results)
    else:
        all_results = batch_call_dspy_module(batch_inputs, codegen)

    # parse all the results
    all_responses = []
    for output in all_results:
        try:
            output_code = output["output_code"]
            output_code = extract_code(output_code)
        except:
            if output is None:
                output_code = ""
            elif isinstance(output, dict):
                output_code = output.get("output_code", "")
            else:
                output_code = output
        
        all_responses.append(
            {"output": output_code}
            )
    return all_responses
