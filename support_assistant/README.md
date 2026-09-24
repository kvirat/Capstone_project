# RAG Pipeline Architecture

This project implements a simple retrieval-augmented generation (RAG) pipeline for a Zepto policy assistant. The main logic lives in the notebook at [ai_support_assistant.ipynb](ai_support_assistant.ipynb), and the end-to-end flow is: ingestion → embedding → retrieval → generation.

## 1) Ingestion

The ingestion stage starts with the policy text files in the project docs directory. Each policy document is read and split into sentence-like chunks by the function `chunk_docs(file_path, source_name)` in the notebook.

That function:
- opens the source text file,
- splits the text on periods,
- filters out very short fragments,
- returns a list of dictionaries like `{ "text": "...", "source": "Delivery Policy" }`.

The code then combines all per-document chunk lists into a single `all_chunks` list. This is the raw knowledge base that will be loaded into the vector store.

The ingestion step is not done by a separate app service; it is the notebook cell sequence that reads the docs, calls `chunk_docs`, and adds the chunks into ChromaDB.

## 2) Embedding

The embedding stage is handled by ChromaDB itself. The project creates a client and a collection named `Zepto_Document_corpus`:

- `chroma_client = chromadb.Client()`
- `collection = chroma_client.get_or_create_collection(name="Zepto_Document_corpus")`

Then each chunk is added with its text, ID, and source metadata:

- `documents.append(chunk["text"])`
- `ids.append(f"chunk_{i}")`
- `metadatas.append({"source": chunk["source"]})`
- `collection.add(documents=documents, ids=ids, metadatas=metadatas)`

This is the point where the text chunks become vector representations in the Chroma collection. In other words, the vector store is the embedding layer, and the stored metadata keeps track of the document/section source for later provenance.

## 3) Retrieval

The retrieval stage begins when the LangGraph workflow starts at `classify_intent`. This node inspects the user question and decides whether it is a policy question or a general question.

The routing logic is:
- `classify_intent(state)` decides the intent,
- `route_intent(state)` chooses which node to call next,
- if the intent is `policy_question`, the graph goes to `retrieve_and_answer`,
- if the intent is `general_question`, the graph goes to `direct_answer`.

The actual document lookup happens inside `retrieve_and_answer(state: AgentState)`. That node does:

- `results = collection.query(query_texts=[question], n_results=3)`
- pulls the top matching chunks from `Zepto_Document_corpus`
- captures both the chunk content and the corresponding `ids` and `metadatas`
- builds `context_list` entries containing `Source: ...` and the matching text

This produces the retrieved evidence used in the final answer and also records the chunk IDs that were used for the final `sources` field.

## 4) Generation

The generation stage is implemented in the answer nodes of the LangGraph graph.

For policy questions:
- `retrieve_and_answer(state)` is the generator node for grounded answers.
- It assembles the retrieved context and then either:
  - uses a mock canned response when `MOCK_LLM` is enabled, or
  - would call a real LLM using the `prompt_template` string in the optional real-LLM branch.

The prompt template is defined as `prompt_template`, and it instructs the model to answer using only the supplied policy context. The notebook includes placeholder code for a real LangChain/OpenAI call, but the default path uses the mock branch.

For general questions:
- `direct_answer(state)` handles non-policy queries.
- In default mock mode, it returns a fixed answer such as: "I can only answer questions about Zepto policies right now."
- In the optional real-LLM mode, it would call the LLM directly with a question-only prompt.

After the answer is produced, the final graph node `format_final_response(state)` converts the result into the `Response` Pydantic model with fields:
- `answer`
- `sources`
- `confidence`

That structured response is the final output of the pipeline.

## Data Flow Summary

A simple flow is:

```text
Policy docs in support_assistant/docs/
        |
        v
chunk_docs(file_path, source_name)
        |
        v
all_chunks -> ChromaDB collection "Zepto_Document_corpus"
        |
        v
classify_intent -> route_intent
        |
        +--> policy_question -> retrieve_and_answer
        |                           |
        |                           v
        |                    collection.query(...)
        |                           |
        |                           v
        |                     context + retrieved IDs
        |                           |
        |                           v
        |               prompt_template / mock generation
        |                           |
        |                           v
        |                 format_final_response
        |
        +--> general_question -> direct_answer
                                    |
                                    v
                              prompt_template / mock generation
                                    |
                                    v
                            format_final_response
```

## MOCK_LLM behavior

The toggle is defined as:

- `MOCK_LLM = os.environ.get("MOCK_LLM", "1") == "1"`

This means the default behavior is mock mode (`MOCK_LLM` unset or set to `1`). In that state:
- intent classification uses a keyword heuristic,
- `retrieve_and_answer` returns a canned answer based on the top retrieved snippet,
- `direct_answer` returns the fixed canned general-answer message,
- the final response is generated from the state without calling an external LLM.

When `MOCK_LLM` is set to `0` (or the optional real-LLM branch is enabled):
- the same graph structure remains, but the classification and generation nodes are expected to call an LLM instead of using the mock heuristics,
- `retrieve_and_answer` would use the formatted policy context and `prompt_template` to generate a grounded answer,
- `direct_answer` would answer general questions through a direct LLM prompt,
- the result would still flow through `format_final_response`, but the answer text would come from the model rather than the hardcoded mock logic.

In short, the branching on `MOCK_LLM` affects the generation and classification path, while the ingestion, ChromaDB storage, and retrieval logic remain the same in both modes.

## Local Docker build and run

Build the FastAPI app image locally:

```bash
docker build -t zepto-support-assistant .
```

Run the container locally:

```bash
docker run --rm -p 7860:7860 zepto-support-assistant
```

The app serves the `/ask` endpoint locally at:

```text
http://localhost:7860/ask
```

Example request:

```bash
curl -X POST http://localhost:7860/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the delivery fees?"}'
```

Example response:

```json
{
  "answer": "Based on the retrieved context: ...",
  "sources": ["chunk_0", "chunk_1"],
  "confidence": 1.0
}
```
