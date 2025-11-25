# DSWizard Agent

DSWizard (Data Science Wizard) is a two-phase agent designed for reliable biomedical data analysis. It operates by first creating a detailed analysis plan in natural language, then converting that plan into executable Python code.

## Overview

DSWizard addresses the challenge of making large language models more reliable for data science tasks by decomposing the problem into two specialized phases:

1. **Planning Phase**: The agent explores available datasets and creates a structured, step-by-step analysis plan in natural language
2. **Implementation Phase**: The agent converts the analysis plan into correct and complete Python code

This two-phase approach improves reliability by:
- Separating high-level reasoning from low-level coding
- Allowing dataset exploration before committing to an analysis strategy  
- Creating explicit plans that can be reviewed and verified
- Including quality control steps to assess result quality

## Usage

### Basic Example

```python
import os
from biodsa.agents import DSWizardAgent

# Initialize the agent
agent = DSWizardAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Register a dataset for analysis
agent.register_workspace("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")

# Execute a data science task
results = agent.go("Make a clustering of the patients based on their genomic mutation data to maximize the separation of the prognostic survival outcomes.")

# View results
print(results)

# Download generated artifacts (figures, tables, etc.)
results.download_artifacts(output_dir="output_artifacts")

# Generate structured PDF report
results.to_pdf(output_dir="reports")

# Clean up
agent.clear_workspace()
```

### Azure OpenAI Example

```python
import os
from biodsa.agents import DSWizardAgent

agent = DSWizardAgent(
    model_name="gpt-5",
    small_model_name="gpt-5-mini",  # Optional smaller model for plan generation
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
)

agent.register_workspace("./path/to/your/dataset")
results = agent.go("Your analysis question here")
```

### Anthropic Claude Example

```python
import os
from biodsa.agents import DSWizardAgent

agent = DSWizardAgent(
    model_name="claude-3-5-sonnet-20241022",
    api_type="anthropic",
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

agent.register_workspace("./path/to/your/dataset")
results = agent.go("Your analysis question here")
```

## How It Works

### Phase 1: Planning

The planning agent:
1. Explores the dataset by executing code to understand:
   - Table names and schemas
   - Column names and data types
   - Value ranges and distributions
   - Available Python packages
2. Creates a structured analysis plan that includes:
   - Step-by-step analysis procedures
   - Specific table/column references
   - Quality control steps
3. Iterates until confident the plan is complete and unambiguous

### Phase 2: Implementation

The coding agent:
1. Reviews the analysis plan and checks feasibility of each step
2. Performs additional exploration if any step needs clarification
3. Generates complete Python code implementing all plan steps
4. Executes the code and returns results

## Configuration Options

### Model Selection

```python
agent = DSWizardAgent(
    model_name="gpt-5",              # Main model for both phases
    small_model_name="gpt-5-mini",   # Optional: smaller model for plan content generation
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY")
)
```

The `small_model_name` parameter allows using a smaller, faster model for the analysis plan generation step to reduce costs while maintaining quality.

### Sandbox Configuration

By default, DSWizard uses the `biodsa-sandbox-py` Docker container for code execution. You can customize this:

```python
agent = DSWizardAgent(
    model_name="gpt-5",
    api_type="openai", 
    api_key=os.environ.get("OPENAI_API_KEY"),
    container_id="your-custom-container-id"  # Use specific container
)
```

## Working with Results

The `ExecutionResults` object provides comprehensive access to all analysis outputs:

```python
results = agent.go("Your analysis question")

# Access execution components
print(f"Final answer: {results.final_response}")
print(f"Code executions: {len(results.code_execution_results)}")
print(f"Message history: {len(results.message_history)}")

# Export results
results.to_json("results.json")
results.to_pdf(output_dir="reports")  # PDF with embedded figures
artifact_files = results.download_artifacts(output_dir="outputs")

# View resource usage
for execution in results.code_execution_results:
    print(f"Runtime: {execution.running_time}s")
    print(f"Peak memory: {execution.peak_memory}MB")
```

## Key Features

- **Dataset Exploration**: Automatically explores datasets before planning
- **Structured Planning**: Creates explicit, verifiable analysis plans
- **Quality Control**: Includes steps to assess analysis quality
- **Resource Monitoring**: Tracks execution time and memory usage
- **Artifact Management**: Automatically saves figures, tables, and outputs
- **PDF Reports**: Generates professional reports with embedded visualizations
- **Sandboxed Execution**: Safe, isolated code execution in Docker containers

## Best Practices

1. **Be Specific**: Provide clear, specific analysis questions
   ```python
   # Good
   results = agent.go("Compare survival outcomes between TP53 mutant and wild-type patients using Kaplan-Meier analysis")
   
   # Less ideal  
   results = agent.go("Analyze the data")
   ```

2. **Register Complete Workspaces**: Ensure all necessary data files are in the registered workspace directory

3. **Monitor Resources**: Check execution results for memory and runtime metrics to optimize performance

4. **Review Plans**: The agent creates explicit analysis plans - you can examine these in the message history

5. **Clean Up**: Always call `agent.clear_workspace()` when done to stop sandbox containers

## Requirements

- Python 3.12+
- Docker (for sandboxed execution)
- Required Python packages (see main README)
- API credentials for your chosen LLM provider

## Citation

If you use DSWizard in your research, please cite:

```bibtex
@article{wang2025biodsa1k,
  title={BioDSA-1K: Benchmarking Data Science Agents for Biomedical Research},
  author={Wang, Zifeng and Danek, Benjamin and Sun, Jimeng},
  journal={arXiv preprint arXiv:2505.16100},
  year={2025}
}

@article{wang2024llm,
  title={Can Large Language Models Replace Data Scientists in Biomedical Research?},
  author={Wang, Zifeng and Danek, Benjamin and Yang, Ziwei and Chen, Zheng and Sun, Jimeng},
  journal={arXiv preprint arXiv:2410.21591},
  year={2024}
}
```

## Support

For issues, questions, or contributions, please refer to the main BioDSA repository.
