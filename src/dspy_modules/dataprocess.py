"""Build the dataset processing pipeline using few-shot learning and dspy.
"""
import dspy
from bs4 import BeautifulSoup

def extract_score(_raw_output: str) -> str:
    # Using 'html.parser' to parse the content
    try:
        soup = BeautifulSoup(_raw_output, "html.parser")
        _raw_output = soup.find("score").text
        _raw_output = int(_raw_output)
    except:
        _raw_output = None
    return _raw_output

class Assess(dspy.Signature):
    """Evaluate the correctness of the output instruction referring to the reference instruction. Return the quality score.
Note: The instruction is meant to provide a high-level guidance to resolve the user's question. 
Hence, the output instruction should not contain the direct code solutions grabbed from the reference code answers. If it happens,
rate the instruction as 0.
    """
    output_instruction = dspy.InputField(desc="The generated instruction.")
    reference_instruction = dspy.InputField()
    assessment_question = dspy.InputField()
    quality_score = dspy.OutputField(desc="Score ranging from 0 to 5, the higher the better. Return the score directly in the HTML format wrapped by <score> and </score>, e.g., <score>5</score>.")

def check_instruction_quality(example, output, trace=None, llm="gpt-4o"):
    """Check the quality of the instruction.
    """
    # check the instruction length
    output_instruction = output["instruction"]
    llm = dspy.OpenAI(model=llm, max_tokens=256)
    with dspy.context(lm=llm):
        assessment_question = "How good is the instruction? Return the score directly in the HTML format wrapped by <score> and </score>, e.g., <score>4</score>."
        results = dspy.Predict(Assess)(
            output_instruction=output_instruction, 
            reference_instruction=example["instruction"], 
            assessment_question=assessment_question,
            )
    score = extract_score(results.quality_score)
    indicator = score/5 if score is not None else 0
    return indicator


class TaskInstructionGeneration(dspy.Signature):
    """Augment the raw user question with a more detailed instruction. The instruction should NOT contain the direct code solutions grabbed from the reference code answers.
    """
    question = dspy.InputField(desc="Raw user question.")
    reference_answer = dspy.InputField(desc="The reference answer to the user question.")
    instruction = dspy.OutputField(desc="The generated task instructions.")

class DSPyInstructionGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.Predict(signature=TaskInstructionGeneration)
    
    def forward(self, question, reference_answer, temperature=0.7):
        """Args:

        question (str): the raw user question
        reference_answer (str): the reference answer to the user question
        """
        response = self.prog(question=question, 
                                reference_answer=reference_answer,
                                **{
                                    "temperature": temperature
                                }
                                )

        instruction = response.instruction

        return {
            "instruction": instruction,
        }


class TaskQuestionGeneration(dspy.Signature):
    """Generate a question based on the reference answer and the unit test cases.
    """
    question = dspy.OutputField(desc="question.")
    reference_answer = dspy.InputField(desc="The coding answer.")
    test_case = dspy.InputField(desc="The unit test cases.")

class DSPyQuestionGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.Predict(signature=TaskQuestionGeneration)
    
    def forward(self, test_case, reference_answer, temperature=0.7):
        """Args:

        test_case (str): the raw user question
        reference_answer (str): the reference answer to the user question
        """
        response = self.prog(test_case=test_case,
                                reference_answer=reference_answer,
                                **{
                                    "temperature": temperature
                                }
                                )

        question = response.question

        return {
            "question": question,
        }

def check_question_quality(example, output, trace=None):
    """Check the quality of the question. using BLEU score.
    """
    import evaluate
    bleu = evaluate.load("bleu")
    results = bleu.compute(
        predictions = [output["question"]],
        references = [example["question"]],
    )
    score = results["bleu"]
    return score
