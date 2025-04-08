# Introduction

This repository contains the code for the paper ["Can Large Language Models Replace Data Scientists in Biomedical Research?"](https://arxiv.org/abs/2410.21591).

# Prepare the environment

1. Configure the pipenv virtual environment, by taking `pipenv shell` to get into the virtual environment.

2. Prepare the API key to access different LLMs, and put them in the base director of the code repository.
- OpenAI: `openai.key`
- Azure OpenAI: `azure_openai_credentials.json`
- AWS Bedrock for Claude models: `aws_credentials.json`
- Google VertexAI for Gemini: `vertexai.json`

The example credential files can be found in `example_credentials/`.

# Prepare the coding tasks

1. We have preprocessed python and R coding tasks in `benchmark_datasets/python/coding_tasks.csv` and in `benchmark_datasets/R/coding_tasks.csv`, respectively. Each row has a coding question, reference answers, testing cases, and the string dataset schema description.

2. If you need to process for other coding questions, check `benchmark_datasets/preprocess_python_tasks.py` and `benchmark_datasets/preprocess_R_tasks.py` for examples.

3. If you need to execute the generated Python and R code on the patient data. Go `sandbox/docker_container`, and execute `build_sandbox.sh` to create the docker container. Also, you need to download the raw patient-level data for [Python](https://drive.google.com/drive/folders/1M_ex6EUdYhnEly84dVX_Pb_ScVN_yjm_?usp=sharing) and [R](https://drive.google.com/drive/folders/18dv6l1UHkiCnpLR-eGgY3g8zf9xk79zI?usp=sharing) tasks. Put them under `benchmark_datasets/python` and `benchmark_datasets/R`, respectively. 


# Run code generation

`scripts/run_code_generation_python.py`, `scripts/run_code_generation_R.py` for python code and R code generation, respectively, the following adaptations are implemented:

- vanilla prompt
- manual prompt
- chain of thought prompt
- autoprompt (dependent on `dspy`)
- fewshot prompt (dependent on `dspy`)

# Run code improvement

`scripts/run_code_improvement_python.py` has the implementation to request LLM to self-reflect and improve the code.


# Execute the generated code

The generated code can be executed and see the execution results if
- the docker sandbox has been set up
- the raw patient-level data has been prepared

See `scripts/run_code_execution.py` for the implementations. 


# Reference

```bibtex
@misc{wang2024largelanguagemodelsreplace,
      title={Can Large Language Models Replace Data Scientists in Biomedical Research?}, 
      author={Zifeng Wang and Benjamin Danek and Ziwei Yang and Zheng Chen and Jimeng Sun},
      year={2024},
      eprint={2410.21591},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2410.21591}, 
}
```