"""
AgentMD Agent for Clinical Risk Prediction.

AgentMD is an LLM-based autonomous agent for clinical risk prediction using
a large-scale toolkit of clinical calculators (RiskCalcs).

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

The agent implements a two-step workflow (matching the original paper):
1. Tool Selection: Retrieve relevant calculators and select the most appropriate one
2. Tool Computation: Apply the selected calculator to answer the clinical question
"""

import re
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.tools.risk_calculators import get_riskcalcs
from biodsa.sandbox.execution import ExecutionResults


# Note: torch, transformers, faiss are imported lazily when use_embedding=True
# This avoids loading heavy dependencies when using BM25 fallback


class BM25Retriever:
    """
    Simple BM25 retriever for text matching.
    Used as fallback when embedding models are not available.
    """
    
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 retriever.
        
        Args:
            documents: List of documents to index
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        
        # Tokenize documents
        self.doc_tokens = [self._tokenize(doc) for doc in documents]
        
        # Calculate document lengths and average
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_length = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0
        
        # Build inverted index and document frequencies
        self.doc_freqs = {}  # term -> number of documents containing term
        self.inverted_index = {}  # term -> {doc_id: term_freq}
        
        for doc_id, tokens in enumerate(self.doc_tokens):
            term_freqs = {}
            for token in tokens:
                term_freqs[token] = term_freqs.get(token, 0) + 1
            
            for term, freq in term_freqs.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                    self.doc_freqs[term] = 0
                self.inverted_index[term][doc_id] = freq
                self.doc_freqs[term] += 1
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
        import re
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        return tokens
    
    def _idf(self, term: str) -> float:
        """Calculate inverse document frequency for a term."""
        import math
        doc_freq = self.doc_freqs.get(term, 0)
        if doc_freq == 0:
            return 0
        return math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def score(self, query: str, doc_id: int) -> float:
        """Calculate BM25 score for a query against a document."""
        query_tokens = self._tokenize(query)
        doc_length = self.doc_lengths[doc_id]
        
        score = 0.0
        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            if doc_id not in self.inverted_index[term]:
                continue
            
            tf = self.inverted_index[term][doc_id]
            idf = self._idf(term)
            
            # BM25 scoring formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            score += idf * numerator / denominator
        
        return score
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Retrieve top-k documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_id, score) tuples sorted by score descending
        """
        scores = []
        for doc_id in range(self.doc_count):
            score = self.score(query, doc_id)
            if score > 0:
                scores.append((doc_id, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class AgentMD(BaseAgent):
    """
    AgentMD Agent for clinical risk prediction using clinical calculators.
    
    This agent implements the two-step AgentMD workflow:
    1. Tool Selection: Retrieve and select appropriate clinical calculators
    2. Tool Computation: Execute calculations with iterative code generation
    
    Example usage:
    ```python
    agent = AgentMD(
        model_name="gpt-4o",
        api_type="azure",
        api_key="your-api-key",
        endpoint="your-endpoint"
    )
    
    patient_note = '''
    65-year-old male with chest pain. History of hypertension and diabetes.
    ECG shows ST depression in leads V4-V6. Troponin elevated at 0.08 ng/mL.
    '''
    
    results = agent.go(patient_note)
    print(results.final_response)
    ```
    """
    
    name = "agentmd"
    
    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str,
        container_id: str = None,
        use_embedding: bool = False,
        top_k_retrieval: int = 10,
        max_computation_rounds: int = 20,
        **kwargs
    ):
        """
        Initialize the AgentMD agent.
        
        Args:
            model_name: Name of the LLM model to use (e.g., 'gpt-4o', 'gpt-4')
            api_type: API provider type (openai, azure)
            api_key: API key for the provider
            endpoint: API endpoint
            container_id: Optional Docker container ID (not used by AgentMD)
            use_embedding: Whether to use MedCPT embeddings for retrieval. 
                          If False (default), uses BM25 which doesn't require torch/transformers.
                          If True, requires: torch, transformers, faiss-cpu
            top_k_retrieval: Number of tools to retrieve for selection
            max_computation_rounds: Maximum rounds for tool computation conversation
            **kwargs: Additional arguments
        """
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
        )
        
        self.use_embedding = use_embedding
        self.top_k_retrieval = top_k_retrieval
        self.max_computation_rounds = max_computation_rounds
        
        # Lazy-loaded components
        self._riskcalcs = None
        self._retrieval_index = None
        self._pmids = None
        self._query_encoder = None
        self._article_encoder = None
        self._tokenizer = None
        self._torch = None  # Lazy-loaded torch module
    
    def _load_riskcalcs(self) -> Dict[str, Any]:
        """Lazy load the RiskCalcs dataset."""
        if self._riskcalcs is None:
            self._riskcalcs = get_riskcalcs()
            print(f"Loaded {len(self._riskcalcs)} clinical calculators")
        return self._riskcalcs
    
    def _load_retrieval_models(self):
        """Load MedCPT models for retrieval (lazy import of torch/transformers)."""
        if not self.use_embedding:
            return
        
        if self._query_encoder is None:
            # Lazy import of heavy dependencies
            try:
                import torch
                from transformers import AutoModel, AutoTokenizer
            except ImportError as e:
                raise ImportError(
                    "MedCPT embedding requires torch and transformers. "
                    "Install with: pip install torch transformers faiss-cpu\n"
                    "Or set use_embedding=False to use BM25 retrieval."
                ) from e
            
            print("Loading MedCPT retrieval models...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self._query_encoder = AutoModel.from_pretrained(
                "ncbi/MedCPT-Query-Encoder"
            ).to(device)
            self._article_encoder = AutoModel.from_pretrained(
                "ncbi/MedCPT-Article-Encoder"
            ).to(device)
            self._tokenizer = AutoTokenizer.from_pretrained(
                "ncbi/MedCPT-Query-Encoder"
            )
            
            # Store torch module reference for later use
            self._torch = torch
            
            print(f"MedCPT models loaded on {device}")
    
    def _build_retrieval_index(self) -> Tuple[Any, List[str]]:
        """Build retrieval index (FAISS for MedCPT, BM25 for fallback)."""
        if self._retrieval_index is not None:
            return self._retrieval_index, self._pmids
        
        riskcalcs = self._load_riskcalcs()
        pmids = list(riskcalcs.keys())
        
        # Build tool text representations
        tool_texts = []
        for pmid in pmids:
            calc = riskcalcs[pmid]
            title = calc.get("title", "").strip()
            purpose = calc.get("purpose", "").strip()
            specialty = calc.get("specialty", "").strip()
            tool_texts.append(f"{title} {purpose} {specialty}")
        
        if self.use_embedding:
            self._load_retrieval_models()
            
            # Lazy import faiss
            try:
                import faiss
            except ImportError as e:
                raise ImportError(
                    "FAISS is required for embedding-based retrieval. "
                    "Install with: pip install faiss-cpu\n"
                    "Or set use_embedding=False to use BM25 retrieval."
                ) from e
            
            # Encode all tools for FAISS
            tool_pairs = []
            for pmid in pmids:
                calc = riskcalcs[pmid]
                title = calc.get("title", "").strip()
                purpose = calc.get("purpose", "").strip()
                tool_pairs.append([title, purpose])
            
            tool_embeddings = self._encode_tools(tool_pairs)
            
            # Build FAISS index
            self._retrieval_index = faiss.IndexFlatIP(768)
            self._retrieval_index.add(tool_embeddings.astype(np.float32))
            print("Built FAISS index with MedCPT embeddings")
        else:
            # Fallback: Build BM25 index
            print("Building BM25 index for retrieval...")
            self._retrieval_index = BM25Retriever(tool_texts)
            print(f"Built BM25 index with {len(tool_texts)} documents")
        
        self._pmids = pmids
        return self._retrieval_index, pmids
    
    def _encode_tools(self, tool_texts: List[List[str]], batch_size: int = 16) -> np.ndarray:
        """Encode tools using MedCPT Article Encoder."""
        torch = self._torch  # Use lazily loaded torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        embeddings = []
        
        with torch.no_grad():
            for i in range(0, len(tool_texts), batch_size):
                batch = tool_texts[i:i + batch_size]
                encoded = self._tokenizer(
                    batch,
                    truncation=True,
                    padding=True,
                    return_tensors="pt",
                    max_length=512,
                )
                encoded = {k: v.to(device) for k, v in encoded.items()}
                
                output = self._article_encoder(**encoded)
                embeddings.append(output.last_hidden_state[:, 0, :].cpu().numpy())
        
        return np.vstack(embeddings)
    
    def _encode_query(self, query: str) -> np.ndarray:
        """Encode a query using MedCPT Query Encoder."""
        torch = self._torch  # Use lazily loaded torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        with torch.no_grad():
            encoded = self._tokenizer(
                [query],
                truncation=True,
                padding=True,
                return_tensors="pt",
                max_length=512,
            )
            encoded = {k: v.to(device) for k, v in encoded.items()}
            
            output = self._query_encoder(**encoded)
            embedding = output.last_hidden_state[:, 0, :].cpu().numpy()
        
        return embedding
    
    def _retrieve_tools(self, query: str, top_k: int = None) -> List[str]:
        """Retrieve relevant tools for a query using MedCPT or BM25 fallback."""
        if top_k is None:
            top_k = self.top_k_retrieval
        
        index, pmids = self._build_retrieval_index()
        
        if self.use_embedding:
            # Use MedCPT + FAISS
            query_embedding = self._encode_query(query)
            scores, indices = index.search(query_embedding.astype(np.float32), top_k)
            
            retrieved_pmids = [pmids[idx] for idx in indices[0]]
            return retrieved_pmids
        else:
            # Use BM25 retrieval
            results = index.retrieve(query, top_k=top_k)
            retrieved_pmids = [pmids[doc_id] for doc_id, score in results]
            
            # If BM25 returns fewer results than requested, pad with random tools
            if len(retrieved_pmids) < top_k:
                remaining = [p for p in pmids if p not in retrieved_pmids]
                retrieved_pmids.extend(remaining[:top_k - len(retrieved_pmids)])
            
            return retrieved_pmids
    
    def _step1_tool_selection(
        self,
        question: str,
        verbose: bool = True
    ) -> str:
        """
        Step 1: Tool Retrieval and Selection.
        
        Retrieves relevant calculators and uses LLM to select the best one.
        
        Args:
            question: The clinical question or patient description
            verbose: Whether to print progress
            
        Returns:
            The PMID of the selected tool
        """
        if verbose:
            print("=" * 60)
            print("STEP 1: Tool Retrieval and Selection")
            print("=" * 60)
        
        riskcalcs = self._load_riskcalcs()
        
        # Retrieve relevant tools
        retrieved_pmids = self._retrieve_tools(question)
        
        if verbose:
            print(f"Retrieved {len(retrieved_pmids)} candidate tools")
        
        # Build selection prompt
        prompt = "Please choose the most appropriate tool from the listed ones to solve the question below:\n"
        prompt += question + "\n\n"
        
        for pmid in retrieved_pmids:
            calc = riskcalcs[pmid]
            title = calc.get("title", "").strip()
            purpose = calc.get("purpose", "").strip()
            prompt += f"Tool ID: {pmid}; Title: {title}; Purpose: {purpose}\n"
        
        prompt += "\nPlease copy the most appropriate tool ID: "
        
        # Get LLM selection
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=1.0,
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = run_with_retry(llm.invoke, arg=messages)
        answer = response.content
        
        if verbose:
            print(f"LLM Selection Response: {answer[:200]}...")
        
        # Extract tool ID from response
        if "Tool ID: " in answer:
            selected_pmid = answer.split("Tool ID: ")[-1][:8]
        else:
            # Try to find any 8-digit number (PMID format)
            match = re.search(r'\b(\d{8})\b', answer)
            if match:
                selected_pmid = match.group(1)
            else:
                # Fallback to first retrieved tool
                selected_pmid = retrieved_pmids[0]
        
        if verbose:
            print(f"Selected Tool: {selected_pmid}")
            if selected_pmid in riskcalcs:
                print(f"Title: {riskcalcs[selected_pmid].get('title', '').strip()}")
        
        return selected_pmid
    
    @staticmethod
    def _extract_python_code(text: str) -> str:
        """Extract Python code blocks from text."""
        pattern = r"```python\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return "\n".join(matches)
    
    def _format_calculator(self, calc: Dict[str, Any]) -> str:
        """Format calculator data for the prompt."""
        calc_text = ""
        for key, value in calc.items():
            if key == "example":
                continue
            calc_text += key.upper() + "\n"
            calc_text += str(value) + "\n\n"
        return calc_text
    
    def _step2_tool_computation(
        self,
        question: str,
        tool_pmid: str,
        verbose: bool = True
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Step 2: Tool Computation.
        
        Applies the selected calculator through iterative code execution using
        the ExecuteCodeTool for proper tool-based execution.
        
        Args:
            question: The clinical question
            tool_pmid: PMID of the selected calculator
            verbose: Whether to print progress
            
        Returns:
            Tuple of (answer, message_history)
        """
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
        from biodsa.agents.agentmd.tools import ExecuteCodeTool
        
        if verbose:
            print("\n" + "=" * 60)
            print("STEP 2: Tool Computation")
            print("=" * 60)
        
        riskcalcs = self._load_riskcalcs()
        
        if tool_pmid not in riskcalcs:
            return f"Error: Tool {tool_pmid} not found", []
        
        calc = riskcalcs[tool_pmid]
        calc_text = self._format_calculator(calc)
        
        if verbose:
            print(f"Applying calculator: {calc.get('title', '').strip()}")
        
        # Extract any code from the calculator for context (will be prepended to executed code)
        calculator_code = self._extract_python_code(calc_text)
        
        # System prompt - instructs LLM to use the execute_calculation tool
        system = """You are a helpful clinical assistant. Your task is to apply a medical calculator to solve a clinical question.

You have access to the `execute_calculation` tool which can run Python code. Use this tool to:
1. Define and call the calculator function with the patient's values
2. Print the results using print()

The calculator function is provided below. Extract the relevant values from the patient case and call the function.

IMPORTANT: 
- Use the execute_calculation tool to run your Python code
- After getting the execution results, provide your final answer starting with "Answer: "
- Choose the closest answer if there is no exact match"""
        
        # Initial user prompt
        prompt = f"""Here is the calculator:
{calc_text}

Here is the clinical question:
{question}

Please use the execute_calculation tool to apply this calculator. Include the calculator function definition in your code, extract the patient values from the question, and call the function with those values. Use print() to show the results."""
        
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ]
        
        # Get tools and bind to LLM
        tools = [ExecuteCodeTool()]
        
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=1.0,
        )
        llm_with_tools = llm.bind_tools(tools)
        
        # Iterative computation loop
        for round_num in range(1, self.max_computation_rounds + 1):
            if verbose:
                print(f"\n--- Round {round_num} ---")
            
            response = run_with_retry(llm_with_tools.invoke, arg=messages)
            messages.append(response)
            
            message_content = response.content or ""
            
            # Check if we have an answer in the response content
            if "Answer:" in message_content:
                answer = message_content.split("Answer:")[-1].strip()
                if verbose:
                    print(f"[FINAL ANSWER]: {answer}")
                return answer, self._format_messages_to_dict(messages)
            
            # Check if there are tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    if verbose:
                        print(f"[TOOL CALL]: {tool_name}")
                        if "code" in tool_args:
                            code_preview = tool_args["code"][:300] + "..." if len(tool_args["code"]) > 300 else tool_args["code"]
                            print(f"[CODE]:\n{code_preview}")
                    
                    # Execute the tool
                    tool = tools[0]  # ExecuteCodeTool
                    try:
                        # Prepend calculator code to the user's code
                        full_code = calculator_code + "\n\n" + tool_args.get("code", "")
                        tool_result = tool._run(code=full_code)
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"
                    
                    if verbose:
                        print(f"[TOOL RESULT]:\n{tool_result}")
                    
                    # Add tool result as ToolMessage
                    messages.append(ToolMessage(
                        content=tool_result,
                        name=tool_name,
                        tool_call_id=tool_call_id
                    ))
            else:
                # No tool calls and no answer - prompt to provide answer or use tool
                if verbose:
                    reasoning_preview = message_content[:300] + "..." if len(message_content) > 300 else message_content
                    print(f"[LLM RESPONSE]: {reasoning_preview}")
                
                messages.append(HumanMessage(
                    content='Please use the execute_calculation tool to run the Python code, or if you have the result, provide your final answer starting with "Answer: "'
                ))
        
        # Max rounds reached
        return "Failed: Maximum rounds reached", self._format_messages_to_dict(messages)
    
    def _format_messages_to_dict(self, messages) -> List[Dict[str, str]]:
        """Convert LangChain messages to dict format."""
        result = []
        for msg in messages:
            if hasattr(msg, 'content'):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                role = getattr(msg, 'type', 'unknown')
                result.append({"role": role, "content": content[:1000] if len(content) > 1000 else content})
        return result
    
    def go(
        self,
        patient_note: str,
        query: Optional[str] = None,
        tool_pmid: Optional[str] = None,
        verbose: bool = True
    ) -> ExecutionResults:
        """
        Execute the AgentMD workflow on a patient note.
        
        Args:
            patient_note: The patient's clinical note or question
            query: Optional additional query (will be appended to patient_note)
            tool_pmid: Optional specific tool to use (skips Step 1 if provided)
            verbose: Whether to print progress
            
        Returns:
            ExecutionResults with the final response
        """
        # Combine patient note and query
        question = patient_note
        if query:
            question += f"\n\n{query}"
        
        if verbose:
            print("=" * 70)
            print("AgentMD: Clinical Risk Prediction Agent")
            print("=" * 70)
            print(f"\nQuestion:\n{question[:500]}..." if len(question) > 500 else f"\nQuestion:\n{question}")
            print()
        
        # Step 1: Tool Selection (skip if tool_pmid provided)
        if tool_pmid is None:
            tool_pmid = self._step1_tool_selection(question, verbose=verbose)
        elif verbose:
            print(f"Using provided tool: {tool_pmid}")
        
        # Step 2: Tool Computation
        answer, messages = self._step2_tool_computation(question, tool_pmid, verbose=verbose)
        
        if verbose:
            print("\n" + "=" * 60)
            print("FINAL ANSWER")
            print("=" * 60)
            print(answer)
        
        # Format message history
        message_history = []
        for msg in messages:
            message_history.append({
                "role": msg["role"],
                "content": msg["content"][:1000] if len(msg["content"]) > 1000 else msg["content"]
            })
        
        return ExecutionResults(
            sandbox=None,
            message_history=message_history,
            code_execution_results=[],
            final_response=answer
        )
    
    def evaluate_riskqa(
        self,
        question: str,
        choices: Dict[str, str],
        oracle_pmid: Optional[str] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate on RiskQA benchmark.
        
        Args:
            question: The RiskQA question
            choices: Answer choices {"A": "...", "B": "...", ...}
            oracle_pmid: If provided, use this tool (oracle mode)
            verbose: Whether to print progress
            
        Returns:
            Dict with 'answer', 'reasoning', 'tool_pmid', 'messages'
        """
        # Format question with choices
        formatted_question = question + "\n\n"
        for letter, choice in choices.items():
            formatted_question += f"{letter}. {choice}\n"
        
        # Run the agent
        results = self.go(
            patient_note=formatted_question,
            tool_pmid=oracle_pmid,
            verbose=verbose
        )
        
        # Extract letter answer
        answer_text = results.final_response
        answer_letter = ""
        
        # Try to extract single letter answer
        for letter in choices.keys():
            if answer_text.strip().upper().startswith(letter):
                answer_letter = letter
                break
            if f"Answer: {letter}" in answer_text or f"answer is {letter}" in answer_text.lower():
                answer_letter = letter
                break
        
        if not answer_letter:
            # Look for any choice letter in the response
            for letter in choices.keys():
                if letter in answer_text:
                    answer_letter = letter
                    break
        
        return {
            "answer": answer_letter,
            "reasoning": answer_text,
            "tool_pmid": oracle_pmid,
            "messages": results.message_history
        }
