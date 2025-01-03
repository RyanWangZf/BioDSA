"""Manage the memory of conversation history and context"""
import json
import json
import time

from typing import Any, Iterator, List, Dict

from .schema import (
    Message,
    ChatResponse,
    MessageObject,
    Dataframe,
    CodeSnippet,
)


def combine_chat_history(
    chat_history: List[Message],
    window_size: int = None,  # TODO: control the size of the chat history
) -> str:
    """Combine the chat history into a single string.
    """
    combined = []
    if len(chat_history) == 0:
        return ""

    for message in chat_history:
        add_fn = None
        if message.role in ["assistant"]:
            add_fn = _add_ai_message

        elif message.role in ["user"]:
            add_fn = _add_user_message

        elif message.role in ["system"]:
            def add_fn(x): return None

        if add_fn:
            # perform filtering and add to memory
            combined.append(add_fn(message))

        else:
            raise ValueError(
                f"Invalid message role: {message.role} ({message})")

    return "\n".join(combined)


def combine_dataframes(dataframes: List[Dataframe]) -> str:
    """Combine the schema of the input dataframes into a single string.
    """
    schema_list = []
    for df in dataframes:
        if df.data_schema is not None:
            schema_str = df.data_schema
            schema_str = f"""A Dataframe stored in `{df.path}`. Dataframe schema: {schema_str}"""
            schema_list.append(schema_str)
    if len(schema_list) == 0:
        return ""
    schema = "\n".join(schema_list)
    return schema


def combine_code_history(code_history: List[CodeSnippet]) -> str:
    """Combine the code history into a single string.
    """
    code_list = []
    if len(code_history) == 0:
        return ""

    for code in code_history:
        if isinstance(code, CodeSnippet):
            code_list.append(_add_code_snippet(code))
        else: # it is just string
            code_list.append(code)

    return "\n".join(code_list)


"""Utility functions for combining the chat history and dataframes into a single string
"""


def _add_ai_message(message: Message) -> str:
    _aggregate_ai_message_objects(message)
    content = message.content.message_objects[0].text
    return "AI:\t" + content


def _add_user_message(message: Message) -> str:
    content = message.content.message_objects[0].text
    return "User:\t" + content


def _aggregate_ai_message_objects(message: Message):
    text_list = []
    for message_object in message.content.message_objects:
        if (message_object.text is not None) and (message_object.text != ""):
            text_list.append(message_object.text)

    # aggregate the AI messages
    text_list_str = "".join(text_list)

    # replace the message objects with a single message object
    message.content.message_objects = [
        MessageObject(text=text_list_str, data_modality="messageString"),
    ]


def _add_code_snippet(code: CodeSnippet) -> str:
    # add the prefix
    line = "---"*10 + "\n```python\n"

    # add the code snippet id
    if code.doc_id is not None:
        line += f"# Code snippet ID: {code.doc_id}\n"

    # add the description of the code snippet
    desc = f"# Description: {code.desc}" if code.desc else ""

    # add the imported functions/variables
    imported = code.imported
    if imported is not None:
        if len(imported) > 0:
            imported = " | ".join(imported)
            imported = f"# Imported functions/variables: {imported}"
    else:
        imported = ""

    # combine the code snippet
    line += f"{desc}\n{imported}\n{code.code}\n```\n"
    return line