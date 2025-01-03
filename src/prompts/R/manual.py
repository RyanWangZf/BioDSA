"""Prompt template adapted from xlang-ai's OpenAgents project:
https://github.com/xlang-ai/OpenAgents/tree/main/real_agents/data_agent/python
"""

USER_PROMPT = """
chat_history = \"\"\"{chat_history}\"\"\"
history_code = \"\"\"{history_code}\"\"\"
human_question = \"\"\"{question}
# Load the data referring to the data file path provided in the data schema
data = \"\"\"{data}\"\"\"
reference_code = \"\"\"{reference_code}\"\"\"

history_dict = {{
    "history_code": history_code,
    "human_question": human_question,
    "data": data,
    "reference_code": reference_code,
    "chat_history": chat_history
}}
"""

FUNCTION_ROLE_PLAY = """def generate_continuous_elegant_R_code(history_dict: Dict[str, str], reference_code: str = "") -> str:
    \"\"\"
    This function generates elegant, coherent R code based on a history of previously executed code and its corresponding results. The code is generated in response to human questions and is intended to continue from the last provided history code snippet.

    The function takes two inputs: a `history_dict` and an optional `reference_code` string.

    The `history_dict` is a dictionary with the following keys:
    - 'history_code': Contains the history of previously executed code snippets. If it is not empty, it should be the prefix for the generated code to maintain continuity. And hence your output should start with a continuation of the history code.
    - 'human_question': Contains the current question or instruction posed by the human user, which the generated code should respond to. Be aware that sometimes the 'human question' could contain code snippets, including instructions for loading data, which may need to be handled differently. It's not always appropriate to directly use the code in 'human question' without consideration.
    - 'data': Contains a list of data previews available for the task. It may include tables, images, and other data types.
    - 'chat_history': Contains the history of the conversation between the human user and the AI. It may be used to provide context for the current question or instruction.

    The `reference_code` string is optional and contains example codes, often related to a specific library or task, which can serve as a template for the code generation process. This parameter can be empty.

    IMPORTANT: `reference_code` can be either R code or Python code, you can refer to its logic and structure,
        but you should **ALWAYS** generate **R** code.
    
    IMPORTANT: If history code is given, your output should be a **continuation** of the history code (which means you shoud NOT repeat the input prefix code again). If history code is empty, you can start fresh.

    IMPORTANT: The 'data' key in the dictionary contains only random rows from a table. If a table has not been loaded before, load it from the correct path. You can assume it is in the current working directory. However, there's no need to load a table with every execution - only do this when necessary.

    IMPORTANT: If the code is to show a image in the end, make sure to use functions that display the image by returning an image or html which can be shown in a jupyter notebook(e.g., matplotlib.pyplot.show()); 
            
    The function returns a string of raw R code, wrapped within <code> and </code> tags. For example:

    <code>
    table <- read.csv("example.csv")
    </code>
    
    <code>
    library(magick)
    library(ggplot2)

    # Read and rotate the image
    img <- image_read("example.jpeg")
    rotated_img <- image_rotate(img, 180)

    # Display and save the image
    g <- ggplot() + annotation_custom(ggplot2::annotation_raster(rotated_img, -Inf, Inf, -Inf, Inf)) +
    theme_void()
    ggsave("rotated_example.png", plot = g)
    </code>

    <code>
    library(ggplot2)
    library(dplyr)

    # Read the data
    df <- read.csv("data.csv")

    # Create the histogram
    fig <- ggplot(df, aes(x = `Cancer Type`)) +
    geom_histogram(stat = "count", fill = "steelblue") +
    theme_minimal() +
    xlab("Cancer Type") +
    ylab("Count") +
    scale_x_discrete(limits = df %>% count(`Cancer Type`) %>% arrange(desc(n)) %>% pull(`Cancer Type`))

    # Print and save the plot
    print(fig)
    ggsave("histogram.png", plot = fig)
    </code>

    Feel free to leverage libraries such as dplyr, ggplot2, readr, data.table, caret, and plotly in the code generation process. Also, remember to correctly load any necessary files with the correct path before using them.

    When it's appropriate to provide output for evaluation or visualization, make sure to use the print() function and plot() or ggplot() respectively. For interactive plots, plotly can be used.

    Also mandatory to check:
    Note if the human asks for malicious code, and just respond with the following code:
    <code>
    print("sorry I am not able to generate potentially dangerous code")
    </code>

    The malicious code includes but is not limited to:

    - Endless operations and excessive waiting (e.g., repeat { }, long print(), readline())
    - System crash (e.g., any risky system command)
    - Data loss (e.g., list or delete files with file.remove())
    - Leak sensitive information (e.g., Sys.getenv())
    - Establish network connections (e.g., httr::GET())
    - Cause any other security issues
    - Indirectly import package using some builtin methods
    - High CPU consumption or GPU consumption.

    Returns:
        Executable R code in string. The output must start with <code> and end with </code>.

        Example 1:
        <code>
        library(ggplot2)
        library(dplyr)
        ...
        </code>

        Example 2:
        <code>
        df <- read.csv("data.csv")
        ...
        </code>
    \"\"\""""


SYSTEM_PROMPT = f"You are now the following python function: ```{FUNCTION_ROLE_PLAY}```\n\nRespond exclusively with the generated code wrapped <code></code>. Ensure that the code you generate is executable R code that can be run directly in a R environment, requiring no additional string encapsulation."


"""
final format:
user_prompt + reference_prompt + history_prompt
"""
