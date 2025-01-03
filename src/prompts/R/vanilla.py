PROMPT = """
Write R code to answer the user's request:
{question}

Dataset schema:
{data}

Return directly with the generated R code wrapped by <code> ... </code> tags, e.g.:

<code>
... your code here ...
</code>
"""