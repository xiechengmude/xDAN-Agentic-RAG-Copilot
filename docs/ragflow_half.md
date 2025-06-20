TITLE: Example: Create Chat Completion with OpenAI SDK
DESCRIPTION: Demonstrates how to use the OpenAI Python SDK to interact with RAGFlow's OpenAI-compatible chat completion endpoint. This example shows how to send messages and handle both streaming and non-streaming responses.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_3

LANGUAGE: python
CODE:
```
from openai import OpenAI

model = "model"
client = OpenAI(api_key="ragflow-api-key", base_url=f"http://ragflow_address/api/v1/chats_openai/<chat_id>")

completion = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who are you?"}
    ],
    stream=True
)

stream = True
if stream:
    for chunk in completion:
        print(chunk)
else:
    print(completion.choices[0].message.content)
```

----------------------------------------

TITLE: API Reference: Chat Completions Request Details
DESCRIPTION: Details the HTTP POST request for initiating an AI-powered conversation with a chat assistant. It specifies the URL, required headers, and body parameters for sending a question and controlling streaming behavior.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_87

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/chats/{chat_id}/completions
Headers:
  'content-Type: application/json'
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "question": string
  "stream": boolean
  "session_id": string (optional)
  "user_id": string (optional)
```

----------------------------------------

TITLE: Python Example: Retrieving Chunks with RAGFlow
DESCRIPTION: Demonstrates how to use the `RAGFlow.retrieve` method in Python. This example initializes the RAGFlow SDK, lists datasets, uploads a document, adds a chunk, and then iterates through retrieved chunks based on dataset and document IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_38

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.list_datasets(name="ragflow")
dataset = dataset[0]
name = 'ragflow_test.txt'
path = './test_data/ragflow_test.txt'
documents =[{"display_name":"test_retrieve_chunks.txt","blob":open(path, "rb").read()}]
docs = dataset.upload_documents(documents)
doc = docs[0]
doc.add_chunk(content="This is a chunk addition test")
for c in rag_object.retrieve(dataset_ids=[dataset.id],document_ids=[doc.id]):
  print(c)
```

----------------------------------------

TITLE: API: Session.ask Method
DESCRIPTION: Documents the `ask` method of the `Session` class, which initiates an AI-powered conversation with the associated agent. It explains the `question` and `stream` parameters and the different return types (single `Message` or iterator of `Message` objects) based on the streaming mode.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_58

LANGUAGE: APIDOC
CODE:
```
Session.ask(question: str="", stream: bool = False) -> Optional[Message, iter[Message]]
  Parameters:
    question: str
      The question to start an AI-powered conversation. If the 'Begin' component takes parameters, a question is not required.
    stream: bool
      Indicates whether to output responses in a streaming way.
      True: Enable streaming (default).
      False: Disable streaming.
  Returns:
    A Message object containing the response to the question if stream is set to False.
    An iterator containing multiple message objects (iter[Message]) if stream is set to True.
```

----------------------------------------

TITLE: API Endpoint: Converse with Agent
DESCRIPTION: This section details the POST API endpoint for initiating an AI-powered conversation with a specified agent. It covers the URL structure, required headers, and the various parameters that can be included in the request body, along with important notes regarding streaming mode and custom parameters.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_102

LANGUAGE: APIDOC
CODE:
```
POST /api/v1/agents/{agent_id}/completions

Description: Asks a specified agent a question to start an AI-powered conversation.

Notes:
- In streaming mode, not all responses include a reference, as this depends on the system's judgement.
- In streaming mode, the last message is an empty message:
  data:
  {
    "code": 0,
    "data": true
  }

Request:
  Method: POST
  URL: /api/v1/agents/{agent_id}/completions
  Headers:
    'content-Type: application/json'
    'Authorization: Bearer <YOUR_API_KEY>'
  Body:
    "question": string
    "stream": boolean
    "session_id": string
    "user_id": string (optional)
    "sync_dsl": boolean (optional)
    other parameters: string

Important:
You can include custom parameters in the request body, but first ensure they are defined in the [Begin](../guides/agent/agent_component_reference/begin.mdx) agent component.
```

----------------------------------------

TITLE: Install RAGFlow Python SDK
DESCRIPTION: Run this command to download the RAGFlow Python SDK using pip. This SDK provides the necessary tools to interact with RAGFlow's functionalities programmatically.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install ragflow-sdk
```

----------------------------------------

TITLE: Manage RAGFlow Datasets and Documents
DESCRIPTION: This Python example demonstrates how to initialize the RAGFlow SDK, create a dataset, upload multiple documents, list documents by keywords, and initiate or cancel asynchronous bulk parsing of documents.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_28

LANGUAGE: python
CODE:
```
rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.create_dataset(name="dataset_name")
documents = [
    {'display_name': 'test1.txt', 'blob': open('./test_data/test1.txt',"rb").read()},
    {'display_name': 'test2.txt', 'blob': open('./test_data/test2.txt',"rb").read()},
    {'display_name': 'test3.txt', 'blob': open('./test_data/test3.txt',"rb").read()}
]
dataset.upload_documents(documents)
documents = dataset.list_documents(keywords="test")
ids = []
for document in documents:
    ids.append(document.id)
dataset.async_parse_documents(ids)
print("Async bulk parsing initiated.")
dataset.async_cancel_parse_documents(ids)
print("Async bulk parsing cancelled.")
```

----------------------------------------

TITLE: Upload Documents to a Specific Dataset
DESCRIPTION: This API endpoint facilitates uploading one or more documents to an existing dataset. It requires a multipart/form-data content type for file transfer and includes the dataset ID in the URL path.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_25

LANGUAGE: APIDOC
CODE:
```
Endpoint: POST /api/v1/datasets/{dataset_id}/documents
Description: Uploads documents to a specified dataset.
Request Details:
- Method: POST
- URL: `/api/v1/datasets/{dataset_id}/documents`
- Headers:
  - `'Content-Type: multipart/form-data'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- Form:
  - `'file=@{FILE_PATH}'`
```

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents \
     --header 'Content-Type: multipart/form-data' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --form 'file=@./test1.txt' \
     --form 'file=@./test2.pdf'
```

LANGUAGE: APIDOC
CODE:
```
Request Parameters:
- `dataset_id`: (Path parameter) The ID of the dataset to which the documents will be uploaded.
- `'file'`: (Body parameter) A document to upload.
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": [
        {
            "chunk_method": "naive",
            "created_by": "69736c5e723611efb51b0242ac120007",
            "dataset_id": "527fa74891e811ef9c650242ac120006",
            "id": "b330ec2e91ec11efbc510242ac120004",
            "location": "1.txt",
            "name": "1.txt",
            "parser_config": {
                "chunk_token_num": 128,
                "delimiter": "\\n",
                "html4excel": false,
                "layout_recognize": true,
                "raptor": {
                    "use_raptor": false
                }
            },
            "run": "UNSTART",
            "size": 17966,
            "thumbnail": "",
            "type": "doc"
        }
    ]
}
```

LANGUAGE: json
CODE:
```
{
    "code": 101,
    "message": "No file part!"
}
```

----------------------------------------

TITLE: API: Agent.create_session Method
DESCRIPTION: Documents the `create_session` method of the `Agent` class, used to establish a new conversation session. It details the `kwargs` parameters, the `Session` object returned on success, and potential exceptions on failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_56

LANGUAGE: APIDOC
CODE:
```
Agent.create_session(**kwargs) -> Session
  Parameters:
    **kwargs: The parameters in 'begin' component.
  Returns:
    Success: Session object
      id: str
        The auto-generated unique identifier of the created session.
      message: list[Message]
        The messages of the created session assistant. Default: [{"role": "assistant", "content": "Hi! I am your assistant, can I help you?"}]
      agent_id: str
        The ID of the associated agent.
    Failure: Exception
```

----------------------------------------

TITLE: Converse with RAGFlow Chat Assistant - Python
DESCRIPTION: This Python example demonstrates how to use the `ragflow_sdk` to interact with a chat assistant. It initializes the SDK, retrieves a specific assistant by name, creates a conversation session, and then continuously prompts the user for questions and preferred styles, streaming the assistant's responses back to the console. It requires an API key and base URL for the RAGFlow service.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/chat/set_chat_variables.md#_snippet_2

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
assistant = rag_object.list_chats(name="Miss R")
assistant = assistant[0]
session = assistant.create_session()    

print("\n==================== Miss R =====================\n")
print("Hello. What can I do for you?")

while True:
    question = input("\n==================== User =====================\n> ")
    style = input("Please enter your preferred style (e.g., formal, informal, hilarious): ")
    
    print("\n==================== Miss R =====================\n")
    
    cont = ""
    for ans in session.ask(question, stream=True, style=style):
        print(ans.content[len(cont):], end='', flush=True)
        cont = ans.content
```

----------------------------------------

TITLE: Example System Prompt for Translation Improvement (Text)
DESCRIPTION: This system prompt excerpt from the 'Interpreter' template (component ID: 'Reflect') guides an LLM to provide constructive suggestions for improving a translation. It defines the task, specifies input formats using XML tags for source text and translation, and outlines criteria for suggestions, such as fluency, grammar, spelling, punctuation, and avoiding repetitions. It utilizes variables like {target_lang}, {source_text}, and {translation_1} for dynamic data input.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/agent_component_reference/generate.mdx#_snippet_0

LANGUAGE: text
CODE:
```
Your task is to read a source text and a translation to {target_lang}, and give constructive suggestions to improve the translation. The source text and initial translation, delimited by XML tags <SOURCE_TEXT></SOURCE_TEXT> and <TRANSLATION></TRANSLATION>, are as follows:

<SOURCE_TEXT>
{source_text}
</SOURCE_TEXT>

<TRANSLATION>
{translation_1}
</TRANSLATION>

When writing suggestions, pay attention to whether there are ways to improve the translation's fluency, by applying {target_lang} grammar, spelling and punctuation rules, and ensuring there are no unnecessary repetitions.
- Each suggestion should address one specific part of the translation.
- Output the suggestions only.
```

----------------------------------------

TITLE: Start RAGFlow Server with Docker Compose (CPU)
DESCRIPTION: This snippet shows how to navigate to the Docker directory and start the RAGFlow server using Docker Compose with CPU for embedding and DeepDoc tasks. It utilizes the `docker-compose.yml` file for deployment.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
$ cd ragflow/docker
# Use CPU for embedding and DeepDoc tasks:
$ docker compose -f docker-compose.yml up -d
```

----------------------------------------

TITLE: Add Chunk to Document Example
DESCRIPTION: Python example demonstrating how to initialize RAGFlow, retrieve a dataset and document, and then add a new chunk with specified content to that document.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_30

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
datasets = rag_object.list_datasets(id="123")
dataset = datasets[0]
doc = dataset.list_documents(id="wdfxb5t547d")
doc = doc[0]
chunk = doc.add_chunk(content="xxxxxxx")
```

----------------------------------------

TITLE: Building RAGFlow Docker Image including Embedding Models (Bash)
DESCRIPTION: This snippet outlines the Bash commands to clone the RAGFlow repository, download dependencies, and build a Docker image that includes embedding models. This image is larger (approx. 9 GB) and only requires external LLM services, making it suitable for environments where embedding models need to be self-contained.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/build_docker_image.mdx#_snippet_1

LANGUAGE: bash
CODE:
```
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/
uv run download_deps.py
docker build -f Dockerfile.deps -t infiniflow/ragflow_deps .
docker build -f Dockerfile -t infiniflow/ragflow:nightly .
```

----------------------------------------

TITLE: Installing RAGFlow Python Dependencies (Full) - Bash
DESCRIPTION: This command uses 'uv' to synchronize and install all Python dependencies, including optional extras, for RAGFlow, targeting Python 3.10. It ensures all features are available by installing a comprehensive set of modules.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_3

LANGUAGE: bash
CODE:
```
uv sync --python 3.10 --all-extras
```

----------------------------------------

TITLE: RAGFlow API Error Codes Reference
DESCRIPTION: A comprehensive list of HTTP and custom error codes returned by the RAGFlow API, detailing their messages and descriptions to aid in debugging and error handling.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_0

LANGUAGE: APIDOC
CODE:
```
Error Codes:
  400: Bad Request - Invalid request parameters
  401: Unauthorized - Unauthorized access
  403: Forbidden - Access denied
  404: Not Found - Resource not found
  500: Internal Server Error - Server internal error
  1001: Invalid Chunk ID - Invalid Chunk ID
  1002: Chunk Update Failed - Chunk update failed
```

----------------------------------------

TITLE: Converse with Agent using Streaming Mode (Python)
DESCRIPTION: Demonstrates how to initialize the RAGFlow SDK, retrieve an agent, create a session, and engage in a real-time, streaming conversation with the agent. It shows how to print the streamed content incrementally.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_54

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
assistant = rag_object.list_chats(name="Miss R")
assistant = assistant[0]
session = assistant.create_session()    

print("\n==================== Miss R =====================\n")
print("Hello. What can I do for you?")

while True:
    question = input("\n==================== User =====================\n> ")
    print("\n==================== Miss R =====================\n")
    
    cont = ""
    for ans in session.ask(question, stream=True):
        print(ans.content[len(cont):], end='', flush=True)
        cont = ans.content
```

----------------------------------------

TITLE: Python: Interact with Agent and Ask Questions
DESCRIPTION: Demonstrates how to initialize the RAGFlow SDK, retrieve an agent, create a session, and interactively ask questions, streaming the responses. Requires an API key and base URL.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_60

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow, Agent

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
AGENT_id = "AGENT_ID"
agent = rag_object.list_agents(id = AGENT_id)[0]
session = agent.create_session()    

print("\n===== Miss R ====\n")
print("Hello. What can I do for you?")

while True:
    question = input("\n===== User ====\n> ")
    print("\n==== Miss R ====\n")
    
    cont = ""
    for ans in session.ask(question, stream=True):
        print(ans.content[len(cont):], end='', flush=True)
        cont = ans.content
```

----------------------------------------

TITLE: Updating and Restarting RAGFlow Docker
DESCRIPTION: Pulls the specified RAGFlow Docker image and then restarts the RAGFlow services in detached mode using Docker Compose. This command applies the new image configuration and ensures the RAGFlow application is running with the updated version.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/upgrade_ragflow.mdx#_snippet_3

LANGUAGE: bash
CODE:
```
docker compose -f docker/docker-compose.yml pull
docker compose -f docker/docker-compose.yml up -d
```

----------------------------------------

TITLE: RAGFlow Chat.Prompt Object Attributes
DESCRIPTION: Defines the attributes of the `Chat.Prompt` object used to configure LLM instructions and retrieval parameters within RAGFlow. It includes settings for similarity thresholds, keyword weighting, top-N chunk selection, variable handling, reranking models, and default responses.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_40

LANGUAGE: APIDOC
CODE:
```
Chat.Prompt:
  similarity_threshold: float
    RAGFlow employs either a combination of weighted keyword similarity and weighted vector cosine similarity, or a combination of weighted keyword similarity and weighted reranking score during retrieval. If a similarity score falls below this threshold, the corresponding chunk will be excluded from the results. The default value is 0.2.
  keywords_similarity_weight: float
    This argument sets the weight of keyword similarity in the hybrid similarity score with vector cosine similarity or reranking model similarity. By adjusting this weight, you can control the influence of keyword similarity in relation to other similarity measures. The default value is 0.7.
  top_n: int
    This argument specifies the number of top chunks with similarity scores above the similarity_threshold that are fed to the LLM. The LLM will only access these 'top N' chunks. The default value is 8.
  variables: list[dict[]]
    This argument lists the variables to use in the 'System' field of Chat Configurations. Note that:
    - knowledge is a reserved variable, which represents the retrieved chunks.
    - All the variables in 'System' should be curly bracketed.
    - The default value is [{"key": "knowledge", "optional": True}].
  rerank_model: str
    If it is not specified, vector cosine similarity will be used; otherwise, reranking score will be used. Defaults to "".
  top_k: int
    Refers to the process of reordering or selecting the top-k items from a list or set based on a specific ranking criterion. Default to 1024.
  empty_response: str
    If nothing is retrieved in the dataset for the user's question, this will be used as the response. To allow the LLM to improvise when nothing is found, leave this blank. Defaults to None.
  opener: str
    The opening greeting for the user. Defaults to "Hi! I am your assistant, can I help you?".
  show_quote: bool
    Indicates whether the source of text should be displayed. Defaults to True.
  prompt: str
    The prompt content.
Returns:
  Success: A Chat object representing the chat assistant.
  Failure: Exception
```

----------------------------------------

TITLE: Pulling Llama3.2 Model via Ollama Docker
DESCRIPTION: This command executes `ollama pull llama3.2` inside the running Ollama Docker container to download the `llama3.2` chat model. The output indicates the progress and successful completion of the model download, making it available for use.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_2

LANGUAGE: bash
CODE:
```
$ sudo docker exec ollama ollama pull llama3.2
> pulling dde5aa3fc5ff... 100% │████████████████▓ 2.0 GB
> success
```

----------------------------------------

TITLE: Query API Request Parameters
DESCRIPTION: Defines the parameters accepted by the Ragflow query API. These parameters control aspects like the search query, target datasets/documents, pagination, similarity thresholds, and keyword matching. Most parameters are body parameters, with some being required and others having default values.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_57

LANGUAGE: APIDOC
CODE:
```
Request parameters:
- "question": (Body parameter), string, Required
  The user query or query keywords.
- "dataset_ids": (Body parameter) list[string]
  The IDs of the datasets to search. If you do not set this argument, ensure that you set "document_ids".
- "document_ids": (Body parameter), list[string]
  The IDs of the documents to search. Ensure that all selected documents use the same embedding model. Otherwise, an error will occur. If you do not set this argument, ensure that you set "dataset_ids".
- "page": (Body parameter), integer
  Specifies the page on which the chunks will be displayed. Defaults to 1.
- "page_size": (Body parameter)
  The maximum number of chunks on each page. Defaults to 30.
- "similarity_threshold": (Body parameter)
  The minimum similarity score. Defaults to 0.2.
- "vector_similarity_weight": (Body parameter), float
  The weight of vector cosine similarity. Defaults to 0.3. If x represents the weight of vector cosine similarity, then (1 - x) is the term similarity weight.
- "top_k": (Body parameter), integer
  The number of chunks engaged in vector cosine computation. Defaults to 1024.
- "rerank_id": (Body parameter), integer
  The ID of the rerank model.
- "keyword": (Body parameter), boolean
  Indicates whether to enable keyword-based matching:
  - true: Enable keyword-based matching.
  - false: Disable keyword-based matching (default).
- "highlight": (Body parameter), boolean
  Specifies whether to enable highlighting of matched terms in the results:
  - true: Enable highlighting of matched terms.
  - false: Disable highlighting of matched terms (default).
```

----------------------------------------

TITLE: Python: Upload and List Documents in RagFlow SDK
DESCRIPTION: Demonstrates how to initialize the `RAGFlow` SDK, create a dataset, upload a local file as a document, and then list documents within that dataset, filtering by keywords.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_22

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.create_dataset(name="kb_1")

filename1 = "~/ragflow.txt"
blob = open(filename1 , "rb").read()
dataset.upload_documents([{"name":filename1,"blob":blob}])
for doc in dataset.list_documents(keywords="rag", page=0, page_size=12):
    print(doc)
```

----------------------------------------

TITLE: RAGFlow OpenAI-Compatible Chat Completion API Definition
DESCRIPTION: Defines the POST endpoint for creating chat completions, which adheres to the OpenAI API request and response format. This allows users to interact with RAGFlow models similarly to OpenAI's chat API.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_1

LANGUAGE: APIDOC
CODE:
```
Endpoint: /api/v1/chats_openai/{chat_id}/chat/completions
  Method: POST
  Description: Creates a model response for a given chat conversation.
  Headers:
    Content-Type: application/json
    Authorization: Bearer <YOUR_API_KEY>
  Body Parameters:
    model: string (Required)
      Description: The model used to generate the response. The server will parse this automatically, so you can set it to any value for now.
    messages: list[object] (Required)
      Description: A list of historical chat messages used to generate the response. This must contain at least one message with the 'user' role.
    stream: boolean (Optional)
      Description: Whether to receive the response as a stream. Set this to 'false' explicitly if you prefer to receive the entire response in one go instead of as a stream.
```

----------------------------------------

TITLE: Create Session with a Specific Agent (Python)
DESCRIPTION: Illustrates how to initialize the RAGFlow SDK, retrieve a specific agent by ID, and then create a new conversation session linked to that agent.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_57

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow, Agent

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
agent_id = "AGENT_ID"
agent = rag_object.list_agents(id = agent_id)[0]
session = agent.create_session()
```

----------------------------------------

TITLE: Procedure to Construct and Use Knowledge Graph in RAGFlow
DESCRIPTION: A step-by-step guide detailing how to enable, configure, and utilize the knowledge graph feature within a RAGFlow knowledge base, and how to integrate it into chat configurations or agent components for enhanced retrieval.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/dataset/construct_knowledge_graph.md#_snippet_4

LANGUAGE: APIDOC
CODE:
```
Procedure:
  1. On the Configuration page of your knowledge base, switch on 'Extract knowledge graph' or adjust its settings as needed, and click 'Save' to confirm your changes.
     - The default knowledge graph configurations for your knowledge base are now set and files uploaded from this point onward will automatically use these settings during parsing.
     - Files parsed before this update will retain their original knowledge graph settings.
  2. The knowledge graph of your knowledge base does not automatically update until a newly uploaded file is parsed.
     - A 'Knowledge graph' entry appears under 'Configuration' once a knowledge graph is created.
  3. Click 'Knowledge graph' to view the details of the generated graph.
  4. To use the created knowledge graph, do either of the following:
     - In your Chat Configuration dialogue, click the 'Assistant settings' tab to add the corresponding knowledge base(s) and click the 'Prompt engine' tab to switch on the 'Use knowledge graph' toggle.
     - If you are using an agent, click the 'Retrieval' agent component to specify the knowledge base(s) and switch on the 'Use knowledge graph' toggle.
```

----------------------------------------

TITLE: Chat Completion Stream Response Example
DESCRIPTION: Illustrates the JSON format for a streaming chat completion response, showing initial, intermediate, and final chunks. The 'delta' field contains content updates, and subsequent chunks provide continuous content until 'finish_reason' is 'stop'.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_8

LANGUAGE: json
CODE:
```
{
    "id": "chatcmpl-3a9c3572f29311efa69751e139332ced",
    "choices": [
        {
            "delta": {
                "content": "This is a test. If you have any specific questions or need information, feel",
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1740543996,
    "model": "model",
    "object": "chat.completion.chunk",
    "system_fingerprint": "",
    "usage": null
}
{"choices":[{"delta":{"content":" free to ask, and I will do my best to provide an answer based on","role":"assistant"}}]}
{"choices":[{"delta":{"content":" the knowledge I have. If your question is unrelated to the provided knowledge base,","role":"assistant"}}]}
{"choices":[{"delta":{"content":" I will let you know.","role":"assistant"}}]}
{
    "id": "chatcmpl-3a9c3572f29311efa69751e139332ced",
    "choices": [
        {
            "delta": {
                "content": null,
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1740543996,
    "model": "model",
    "object": "chat.completion.chunk",
    "system_fingerprint": "",
    "usage": {
        "prompt_tokens": 18,
        "completion_tokens": 225,
        "total_tokens": 243
    }
}
```

----------------------------------------

TITLE: Launching Third-Party Services with Docker Compose - Bash
DESCRIPTION: This command uses Docker Compose to launch essential third-party services (MinIO, Elasticsearch, Redis, MySQL) required by RAGFlow. The `-f` flag specifies the `docker-compose-base.yml` file, and `-d` runs the containers in detached mode.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_4

LANGUAGE: bash
CODE:
```
docker compose -f docker/docker-compose-base.yml up -d
```

----------------------------------------

TITLE: Configuring OAuth2, OIDC, and GitHub Authentication Clients in Python
DESCRIPTION: This snippet demonstrates how to define configuration dictionaries for OAuth2, OIDC, and GitHub authentication providers. These configurations specify the type of authentication, client credentials, and necessary URLs for integration. The get_auth_client function is then used to initialize an authentication client instance based on the provided configuration.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/api/apps/auth/README.md#_snippet_0

LANGUAGE: python
CODE:
```
# OAuth2 configuration
oauth_config = {
    "type": "oauth2",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "authorization_url": "https://your-oauth-provider.com/oauth/authorize",
    "token_url": "https://your-oauth-provider.com/oauth/token",
    "userinfo_url": "https://your-oauth-provider.com/oauth/userinfo",
    "redirect_uri": "https://your-app.com/v1/user/oauth/callback/<channel>"
}

# OIDC configuration
oidc_config = {
    "type": "oidc",
    "issuer": "https://your-oauth-provider.com/oidc",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "https://your-app.com/v1/user/oauth/callback/<channel>"
}

# Github OAuth configuration
github_config = {
    "type": "github",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "https://your-app.com/v1/user/oauth/callback/<channel>"
}

# Get client instance
client = get_auth_client(oauth_config)
```

----------------------------------------

TITLE: Create Chat Assistant API Request Example (curl)
DESCRIPTION: A curl command example demonstrating how to create a chat assistant via the API. It shows how to specify the POST method, URL, content type, authorization header, and the JSON request body with required parameters like dataset_ids and name.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_61

LANGUAGE: shell
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/chats \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
    "dataset_ids": ["0b2cbc8c877f11ef89070242ac120005"],
    "name":"new_chat_1"
}'
```

----------------------------------------

TITLE: API: List Datasets Endpoint and Request Parameters
DESCRIPTION: Defines the GET endpoint for retrieving a list of datasets, specifying URL parameters for pagination, ordering, and filtering, along with required headers.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_23

LANGUAGE: APIDOC
CODE:
```
List datasets:
  Method: GET
  URL: /api/v1/datasets?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={dataset_name}&id={dataset_id}
  Headers:
    'Authorization: Bearer <YOUR_API_KEY>'
```

----------------------------------------

TITLE: Configure Knowledge Graph Extraction Method
DESCRIPTION: Specifies the underlying method for extracting entities and relationships to construct the knowledge graph. Two options are available: General (GraphRAG prompts) and Light (LightRAG prompts), with Light being the default and more resource-efficient choice.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/dataset/construct_knowledge_graph.md#_snippet_1

LANGUAGE: APIDOC
CODE:
```
Method:
  Description: The method to use to construct knowledge graph.
  Options:
    - General: Use prompts provided by GraphRAG to extract entities and relationships.
    - Light: (Default) Use prompts provided by LightRAG to extract entities and relationships. This option consumes fewer tokens, less memory, and fewer computational resources.
```

----------------------------------------

TITLE: Create Dataset API Request Parameters
DESCRIPTION: Defines the body parameters required to create a new dataset, including name, avatar, description, embedding model, permission, chunking method, and parser configuration. Details constraints and default values for each parameter.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_13

LANGUAGE: APIDOC
CODE:
```
Request Parameters:
- "name": (Body parameter), string, Required
  Description: The unique name of the dataset to create.
  Constraints:
    - Basic Multilingual Plane (BMP) only
    - Maximum 128 characters
    - Case-insensitive
- "avatar": (Body parameter), string
  Description: Base64 encoding of the avatar.
  Constraints:
    - Maximum 65535 characters
- "description": (Body parameter), string
  Description: A brief description of the dataset to create.
  Constraints:
    - Maximum 65535 characters
- "embedding_model": (Body parameter), string
  Description: The name of the embedding model to use.
  Example: "BAAI/bge-large-zh-v1.5@BAAI"
  Constraints:
    - Maximum 255 characters
    - Must follow `model_name@model_factory` format
- "permission": (Body parameter), string
  Description: Specifies who can access the dataset to create.
  Available options:
    - "me": (Default) Only you can manage the dataset.
    - "team": All team members can manage the dataset.
- "chunk_method": (Body parameter), enum<string>
  Description: The chunking method of the dataset to create.
  Available options:
    - "naive": General (default)
    - "book": Book
    - "email": Email
    - "laws": Laws
    - "manual": Manual
    - "one": One
    - "paper": Paper
    - "picture": Picture
    - "presentation": Presentation
    - "qa": Q&A
    - "table": Table
    - "tag": Tag
- "parser_config": (Body parameter), object
  Description: The configuration settings for the dataset parser. Attributes vary with "chunk_method".
  If "chunk_method" is "naive":
    - "auto_keywords": int
      Defaults: 0, Minimum: 0, Maximum: 32
    - "auto_questions": int
      Defaults: 0, Minimum: 0, Maximum: 10
    - "chunk_token_num": int
      Defaults: 128, Minimum: 1, Maximum: 2048
    - "delimiter": string
      Defaults: "\n"
    - "html4excel": bool
      Description: Indicates whether to convert Excel documents into HTML format.
      Defaults: false
    - "layout_recognize": string
      Defaults: "DeepDOC"
    - "tag_kb_ids": array<string>
      Description: Must include a list of dataset IDs, where each dataset is parsed using the Tag Chunk Method.
    - "task_page_size": int
      Description: For PDF only.
      Defaults: 12, Minimum: 1
    - "raptor": object
      Description: RAPTOR-specific settings.
      Defaults: {"use_raptor": false}
    - "graphrag": object
      Description: GRAPHRAG-specific settings.
      Defaults: {"use_graphrag": false}
  If "chunk_method" is "qa", "manuel", "paper", "book", "laws", or "presentation":
    - "raptor": object
      Description: RAPTOR-specific settings.
      Defaults: {"use_raptor": false}
  If "chunk_method" is "table", "picture", "one", or "email":
    - "parser_config" is an empty JSON object.
```

----------------------------------------

TITLE: Configuring HuggingFace Endpoint Mirror (Bash)
DESCRIPTION: This bash command sets the `HF_ENDPOINT` environment variable to `https://hf-mirror.com`. This is useful for users who experience difficulties downloading models directly from HuggingFace, as it redirects requests to a mirror, potentially improving download reliability and speed. This configuration helps resolve common network issues when accessing HuggingFace resources.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/deepdoc/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
export HF_ENDPOINT=https://hf-mirror.com
```

----------------------------------------

TITLE: API Documentation: List Agents
DESCRIPTION: Comprehensive documentation for the GET /api/v1/agents endpoint. This API allows for listing agents with optional pagination, sorting, and filtering by name or ID.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_123

LANGUAGE: APIDOC
CODE:
```
Endpoint: GET /api/v1/agents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={agent_name}&id={agent_id}
Description: Lists agents.

Request:
  Method: GET
  URL: /api/v1/agents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={agent_name}&id={agent_id}
  Headers:
    'Authorization: Bearer <YOUR_API_KEY>'
```

----------------------------------------

TITLE: Defining LLM Tool Plugin Class in Python
DESCRIPTION: This snippet shows the basic structure for defining a custom LLM tool plugin in RAGFlow. It demonstrates inheriting from `LLMToolPlugin` and setting the required `_version_` field, which specifies the plugin's version.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/plugin/README.md#_snippet_0

LANGUAGE: Python
CODE:
```
class BadCalculatorPlugin(LLMToolPlugin):
    _version_ = "1.0.0"
```

----------------------------------------

TITLE: RAGFlow.create_chat API Reference
DESCRIPTION: Documents the `create_chat` method of the `RAGFlow` class, used for creating new chat assistants. It outlines the required and optional parameters, including settings for the chat assistant's name, avatar, associated datasets, and LLM configuration.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_39

LANGUAGE: APIDOC
CODE:
```
RAGFlow.create_chat(name: str, avatar: str = "", dataset_ids: list[str] = [], llm: Chat.LLM = None, prompt: Chat.Prompt = None) -> Chat
Parameters:
  name: str, Required
    The name of the chat assistant.
  avatar: str
    Base64 encoding of the avatar. Defaults to "".
  dataset_ids: list[str]
    The IDs of the associated datasets. Defaults to [""]
  llm: Chat.LLM
    The LLM settings for the chat assistant to create. Defaults to None. When the value is None, a dictionary with the following values will be generated as the default. An LLM object contains the following attributes:
    model_name: str
      The chat model name. If it is None, the user's default chat model will be used.
    temperature: float
      Controls the randomness of the model's predictions. A lower temperature results in more conservative responses, while a higher temperature yields more creative and diverse responses. Defaults to 0.1.
    top_p: float
      Also known as “nucleus sampling”, this parameter sets a threshold to select a smaller set of words to sample from. It focuses on the most likely words, cutting off the less probable ones. Defaults to 0.3
    presence_penalty: float
      This discourages the model from repeating the same information by penalizing words that have already appeared in the conversation. Defaults to 0.2.
    frequency penalty: float
      Similar to the presence penalty, this reduces the model’s tendency to repeat the same words frequently. Defaults to 0.7.
```

----------------------------------------

TITLE: Fetching User Information with Access Token in Python
DESCRIPTION: This snippet illustrates how to use the obtained access token to fetch detailed user information from the identity provider. The returned user_info typically includes details like email, username, and avatar URL.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/api/apps/auth/README.md#_snippet_3

LANGUAGE: python
CODE:
```
user_info = client.fetch_user_info(access_token)
```

----------------------------------------

TITLE: S3-Compatible Object Storage Configuration
DESCRIPTION: Specifies parameters for connecting to S3-compatible object storage services, including access keys, endpoint, bucket, region, and optional signature/addressing styles for authentication and request routing.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_12

LANGUAGE: APIDOC
CODE:
```
s3:
  access_key: The access key ID used to authenticate requests to the S3 service.
  secret_key: The secret access key used to authenticate requests to the S3 service.
  endpoint_url: The URL of the S3-compatible service endpoint. This is necessary when using an S3-compatible protocol instead of the default AWS S3 endpoint.
  bucket: The name of the S3 bucket where files will be stored. When you want to store all files in a specified bucket, you need this configuration item.
  region: The AWS region where the S3 bucket is located. This is important for directing requests to the correct data center.
  signature_version: Optional. The version of the signature to use for authenticating requests. Common versions include v4.
  addressing_style: Optional. The style of addressing to use for the S3 endpoint. This can be path or virtual.
  prefix_path: Optional. A prefix path to prepend to file names in the S3 bucket, which can help organize files within the bucket.
```

----------------------------------------

TITLE: Start RAGFlow Server with Docker Compose (GPU)
DESCRIPTION: This snippet provides the command to start the RAGFlow server using Docker Compose with GPU acceleration for embedding and DeepDoc tasks. It specifically uses the `docker-compose-gpu.yml` file for GPU-enabled deployment.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_5

LANGUAGE: bash
CODE:
```
# To use GPU to accelerate embedding and DeepDoc tasks:
# docker compose -f docker-compose-gpu.yml up -d
```

----------------------------------------

TITLE: RAGFlow.retrieve API Reference
DESCRIPTION: Documents the `retrieve` method of the `RAGFlow` class, which is used to fetch document chunks from specified datasets. It details all available parameters, their types, default values, and descriptions, along with return types.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_37

LANGUAGE: APIDOC
CODE:
```
RAGFlow.retrieve(question:str="", dataset_ids:list[str]=None, document_ids=list[str]=None, page:int=1, page_size:int=30, similarity_threshold:float=0.2, vector_similarity_weight:float=0.3, top_k:int=1024,rerank_id:str=None,keyword:bool=False,highlight:bool=False) -> list[Chunk]
Parameters:
  question: str, Required
    The user query or query keywords. Defaults to "".
  dataset_ids: list[str], Required
    The IDs of the datasets to search. Defaults to None.
  document_ids: list[str]
    The IDs of the documents to search. Defaults to None. You must ensure all selected documents use the same embedding model. Otherwise, an error will occur.
  page: int
    The starting index for the documents to retrieve. Defaults to 1.
  page_size: int
    The maximum number of chunks to retrieve. Defaults to 30.
  Similarity_threshold: float
    The minimum similarity score. Defaults to 0.2.
  vector_similarity_weight: float
    The weight of vector cosine similarity. Defaults to 0.3. If x represents the vector cosine similarity, then (1 - x) is the term similarity weight.
  top_k: int
    The number of chunks engaged in vector cosine computation. Defaults to 1024.
  rerank_id: str
    The ID of the rerank model. Defaults to None.
  keyword: bool
    Indicates whether to enable keyword-based matching:
    True: Enable keyword-based matching.
    False: Disable keyword-based matching (default).
  highlight: bool
    Specifies whether to enable highlighting of matched terms in the results:
    True: Enable highlighting of matched terms.
    False: Disable highlighting of matched terms (default).
Returns:
  Success: A list of Chunk objects representing the document chunks.
  Failure: Exception
```

----------------------------------------

TITLE: Create Dataset API Request Example (cURL)
DESCRIPTION: Provides a cURL command example for making a POST request to the /api/v1/datasets endpoint. It includes the necessary 'Content-Type' and 'Authorization' headers, along with a minimal JSON body to create a dataset named 'test_1'.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_12

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/datasets \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
      "name": "test_1"
      }'
```

----------------------------------------

TITLE: cURL Example: List Agents
DESCRIPTION: A cURL command example demonstrating how to send a GET request to the /api/v1/agents endpoint to retrieve a list of agents, including optional query parameters for pagination and filtering.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_124

LANGUAGE: bash
CODE:
```
curl --request GET \
     --url http://{address}/api/v1/agents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={agent_name}&id={agent_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

----------------------------------------

TITLE: Example: Create Chat Session using cURL
DESCRIPTION: Provides a cURL command demonstrating how to make a POST request to the /api/v1/chats/{chat_id}/sessions endpoint, including content type, authorization headers, and a JSON request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_79

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/chats/{chat_id}/sessions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '\n     {\n          "name": "new session"\n     }'
```

----------------------------------------

TITLE: RAGFlow API: Create Dataset
DESCRIPTION: Defines the `create_dataset` method for RAGFlow's Python API, detailing its parameters, their types, requirements, and default values. It also specifies available options for dataset creation, including various chunking methods and parser configurations.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_4

LANGUAGE: APIDOC
CODE:
```
RAGFlow.create_dataset(
    name: str,
    avatar: Optional[str] = None,
    description: Optional[str] = None,
    embedding_model: Optional[str] = "BAAI/bge-large-zh-v1.5@BAAI",
    permission: str = "me", 
    chunk_method: str = "naive",
    parser_config: DataSet.ParserConfig = None
) -> DataSet

Creates a dataset.

Parameters:
  name: str, Required
    description: The unique name of the dataset to create. It must adhere to the following requirements:
      - Maximum 128 characters.
      - Case-insensitive.
  avatar: str
    description: Base64 encoding of the avatar. Defaults to None
  description: str
    description: A brief description of the dataset to create. Defaults to None.
  permission: str
    description: Specifies who can access the dataset to create. Available options:  
      - "me": (Default) Only you can manage the dataset.
      - "team": All team members can manage the dataset.
  chunk_method: str
    description: The chunking method of the dataset to create. Available options:
      - "naive": General (default)
      - "manual": Manual
      - "qa": Q&A
      - "table": Table
      - "paper": Paper
      - "book": Book
      - "laws": Laws
      - "presentation": Presentation
      - "picture": Picture
      - "one": One
      - "email": Email
  parser_config: DataSet.ParserConfig
    description: The parser configuration of the dataset. A ParserConfig object's attributes vary based on the selected chunk_method:
      - chunk_method="naive": {"chunk_token_num":128,"delimiter":"\\n","html4excel":False,"layout_recognize":True,"raptor":{"use_raptor":False}}.
      - chunk_method="qa": {"raptor": {"use_raptor": False}}
      - chunk_method="manuel": {"raptor": {"use_raptor": False}}
      - chunk_method="table": None
      - chunk_method="paper": {"raptor": {"use_raptor": False}}
      - chunk_method="book": {"raptor": {"use_raptor": False}}
      - chunk_method="laws": {"raptor": {"use_raptor": False}}
      - chunk_method="picture": None
      - chunk_method="presentation": {"raptor": {"use_raptor": False}}
      - chunk_method="one": None
      - chunk_method="knowledge-graph": {"chunk_token_num":128,"delimiter":"\\n","entity_types":["organization","person","location","event","time"]}
      - chunk_method="email": None
Returns:
  Success: A dataset object.
  Failure: Exception
```

----------------------------------------

TITLE: API Documentation: Create Dataset
DESCRIPTION: Documents the POST /api/v1/datasets endpoint for creating a new dataset. It specifies the request method, URL, required headers, and the body parameters with their respective data types.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_11

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/datasets
Description: Creates a dataset.
Headers:
  - 'content-Type: application/json'
  - 'Authorization: Bearer <YOUR_API_KEY>'
Body Parameters:
  - name: string
  - avatar: string
  - description: string
  - embedding_model: string
  - permission: string
  - chunk_method: string
  - parser_config: object
```

----------------------------------------

TITLE: Pulling BGE-M3 Embedding Model via Ollama Docker
DESCRIPTION: This command executes `ollama pull bge-m3` inside the running Ollama Docker container to download the `bge-m3` embedding model. The output shows the download progress and confirms successful completion, making the embedding model ready for RAGFlow.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_3

LANGUAGE: bash
CODE:
```
$ sudo docker exec ollama ollama pull bge-m3                 
> pulling daec91ffb5dd... 100% │████████████████▓ 1.2 GB                                  
> success 
```

----------------------------------------

TITLE: Update Document Configurations within a Dataset
DESCRIPTION: This API endpoint allows modification of configurations for a specific document within a dataset. It supports updating properties such as the document's name, meta fields, chunking method, or parser settings via a JSON request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_26

LANGUAGE: APIDOC
CODE:
```
Endpoint: PUT /api/v1/datasets/{dataset_id}/documents/{document_id}
Description: Updates configurations for a specified document.
Request Details:
- Method: PUT
- URL: `/api/v1/datasets/{dataset_id}/documents/{document_id}`
- Headers:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- Body Parameters:
  - `"name"`: `string`
  - `"meta_fields"`: `object`
  - `"chunk_method"`: `string`
  - `"parser_config"`: `object`
```

LANGUAGE: bash
CODE:
```
curl --request PUT \
     --url http://{address}/api/v1/datasets/{dataset_id}/info/{document_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --header 'Content-Type: application/json' \
     --data '
     {
          "name": "manual.txt", 
          "chunk_method": "manual", 
          "parser_config": {"chunk_token_count": 128}
     }'
```

----------------------------------------

TITLE: Categorize Component Input Configuration
DESCRIPTION: Defines how the Categorize component receives its data inputs (queries). It supports referencing component outputs or user inputs, or using fixed text as the source.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/agent_component_reference/categorize.mdx#_snippet_0

LANGUAGE: APIDOC
CODE:
```
Input:
  + Add variable:
    - Reference:
        Component Output: Select a component ID.
        Begin input: Select a global variable from the Begin component.
    - Text: Enter static text as the query.
```

----------------------------------------

TITLE: Update Dataset Configuration in RAGFlow (Python)
DESCRIPTION: Example Python code to update an existing dataset's embedding model and chunking method. It demonstrates initializing RAGFlow, listing datasets to find the target, and then calling the update method.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_12

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.list_datasets(name="kb_name")
dataset = dataset[0]
dataset.update({"embedding_model":"BAAI/bge-zh-v1.5", "chunk_method":"manual"})
```

----------------------------------------

TITLE: API: List RAGFlow Agents
DESCRIPTION: Documents the `RAGFlow.list_agents` method, which retrieves a list of available agents. It includes parameters for pagination, sorting by creation or update time, and filtering by agent ID or title, along with return types.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_65

LANGUAGE: APIDOC
CODE:
```
RAGFlow.list_agents(
    page: int = 1, 
    page_size: int = 30, 
    orderby: str = "create_time", 
    desc: bool = True,
    id: str = None,
    title: str = None
) -> List[Agent]
Parameters:
  page: int
    Specifies the page on which the agents will be displayed. Defaults to 1.
  page_size: int
    The number of agents on each page. Defaults to 30.
  orderby: str
    The attribute by which the results are sorted. Available options: "create_time" (default), "update_time"
  desc: bool
    Indicates whether the retrieved agents should be sorted in descending order. Defaults to True.
  id: str
    The ID of the agent to retrieve. Defaults to None.
  title: str
    The name of the agent to retrieve. Defaults to None.
Returns:
  Success: A list of Agent objects.
  Failure: Exception.
```

----------------------------------------

TITLE: Converse with Chat Assistant using RAGFlow SDK
DESCRIPTION: Initiates an AI-powered conversation by asking a question to the specified chat assistant. Supports both standard and streaming response modes. Additional parameters can be passed for prompt customization. Note that references may not always be included in streaming mode.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_53

LANGUAGE: APIDOC
CODE:
```
Session.ask(question: str = "", stream: bool = False, **kwargs) -> Optional[Message, iter[Message]]
  Asks a specified chat assistant a question to start an AI-powered conversation.
  NOTE: In streaming mode, not all responses include a reference, as this depends on the system's judgement.
  Parameters:
    question: str, Required
      The question to start an AI-powered conversation. Default to "".
    stream: bool
      Indicates whether to output responses in a streaming way:
      True: Enable streaming (default).
      False: Disable streaming.
    **kwargs
      The parameters in prompt(system).
```

----------------------------------------

TITLE: Upload Documents to a Dataset in RAGFlow (Python)
DESCRIPTION: Example Python code to upload multiple documents to a newly created dataset. Each document is specified with a display name and binary content placeholder.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_14

LANGUAGE: python
CODE:
```
dataset = rag_object.create_dataset(name="kb_name")
dataset.upload_documents([{"display_name": "1.txt", "blob": "<BINARY_CONTENT_OF_THE_DOC>"}, {"display_name": "2.pdf", "blob": "<BINARY_CONTENT_OF_THE_DOC>"}])
```

----------------------------------------

TITLE: Configuring System Prompt with Variables in RAGFlow
DESCRIPTION: This snippet illustrates how to define a system prompt for an LLM within RAGFlow, incorporating both the reserved `{knowledge}` variable and a custom variable `{style}`. It shows how dynamic values can be injected into the prompt to customize the AI's behavior.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/chat/set_chat_variables.md#_snippet_0

LANGUAGE: Prompt Template
CODE:
```
You are an intelligent assistant. Please answer the question by summarizing chunks from the specified knowledge base(s)...

Your answers should follow a professional and {style} style.

...

Here is the knowledge base:
{knowledge}
The above is the knowledge base.
```

----------------------------------------

TITLE: Python: List All RAGFlow Agents Example
DESCRIPTION: Shows a Python example for listing all agents available through the RAGFlow SDK. It initializes the SDK and iterates through the retrieved agents, printing each one.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_66

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow
rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
for agent in rag_object.list_agents():
    print(agent)
```

----------------------------------------

TITLE: Create RAGFlow Agent
DESCRIPTION: This snippet demonstrates how to create a new agent using the RAGFlow SDK. It requires a title, an optional description, and a DSL dictionary for the agent's canvas configuration. The operation returns nothing on success and an Exception on failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_68

LANGUAGE: APIDOC
CODE:
```
RAGFlow.create_agent(
  title: str,
  dsl: dict,
  description: str | None = None
) -> None

Parameters:
  title: str - Specifies the title of the agent.
  dsl: dict - Specifies the canvas DSL of the agent.
  description: str - The description of the agent. Defaults to None.

Returns:
  Success: Nothing.
  Failure: Exception.
```

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow
rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
rag_object.create_agent(
  title="Test Agent",
  description="A test agent",
  dsl={
    # ... canvas DSL here ...
  }
)
```

----------------------------------------

TITLE: Default LLM Configuration for New Users
DESCRIPTION: Allows setting a default Large Language Model (LLM) for new RAGFlow users. This feature is disabled by default and requires uncommenting in `service_conf.yaml.template` to enable. It specifies the LLM supplier and its corresponding API key.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_14

LANGUAGE: APIDOC
CODE:
```
user_default_llm:
  factory: The LLM supplier. Available options: "OpenAI", "DeepSeek", "Moonshot", "Tongyi-Qianwen", "VolcEngine", "ZHIPU-AI".
  api_key: The API key for the specified LLM. You will need to apply for your model API key online.
```

----------------------------------------

TITLE: Start RAGFlow Server with Docker Compose (CPU/GPU)
DESCRIPTION: This snippet shows how to start the RAGFlow server using Docker Compose. It provides commands for both CPU-only and GPU-accelerated deployments, allowing users to choose based on their hardware capabilities. The `docker compose -f docker-compose.yml up -d` command starts the server in detached mode using CPU, while the commented-out command is for GPU acceleration.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/quickstart.mdx#_snippet_2

LANGUAGE: bash
CODE:
```
# Use CPU for embedding and DeepDoc tasks:
$ docker compose -f docker-compose.yml up -d

# To use GPU to accelerate embedding and DeepDoc tasks:
# docker compose -f docker-compose-gpu.yml up -d
```

----------------------------------------

TITLE: Check RAGFlow Server Status Logs
DESCRIPTION: This snippet shows how to check the real-time logs of the `ragflow-server` Docker container to confirm its successful launch and monitor its ongoing status. It helps in debugging and verifying system initialization.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_6

LANGUAGE: bash
CODE:
```
$ docker logs -f ragflow-server
```

----------------------------------------

TITLE: Chat Completion Failure Response JSON
DESCRIPTION: This JSON snippet shows an example of an error response from the chat completion API. It provides an error `code` and a descriptive `message` explaining the reason for the failure, aiding in debugging and error handling.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_5

LANGUAGE: json
CODE:
```
{
  "code": 102,
  "message": "The last content of this conversation is not from user."
}
```

----------------------------------------

TITLE: Restart Docker Containers to Apply Configurations
DESCRIPTION: This snippet provides the command to restart all Docker containers using `docker compose up -d` after making updates to configuration files. This ensures that any changes to settings take effect across the running services.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_8

LANGUAGE: bash
CODE:
```
$ docker compose -f docker-compose.yml up -d
```

----------------------------------------

TITLE: Check RAGFlow Component Docker Container Status
DESCRIPTION: Use this command to list all running Docker containers and their statuses, which helps in verifying if RAGFlow's components (server, Elasticsearch, MySQL, MinIO) are up and running. Note that a container being 'up' does not necessarily guarantee the service within is healthy.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/faq.mdx#_snippet_9

LANGUAGE: bash
CODE:
```
docker ps
```

LANGUAGE: plaintext
CODE:
```
5bc45806b680   infiniflow/ragflow:latest     "./entrypoint.sh"        11 hours ago   Up 11 hours               0.0.0.0:80->80/tcp, :::80->80/tcp, 0.0.0.0:443->443/tcp, :::443->443/tcp, 0.0.0.0:9380->9380/tcp, :::9380->9380/tcp   ragflow-server
91220e3285dd   docker.elastic.co/elasticsearch/elasticsearch:8.11.3   "/bin/tini -- /usr/l…"   11 hours ago   Up 11 hours (healthy)     9300/tcp, 0.0.0.0:9200->9200/tcp, :::9200->9200/tcp           ragflow-es-01
d8c86f06c56b   mysql:5.7.18        "docker-entrypoint.s…"   7 days ago     Up 16 seconds (healthy)   0.0.0.0:3306->3306/tcp, :::3306->3306/tcp     ragflow-mysql
cd29bcb254bc   quay.io/minio/minio:RELEASE.2023-12-20T01-00-02Z       "/usr/bin/docker-ent…"   2 weeks ago    Up 11 hours      0.0.0.0:9001->9001/tcp, :::9001->9001/tcp, 0.0.0.0:9000->9000/tcp, :::9000->9000/tcp     ragflow-minio
```

----------------------------------------

TITLE: API Reference: Update Chat Assistant Request Parameters
DESCRIPTION: Defines the parameters required for updating an existing chat assistant, including path and body parameters for identification, naming, avatar, dataset associations, LLM configurations, and prompt settings.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_67

LANGUAGE: APIDOC
CODE:
```
chat_id: (Path parameter) The ID of the chat assistant to update.
"name": (Body parameter), string, Required
  The revised name of the chat assistant.
"avatar": (Body parameter), string
  Base64 encoding of the avatar.
"dataset_ids": (Body parameter), list[string]
  The IDs of the associated datasets.
"llm": (Body parameter), object
  The LLM settings for the chat assistant to create.
  - "model_name": string
      The chat model name. If not set, the user's default chat model will be used.
  - "temperature": float
      Controls the randomness of the model's predictions. Defaults to 0.1.
  - "top_p": float
      Also known as “nucleus sampling”, this parameter sets a threshold to select a smaller set of words to sample from. Defaults to 0.3.
  - "presence_penalty": float
      This discourages the model from repeating the same information by penalizing words that have already appeared in the conversation. Defaults to 0.2.
  - "frequency penalty": float
      Similar to the presence penalty, this reduces the model’s tendency to repeat the same words frequently. Defaults to 0.7.
"prompt": (Body parameter), object
  Instructions for the LLM to follow.
  - "similarity_threshold": float
      Threshold for similarities between the user query and chunks. Defaults to 0.2.
  - "keywords_similarity_weight": float
      Weight of keyword similarity in the hybrid similarity score. Defaults to 0.7.
  - "top_n": int
      Number of top chunks fed to the LLM. Defaults to 8.
  - "variables": object[]
      Variables to use in the 'System' field of Chat Configurations.
      - "knowledge" is a reserved variable.
      - All variables in 'System' should be curly bracketed.
      - Default: [{"key": "knowledge", "optional": true}]
  - "rerank_model": string
      If not specified, vector cosine similarity will be used; otherwise, reranking score will be used.
  - "empty_response": string
      If nothing is retrieved, this will be used as the response.
  - "opener": string
      The opening greeting for the user. Defaults to "Hi! I am your assistant, can I help you?".
  - "show_quote": boolean
      Indicates whether the source of text should be displayed. Defaults to true.
  - "prompt": string
      The prompt content.
```

----------------------------------------

TITLE: Create Session for Chat Assistant using RAGFlow SDK
DESCRIPTION: Creates a new session associated with the current chat assistant. A session can be named and returns a `Session` object with a unique ID, name, initial message, and associated chat ID. Handles potential exceptions on failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_49

LANGUAGE: APIDOC
CODE:
```
Chat.create_session(name: str = "New session") -> Session
  Creates a session with the current chat assistant.
  Parameters:
    name: str
      The name of the chat session to create.
  Returns:
    Success: A Session object containing the following attributes:
      id: str The auto-generated unique identifier of the created session.
      name: str The name of the created session.
      message: list[Message] The opening message of the created session. Default: [{"role": "assistant", "content": "Hi! I am your assistant, can I help you?"}]
      chat_id: str The ID of the associated chat assistant.
    Failure: Exception
```

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
assistant = rag_object.list_chats(name="Miss R")
assistant = assistant[0]
session = assistant.create_session()
```

----------------------------------------

TITLE: RAGFlow Docker Image Editions Reference
DESCRIPTION: This table provides a comprehensive reference for different RAGFlow Docker image tags, detailing their size, inclusion of embedding models and Python packages, and stability status. It helps users select the appropriate image based on their requirements, such as `v0.19.0-slim` for a smaller image without pre-built models or `v0.19.0` for the full edition.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/quickstart.mdx#_snippet_3

LANGUAGE: APIDOC
CODE:
```
| RAGFlow image tag | Image size (GB) | Has embedding models and Python packages? | Stable? |
| --- | --- | --- | --- |
| `v0.19.0` | &approx;9 | :heavy_check_mark: | Stable release |
| `v0.19.0-slim` | &approx;2 | ❌ | Stable release |
| `nightly` | &approx;9 | :heavy_check_mark: | *Unstable* nightly build |
| `nightly-slim` | &approx;2 | ❌ | *Unstable* nightly build |
```

----------------------------------------

TITLE: Streaming Chat Completion Response JSON
DESCRIPTION: This JSON snippet illustrates a streamed response from the chat completion API. It shows how content is delivered in chunks, with `delta` objects containing partial content and a final chunk indicating the `finish_reason` and `usage` statistics.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_3

LANGUAGE: json
CODE:
```
{
    "id": "chatcmpl-3a9c3572f29311efa69751e139332ced",
    "choices": [
        {
            "delta": {
                "content": "This is a test. If you have any specific questions or need information, feel",
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1740543996,
    "model": "model",
    "object": "chat.completion.chunk",
    "system_fingerprint": "",
    "usage": null
}
// omit duplicated information
{"choices":[{"delta":{"content":" free to ask, and I will do my best to provide an answer based on","role":"assistant"}}]}
{"choices":[{"delta":{"content":" the knowledge I have. If your question is unrelated to the provided knowledge base,","role":"assistant"}}]}
{"choices":[{"delta":{"content":" I will let you know.","role":"assistant"}}]}
// the last chunk
{
    "id": "chatcmpl-3a9c3572f29311efa69751e139332ced",
    "choices": [
        {
            "delta": {
                "content": null,
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1740543996,
    "model": "model",
    "object": "chat.completion.chunk",
    "system_fingerprint": "",
    "usage": {
        "prompt_tokens": 18,
        "completion_tokens": 225,
        "total_tokens": 243
    }
}
```

----------------------------------------

TITLE: Create Agent API: cURL Request Example
DESCRIPTION: Provides a practical cURL command demonstrating how to send a POST request to the `/api/v1/agents` endpoint, including necessary headers and a sample JSON body for agent creation.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_129

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/agents \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
         "title": "Test Agent",
         "description": "A test agent",
         "dsl": {
           // ... Canvas DSL here ...
         }
     }'
```

----------------------------------------

TITLE: List Sessions for Chat Assistant with RAGFlow SDK
DESCRIPTION: Retrieves a paginated list of sessions associated with a specific chat assistant. Supports filtering by ID or name, and sorting by creation or update time in ascending or descending order. Returns a list of `Session` objects.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_51

LANGUAGE: APIDOC
CODE:
```
Chat.list_sessions(
    page: int = 1,
    page_size: int = 30,
    orderby: str = "create_time",
    desc: bool = True,
    id: str = None,
    name: str = None
) -> list[Session]
  Lists sessions associated with the current chat assistant.
  Parameters:
    page: int
      Specifies the page on which the sessions will be displayed. Defaults to 1.
    page_size: int
      The number of sessions on each page. Defaults to 30.
    orderby: str
      The field by which sessions should be sorted. Available options:
      "create_time" (default)
      "update_time"
    desc: bool
      Indicates whether the retrieved sessions should be sorted in descending order. Defaults to True.
    id: str
      The ID of the chat session to retrieve. Defaults to None.
    name: str
      The name of the chat session to retrieve. Defaults to None.
  Returns:
    Success: A list of Session objects associated with the current chat assistant.
    Failure: Exception.
```

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
assistant = rag_object.list_chats(name="Miss R")
assistant = assistant[0]
for session in assistant.list_sessions():
    print(session)
```

----------------------------------------

TITLE: Create Agent API: Endpoint and Request Overview
DESCRIPTION: Outlines the HTTP method (POST), URL, required headers (Content-Type, Authorization), and the expected structure of the request body for creating a new agent.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_128

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/agents
Headers:
  'Content-Type: application/json
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "title": string
  "description": string
  "dsl": object
```

----------------------------------------

TITLE: Agent Completions API Request Parameters
DESCRIPTION: This section details the various parameters available for the agent completions API, including path and body parameters. It describes their types, requirements, and purpose for controlling session behavior and input.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_106

LANGUAGE: APIDOC
CODE:
```
agent_id: (Path parameter), string
  The ID of the associated agent.
"question": (Body Parameter), string, Required
  The question to start an AI-powered conversation.
"stream": (Body Parameter), boolean
  Indicates whether to output responses in a streaming way:
  true: Enable streaming (default).
  false: Disable streaming.
"session_id": (Body Parameter)
  The ID of the session. If it is not provided, a new session will be generated.
"user_id": (Body parameter), string
  The optional user-defined ID. Valid only when no session_id is provided.
"sync_dsl": (Body parameter), boolean
  Whether to synchronize the changes to existing sessions when an agent is modified, defaults to false.
Other parameters: (Body Parameter)
  Parameters specified in the Begin component.
```

----------------------------------------

TITLE: Launch RAGFlow Dependent Services via Docker Compose
DESCRIPTION: Starts essential backend services like MinIO, Elasticsearch, Redis, and MySQL using a specific Docker Compose file (`docker-compose-base.yml`) in detached mode. These services are prerequisites for RAGFlow's operation.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_15

LANGUAGE: bash
CODE:
```
docker compose -f docker/docker-compose-base.yml up -d
```

----------------------------------------

TITLE: Running Ollama Model on Linux (Bash)
DESCRIPTION: Runs the specified Ollama model (e.g., 'qwen2:latest') on Linux. This command initiates the model for inference or interaction.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_18

LANGUAGE: bash
CODE:
```
./ollama run qwen2:latest
```

----------------------------------------

TITLE: Launching Mistral Model with Xinference (Bash)
DESCRIPTION: This command launches the Mistral model (version 0.1, 7 billion parameters) using Xinference. It specifies the model format as PyTorch and requires a placeholder for the desired quantization method. This makes the model available for use by RAGFlow.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_9

LANGUAGE: bash
CODE:
```
$ xinference launch -u mistral --model-name mistral-v0.1 --size-in-billions 7 --model-format pytorch --quantization ${quantization}
```

----------------------------------------

TITLE: API Reference: Parse Documents
DESCRIPTION: Initiates the parsing process for specified documents within a dataset. This operation is a POST request requiring document IDs in the request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_42

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/datasets/{dataset_id}/chunks
Headers:
  Content-Type: application/json
  Authorization: Bearer <YOUR_API_KEY>
Body:
  "document_ids": list[string]
Request Parameters:
  dataset_id (Path parameter): The dataset ID.
  "document_ids" (Body parameter, list[string], Required): The IDs of the documents to parse.
```

----------------------------------------

TITLE: OAuth Authentication Configuration
DESCRIPTION: Configures OAuth settings for integrating third-party authentication providers for user sign-up and sign-in. It supports custom channels with various authentication types (oauth2, oidc, github) and requires specific client and URL parameters.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_13

LANGUAGE: APIDOC
CODE:
```
oauth:
  <channel>: Custom channel ID.
    type: Authentication type, options include oauth2, oidc, github. Default is oauth2, when issuer parameter is provided, defaults to oidc.
    icon: Icon ID, options include github, sso, default is sso.
    display_name: Channel name, defaults to the Title Case format of the channel ID.
    client_id: Required, unique identifier assigned to the client application.
    client_secret: Required, secret key for the client application, used for communication with the authentication server.
    authorization_url: Base URL for obtaining user authorization.
    token_url: URL for exchanging authorization code and obtaining access token.
    userinfo_url: URL for obtaining user information (username, email, etc.).
    issuer: Base URL of the identity provider. OIDC clients can dynamically obtain the identity provider's metadata (authorization_url, token_url, userinfo_url) through issuer.
    scope: Requested permission scope, a space-separated string. For example, openid profile email.
    redirect_uri: Required, URI to which the authorization server redirects during the authentication flow to return results. Must match the callback URI registered with the authentication server. Format: https://your-app.com/v1/user/oauth/callback/<channel>. For local configuration, you can directly use http://127.0.0.1:80/v1/user/oauth/callback/<channel>.
```

----------------------------------------

TITLE: API: Create RAGFlow Agent
DESCRIPTION: Documents the `RAGFlow.create_agent` method, used to create a new agent. It specifies required parameters such as title and DSL, and an optional description.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_67

LANGUAGE: APIDOC
CODE:
```
RAGFlow.create_agent(
    title: str,
    dsl: dict,
    description: str | None = None
) -> None
Parameters:
```

----------------------------------------

TITLE: Deploying Ollama with Docker
DESCRIPTION: This command deploys the Ollama server as a Docker container, mapping port 11434 from the container to the host. The output indicates Ollama is listening on the specified port and has loaded dynamic LLM libraries, confirming successful initialization.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_0

LANGUAGE: bash
CODE:
```
$ sudo docker run --name ollama -p 11434:11434 ollama/ollama
> time=2024-12-02T02:20:21.360Z level=INFO source=routes.go:1248 msg="Listening on [::]:11434 (version 0.4.6)"
> time=2024-12-02T02:20:21.360Z level=INFO source=common.go:49 msg="Dynamic LLM libraries" runners="[cpu cpu_avx cpu_avx2 cuda_v11 cuda_v12]"
```

----------------------------------------

TITLE: Example: Create RAGFlow Dataset
DESCRIPTION: Illustrates how to initialize the RAGFlow SDK with an API key and base URL, then create a new dataset using the `create_dataset` method with a specified name. This is a fundamental step for managing knowledge bases.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_5

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.create_dataset(name="kb_1")
```

----------------------------------------

TITLE: Clone RAGFlow Repository and Checkout Version
DESCRIPTION: These commands clone the RAGFlow repository from GitHub, navigate into the `docker` subdirectory, and then check out a specific version (v0.19.0) of the project.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/quickstart.mdx#_snippet_1

LANGUAGE: bash
CODE:
```
$ git clone https://github.com/infiniflow/ragflow.git
$ cd ragflow/docker
$ git checkout -f v0.19.0
```

----------------------------------------

TITLE: Document.add_chunk API Reference
DESCRIPTION: API documentation for adding a chunk to a document. It details the `content` and `important_keywords` parameters, the `Chunk` object return type, and its attributes like ID, content, keywords, and availability status.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_29

LANGUAGE: APIDOC
CODE:
```
Document.add_chunk(content:str, important_keywords:list[str] = []) -> Chunk

Parameters:
  content: `str`, *Required*
    The text content of the chunk.
  important_keywords: `list[str]`
    The key terms or phrases to tag with the chunk.

Returns:
  Success: A `Chunk` object.
  Failure: `Exception`.

Chunk object attributes:
  id: `str`: The chunk ID.
  content: `str` The text content of the chunk.
  important_keywords: `list[str]` A list of key terms or phrases tagged with the chunk.
  create_time: `str` The time when the chunk was created (added to the document).
  create_timestamp: `float` The timestamp representing the creation time of the chunk, expressed in seconds since January 1, 1970.
  dataset_id: `str` The ID of the associated dataset.
  document_name: `str` The name of the associated document.
  document_id: `str` The ID of the associated document.
  available: `bool` The chunk's availability status in the dataset. Value options:
    False: Unavailable
    True: Available (default)
```

----------------------------------------

TITLE: Install RAGFlow Python SDK
DESCRIPTION: Instructions for installing the RAGFlow Python SDK using pip, specifying version 0.13.0. This command ensures the correct SDK version is downloaded and installed.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/release_notes.md#_snippet_7

LANGUAGE: bash
CODE:
```
pip install ragflow-sdk==0.13.0
```

----------------------------------------

TITLE: APIDOC: List Chat Assistants Method
DESCRIPTION: API documentation for the `RAGFlow.list_chats` method, enabling retrieval of chat assistants with pagination, sorting, and filtering options. Results can be ordered by creation or update time, and filtered by ID or name.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_47

LANGUAGE: APIDOC
CODE:
```
RAGFlow.list_chats(
    page: int = 1,
    page_size: int = 30,
    orderby: str = "create_time",
    desc: bool = True,
    id: str = None,
    name: str = None
) -> list[Chat]
Parameters:
  page: int - Specifies the page on which the chat assistants will be displayed. Defaults to 1.
  page_size: int - The number of chat assistants on each page. Defaults to 30.
  orderby: str - The attribute by which the results are sorted. Available options: "create_time" (default), "update_time".
  desc: bool - Indicates whether the retrieved chat assistants should be sorted in descending order. Defaults to True.
  id: str - The ID of the chat assistant to retrieve. Defaults to None.
  name: str - The name of the chat assistant to retrieve. Defaults to None.
```

----------------------------------------

TITLE: Update RAGFlow Agent
DESCRIPTION: This snippet demonstrates how to update an existing agent using its ID. You can modify the agent's title, description, or DSL. Parameters can be set to `None` if no update is desired for that specific field. The operation returns nothing on success and an Exception on failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_69

LANGUAGE: APIDOC
CODE:
```
RAGFlow.update_agent(
  agent_id: str,
  title: str | None = None,
  description: str | None = None,
  dsl: dict | None = None
) -> None

Parameters:
  agent_id: str - Specifies the id of the agent to be updated.
  title: str - Specifies the new title of the agent. None if you do not want to update this.
  dsl: dict - Specifies the new canvas DSL of the agent. None if you do not want to update this.
  description: str - The new description of the agent. None if you do not want to update this.

Returns:
  Success: Nothing.
  Failure: Exception.
```

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow
rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
rag_object.update_agent(
  agent_id="58af890a2a8911f0a71a11b922ed82d6",
  title="Test Agent",
  description="A test agent",
  dsl={
    # ... canvas DSL here ...
  }
)
```

----------------------------------------

TITLE: Restart RAGFlow Server After Configuration Changes
DESCRIPTION: After modifying configuration files, such as increasing the MEM_LIMIT in docker/.env, these commands are necessary to stop and then restart the RAGFlow server for the changes to take effect.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/faq.mdx#_snippet_7

LANGUAGE: bash
CODE:
```
docker compose stop
```

LANGUAGE: bash
CODE:
```
docker compose up -d
```

----------------------------------------

TITLE: Implementing Invoke Method for LLM Tool in Python
DESCRIPTION: This snippet implements the `invoke` method for the `BadCalculatorPlugin`. This method is called by the LLM, accepts parameters (`a` and `b` in this case), and must return a string containing the tool's execution result. Here, it intentionally returns an incorrect sum.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/plugin/README.md#_snippet_1

LANGUAGE: Python
CODE:
```
def invoke(self, a: int, b: int) -> str:
    return str(a + b + 100)
```

----------------------------------------

TITLE: API Reference: Chat Completions Request Parameters
DESCRIPTION: Describes the parameters used in the chat completions API request, including path and body parameters. It clarifies their types, requirements, and purpose, such as `chat_id`, `question`, `stream`, `session_id`, and `user_id`.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_88

LANGUAGE: APIDOC
CODE:
```
chat_id: (Path parameter)
  The ID of the associated chat assistant.
"question": (Body Parameter), string, Required
  The question to start an AI-powered conversation.
"stream": (Body Parameter), boolean
  Indicates whether to output responses in a streaming way:
  true: Enable streaming (default).
  false: Disable streaming.
"session_id": (Body Parameter)
  The ID of session. If it is not provided, a new session will be generated.
"user_id": (Body parameter), string
  The optional user-defined ID. Valid only when no session_id is provided.
```

----------------------------------------

TITLE: Check RAGFlow Server Logs
DESCRIPTION: This command retrieves and displays the real-time logs for the `ragflow-server` Docker container. It is essential for monitoring the server's operational status, diagnosing issues, and observing the startup sequence and ongoing activities of both RAGFlow and the integrated MCP server.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/mcp/launch_mcp_server.md#_snippet_4

LANGUAGE: bash
CODE:
```
docker logs ragflow-server
```

----------------------------------------

TITLE: RAGFlow Server Successful Launch Confirmation Output
DESCRIPTION: This snippet displays the expected console output confirming that the RAGFlow server has successfully launched and is running. The `* Running on all addresses (0.0.0.0)` line indicates that the server is accessible and ready for use.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/quickstart.mdx#_snippet_5

LANGUAGE: bash
CODE:
```
     ____   ___    ______ ______ __
    / __ \ /   |  / ____// ____// /____  _      __
   / /_/ // /| | / / __ / /_   / // __ \| | /| / /
  / _, _// ___ |/ /_/ // __/  / // /_/ /| |/ |/ /
 /_/ |_|/_/  |_|\____//_/    /_/ \____/ |__/|__/

 * Running on all addresses (0.0.0.0)
```

----------------------------------------

TITLE: Update Chunk Content Example
DESCRIPTION: Python example showing how to initialize RAGFlow, retrieve a dataset and document, add a chunk, and then update its content using the `update` method with a dictionary.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_36

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.list_datasets(id="123")
dataset = dataset[0]
doc = dataset.list_documents(id="wdfxb5t547d")
doc = doc[0]
chunk = doc.add_chunk(content="xxxxxxx")
chunk.update({"content":"sdfx..."})
```

----------------------------------------

TITLE: Verifying Ollama Accessibility from Remote Machine
DESCRIPTION: This command uses `curl` to verify if the Ollama server is accessible from a different host machine (where RAGFlow might be running) by specifying the IP address of the Ollama machine on port 11434. The expected output confirms Ollama is running.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_6

LANGUAGE: bash
CODE:
```
$ curl http://${IP_OF_OLLAMA_MACHINE}:11434/
> Ollama is running
```

----------------------------------------

TITLE: Create Agent Session (No Begin Parameters)
DESCRIPTION: This `curl` command demonstrates how to initiate a new session with the agent completions API when the 'Begin' component does not require any initial parameters. It sends an empty JSON body to the specified endpoint.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_103

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/agents/{agent_id}/completions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data-binary '\n     {\n     }'
```

----------------------------------------

TITLE: Delete Datasets API Endpoint Definition
DESCRIPTION: Defines the HTTP DELETE endpoint for deleting one or more datasets by their IDs. Specifies the method, URL, required headers, and the body parameter for dataset IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_16

LANGUAGE: APIDOC
CODE:
```
Endpoint: DELETE /api/v1/datasets
Description: Deletes datasets by ID.
Request Details:
- Method: DELETE
- URL: /api/v1/datasets
- Headers:
  - 'Content-Type: application/json'
  - 'Authorization: Bearer <YOUR_API_KEY>'
- Body Parameters:
  - "ids": list[string] or null
```

----------------------------------------

TITLE: List Chat Assistant Sessions
DESCRIPTION: Retrieves a paginated list of sessions associated with a specified chat assistant. This endpoint supports various filtering and sorting options based on session properties.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_84

LANGUAGE: APIDOC
CODE:
```
Method: GET
URL: /api/v1/chats/{chat_id}/sessions?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={session_name}&id={session_id}&user_id={user_id}
Headers:
  'Authorization: Bearer <YOUR_API_KEY>'
Parameters:
  Path:
    chat_id: The ID of the associated chat assistant.
  Filter:
    page: integer - Specifies the page on which the sessions will be displayed. Defaults to 1.
    page_size: integer - The number of sessions on each page. Defaults to 30.
    orderby: string - The field by which sessions should be sorted. Options: create_time (default), update_time.
    desc: boolean - Indicates whether the retrieved sessions should be sorted in descending order. Defaults to true.
    name: string - The name of the chat session to retrieve.
    id: string - The ID of the chat session to retrieve.
    user_id: string - The optional user-defined ID passed in when creating session.
```

LANGUAGE: bash
CODE:
```
curl --request GET \
     --url http://{address}/api/v1/chats/{chat_id}/sessions?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={session_name}&id={session_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": [
        {
            "chat": "2ca4b22e878011ef88fe0242ac120005",
            "create_date": "Fri, 11 Oct 2024 08:46:43 GMT",
            "create_time": 1728636403974,
            "id": "578d541e87ad11ef96b90242ac120006",
            "messages": [
                {
                    "content": "Hi! I am your assistant, can I help you?",
                    "role": "assistant"
                }
            ],
            "name": "new session",
            "update_date": "Fri, 11 Oct 2024 08:46:43 GMT",
            "update_time": 1728636403974
        }
    ]
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "The session doesn't exist"
}
```

----------------------------------------

TITLE: List and Retrieve Datasets in RAGFlow (Python)
DESCRIPTION: Python examples demonstrating how to list all datasets and how to retrieve a specific dataset by its ID using the `list_datasets` method.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_10

LANGUAGE: python
CODE:
```
for dataset in rag_object.list_datasets():
    print(dataset)
```

LANGUAGE: python
CODE:
```
dataset = rag_object.list_datasets(id = "id_1")
print(dataset[0])
```

----------------------------------------

TITLE: API Reference: Create Session with Agent
DESCRIPTION: Documents the API endpoint for creating a new session associated with a specific agent. This POST request is used to initialize a new interaction context for an agent.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_94

LANGUAGE: APIDOC
CODE:
```
POST /api/v1/agents/{agent_id}/sessions
Creates a session with an agent.
```

----------------------------------------

TITLE: RAGFlow Chat.update Method
DESCRIPTION: Documents the `Chat.update` method, which is used to modify the configurations of an existing chat assistant. It takes a dictionary of update messages as a parameter.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_42

LANGUAGE: APIDOC
CODE:
```
Chat.update(update_message: dict)
Parameters:
```

----------------------------------------

TITLE: Non-Streaming Chat Completion Response JSON
DESCRIPTION: This JSON snippet demonstrates a complete, non-streamed response from the chat completion API. It includes the full generated content, finish reason, and usage statistics within a single JSON object, suitable for applications that do not require real-time content delivery.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_4

LANGUAGE: json
CODE:
```
{
    "choices":[
        {
            "finish_reason":"stop",
            "index":0,
            "logprobs":null,
            "message":{
                "content":"This is a test. If you have any specific questions or need information, feel free to ask, and I will do my best to provide an answer based on the knowledge I have. If your question is unrelated to the provided knowledge base, I will let you know.",
                "role":"assistant"
            }
        }
    ],
    "created":1740543499,
    "id":"chatcmpl-3a9c3572f29311efa69751e139332ced",
    "model":"model",
    "object":"chat.completion",
    "usage":{
        "completion_tokens":246,
        "completion_tokens_details":{
            "accepted_prediction_tokens":246,
            "reasoning_tokens":18,
            "rejected_prediction_tokens":0
        },
        "prompt_tokens":18,
        "total_tokens":264
    }
}
```

----------------------------------------

TITLE: JSON Response: Successful Chat without Session ID or Begin Parameters
DESCRIPTION: This JSON snippet shows a successful response from a chat interaction where no session ID was provided and no parameters were specified in the 'Begin' component. It returns an initial greeting, a new session ID, and an empty reference object, followed by a final success indicator.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_107

LANGUAGE: json
CODE:
```
data:{
    "code": 0,
    "message": "",
    "data": {
        "answer": "Hi! I'm your smart assistant. What can I do for you?",
        "reference": {},
        "id": "31e6091d-88d4-441b-ac65-eae1c055be7b",
        "session_id": "2987ad3eb85f11efb2a70242ac120005"
    }
}
data:{
    "code": 0,
    "message": "",
    "data": true
}
```

----------------------------------------

TITLE: Create Chunk in Ragflow Document (POST)
DESCRIPTION: This API endpoint allows you to add new text chunks to a specific document within a dataset. It requires content and can optionally include important keywords and questions for embedding.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_51

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks
Headers:
  'content-Type: application/json'
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "content": string
  "important_keywords": list[string]
  "questions": list[string]

Request parameters:
- dataset_id: (Path parameter) The associated dataset ID.
- document_ids: (Path parameter) The associated document ID.
- "content": (Body parameter), string, Required. The text content of the chunk.
- "important_keywords": (Body parameter), list[string]. The key terms or phrases to tag with the chunk.
- "questions": (Body parameter), list[string]. If there is a given question, the embedded chunks will be based on them.
```

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "content": "<CHUNK_CONTENT_HERE>"
     }'
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "chunk": {
            "content": "who are you",
            "create_time": "2024-12-30 16:59:55",
            "create_timestamp": 1735549195.969164,
            "dataset_id": "72f36e1ebdf411efb7250242ac120006",
            "document_id": "61d68474be0111ef98dd0242ac120006",
            "id": "12ccdc56e59837e5",
            "important_keywords": [],
            "questions": []
        }
    }
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "`content` is required"
}
```

----------------------------------------

TITLE: Example User Query for Agent Debugging
DESCRIPTION: This snippet represents a natural language query provided as input to the Ragflow Agent during the debugging process. It's used to test the agent's ability to process user questions, identify relevant information, and generate appropriate SQL queries, even when direct matches are not immediately found, prompting adjustments to reranking models or similarity thresholds.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/text2sql_agent.md#_snippet_11

LANGUAGE: Natural Language
CODE:
```
Find all customers who has bought a mobile phone
```

----------------------------------------

TITLE: Python: Update RagFlow Document Attributes
DESCRIPTION: Demonstrates how to update a document's `parser_config` and `chunk_method` using the RagFlow SDK. It initializes the SDK, retrieves a dataset and a specific document, then calls the `update` method with the desired changes.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_17

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.list_datasets(id='id')
dataset = dataset[0]
doc = dataset.list_documents(id="wdfxb5t547d")
doc = doc[0]
doc.update([{"parser_config": {"chunk_token_count": 256}}, {"chunk_method": "manual"}])
```

----------------------------------------

TITLE: List Documents API Request Parameters
DESCRIPTION: Details the path and filter parameters required for listing documents, including pagination, sorting, and filtering options.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_35

LANGUAGE: APIDOC
CODE:
```
Request parameters:
- `dataset_id`: (Path parameter)
  The associated dataset ID.
- `keywords`: (Filter parameter), `string`
  The keywords used to match document titles.
- `page`: (Filter parameter), `integer`
  Specifies the page on which the documents will be displayed. Defaults to `1`.
- `page_size`: (Filter parameter), `integer`
  The maximum number of documents on each page. Defaults to `30`.
- `orderby`: (Filter parameter), `string`
  The field by which documents should be sorted. Available options:
  - `create_time` (default)
  - `update_time`
- `desc`: (Filter parameter), `boolean`
  Indicates whether the retrieved documents should be sorted in descending order. Defaults to `true`.
- `id`: (Filter parameter), `string`
  The ID of the document to retrieve.
```

----------------------------------------

TITLE: APIDOC: Dataset List Documents Method
DESCRIPTION: Defines the `Dataset.list_documents()` method for retrieving documents within a dataset. It supports filtering by ID or keywords, pagination, and sorting by creation or update time.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_20

LANGUAGE: APIDOC
CODE:
```
Dataset.list_documents(id:str =None, keywords: str=None, page: int=1, page_size:int = 30, order_by:str = "create_time", desc: bool = True) -> list[Document]

Lists documents in the current dataset.

Parameters:
- id: str
  The ID of the document to retrieve. Defaults to None.
- keywords: str
  The keywords used to match document titles. Defaults to None.
- page: int
  Specifies the page on which the documents will be displayed. Defaults to 1.
- page_size: int
  The maximum number of documents on each page. Defaults to 30.
- orderby: str
  The field by which documents should be sorted. Available options:
  - "create_time" (default)
  - "update_time"
- desc: bool
  Indicates whether the retrieved documents should be sorted in descending order. Defaults to True.
```

----------------------------------------

TITLE: Starting RAGFlow Containers (Docker Compose)
DESCRIPTION: This command starts the Docker containers defined in `docker-compose.yml` in detached mode (`-d`). This is used to bring up the RAGFlow services after the `DOC_ENGINE` has been configured to Infinity.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/switch_doc_engine.md#_snippet_1

LANGUAGE: bash
CODE:
```
docker compose -f docker-compose.yml up -d
```

----------------------------------------

TITLE: Retrieve Chunks API Endpoint
DESCRIPTION: Retrieves relevant chunks from specified datasets based on a question and optional filters. Allows pagination, similarity thresholds, and keyword highlighting. Requires authentication and a question in the request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_56

LANGUAGE: APIDOC
CODE:
```
API Endpoint: POST /api/v1/retrieval
Description: Retrieves chunks from specified datasets.
Headers:
  - 'Content-Type: application/json'
  - 'Authorization: Bearer <YOUR_API_KEY>'
Body Parameters:
  - question: string
  - dataset_ids: list[string]
  - document_ids: list[string]
  - page: integer
  - page_size: integer
  - similarity_threshold: float
  - vector_similarity_weight: float
  - top_k: integer
  - rerank_id: string
  - keyword: boolean
  - highlight: boolean
```

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/retrieval \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "question": "What is advantage of ragflow?",
          "dataset_ids": ["b2a62730759d11ef987d0242ac120004"],
          "document_ids": ["77df9ef4759a11ef8bdd0242ac120004"]
     }'
```

----------------------------------------

TITLE: Verifying Ollama Accessibility from Localhost
DESCRIPTION: This command uses `curl` to check if the Ollama server is accessible from the local machine (where RAGFlow is launched from source code) via `localhost` on port 11434. The expected output confirms Ollama is running, indicating a successful connection.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_5

LANGUAGE: bash
CODE:
```
$ curl http://localhost:11434/
> Ollama is running
```

----------------------------------------

TITLE: Create RAGFlow Chat Assistant in Python
DESCRIPTION: This Python example demonstrates how to initialize the RAGFlow SDK, list existing datasets, and create a new chat assistant associated with specific datasets using their IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_41

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
datasets = rag_object.list_datasets(name="kb_1")
dataset_ids = []
for dataset in datasets:
    dataset_ids.append(dataset.id)
assistant = rag_object.create_chat("Miss R", dataset_ids=dataset_ids)
```

----------------------------------------

TITLE: Installing RAGFlow Python Dependencies (Slim) - Bash
DESCRIPTION: This command uses 'uv' to synchronize and install the core Python dependencies for RAGFlow, targeting Python 3.10. It creates a virtual environment named `.venv` if it doesn't exist.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_2

LANGUAGE: bash
CODE:
```
uv sync --python 3.10
```

----------------------------------------

TITLE: Example: Create RAGFlow Chat Completion with cURL
DESCRIPTION: An example cURL command demonstrating how to make a POST request to the RAGFlow OpenAI-compatible chat completion endpoint. It includes the required headers for content type and authorization, along with a JSON body specifying the model, messages, and streaming preference.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_2

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/chats_openai/{chat_id}/chat/completions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
        "model": "model",
        "messages": [{"role": "user", "content": "Say this is a test!"}],
        "stream": true
      }'
```

----------------------------------------

TITLE: DataSet.upload_documents API Reference
DESCRIPTION: API reference for uploading documents to a dataset. Describes the `document_list` parameter, which is a list of dictionaries containing `display_name` and `blob`.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_13

LANGUAGE: APIDOC
CODE:
```
DataSet.upload_documents(document_list: list[dict])
Parameters:
  document_list: `list[dict]`, *Required* - A list of dictionaries representing the documents to upload, each containing the following keys:
    - `"display_name"`: (Optional) The file name to display in the dataset.
    - `"blob"`: (Optional) The binary content of the file to upload.
Returns:
- Success: No value is returned.
- Failure: `Exception`
```

----------------------------------------

TITLE: Launching RAGFlow Service on MacOS with Docker Compose (Bash)
DESCRIPTION: This snippet provides Bash commands to navigate into the `docker` directory and launch the RAGFlow service using Docker Compose on MacOS. It assumes the `RAGFLOW_IMAGE` in `docker/.env` has been updated to `infiniflow/ragflow:nightly-slim` and will bring up all required components like Elasticsearch, MySQL, MinIO, and Redis.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/build_docker_image.mdx#_snippet_2

LANGUAGE: bash
CODE:
```
cd docker
$ docker compose -f docker-compose-macos.yml up -d
```

----------------------------------------

TITLE: Cloning RAGFlow Repository - Bash
DESCRIPTION: This command clones the RAGFlow Git repository from GitHub and then changes the current directory into the newly cloned 'ragflow' directory, preparing for further setup.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_0

LANGUAGE: bash
CODE:
```
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/
```

----------------------------------------

TITLE: Example Failure JSON Response for Agent Conversation
DESCRIPTION: This JSON object illustrates a typical failure response from the agent conversation API. It provides an error code and a descriptive message, such as 'Agent not found', to indicate the reason for the failed request.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_101

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "Agent not found."
}
```

----------------------------------------

TITLE: Connection Refused Error Example
DESCRIPTION: This snippet shows a common error message indicating that RAGFlow failed to establish a connection to the Ollama server's chat API. This typically occurs due to incorrect base URL settings, network issues, or Ollama not running or being inaccessible, requiring troubleshooting of the connection parameters.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_7

LANGUAGE: bash
CODE:
```
Max retries exceeded with url: /api/chat (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0xffff98b81ff0>: Failed to establish a new connection: [Errno 111] Connection refused'))
```

----------------------------------------

TITLE: Create Agent API: Failure Response JSON Example
DESCRIPTION: Illustrates the JSON response for a failed agent creation, typically due to a conflict like an agent with the same title already existing.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_132

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "Agent with title test already exists."
}
```

----------------------------------------

TITLE: Exchanging Authorization Code for Access Token in Python
DESCRIPTION: After a user authorizes the application, the identity provider redirects back with an authorization code. This snippet demonstrates how to exchange this code for an access token using the client, which is then used for subsequent API calls.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/api/apps/auth/README.md#_snippet_2

LANGUAGE: python
CODE:
```
token_response = client.exchange_code_for_token(authorization_code)
access_token = token_response["access_token"]
```

----------------------------------------

TITLE: Calling RAGFlow Chat API with Custom Variables using cURL
DESCRIPTION: This cURL command demonstrates how to interact with the RAGFlow chat assistant API, passing values for custom variables like `style`. It shows a POST request to the `/api/v1/chats/{chat_id}/completions` endpoint, including necessary headers and a JSON payload with the question and the `style` variable's value.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/chat/set_chat_variables.md#_snippet_1

LANGUAGE: Shell
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/chats/{chat_id}/completions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data-binary '
     {
          "question": "xxxxxxxxx",
          "stream": true,
          "style":"hilarious"
     }'
```

----------------------------------------

TITLE: Rebooting RAGFlow Docker Containers
DESCRIPTION: This command reboots all RAGFlow Docker containers defined in the `docker/docker-compose.yml` file. It is crucial to execute this command after any configuration modifications (e.g., in `.env` or `service_conf.yaml.template`) to ensure that the changes are applied. The `-d` flag runs the containers in detached mode, allowing them to operate in the background.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/configurations.md#_snippet_0

LANGUAGE: bash
CODE:
```
docker compose -f docker/docker-compose.yml up -d
```

----------------------------------------

TITLE: Python: List Agent Sessions Example
DESCRIPTION: Provides a Python example for using the `Agent.list_sessions` method to retrieve and print all sessions associated with a given agent. It initializes the RAGFlow SDK and fetches an agent by ID.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_62

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
AGENT_id = "AGENT_ID"
agent = rag_object.list_agents(id = AGENT_id)[0]
sessons = agent.list_sessions()
for session in sessons:
    print(session)
```

----------------------------------------

TITLE: Execute Agent Completion Process
DESCRIPTION: This `curl` command shows how to execute the completion process for an existing agent session. It sends a question, specifies streaming behavior, and includes the session ID to continue the conversation.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_105

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/agents/{agent_id}/completions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data-binary '\n     {\n          "question": "Hello",\n          "stream": true,\n          "session_id": "cb2f385cb86211efa36e0242ac120005"\n     }'
```

----------------------------------------

TITLE: Running RAGFlow Backend API Server - Python
DESCRIPTION: This command starts the main RAGFlow backend API server. It executes `ragflow_server.py`, which handles API requests and orchestrates the RAGFlow functionalities.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_10

LANGUAGE: python
CODE:
```
python api/ragflow_server.py;
```

----------------------------------------

TITLE: Chat Completion Non-Stream Response Example
DESCRIPTION: Shows the complete JSON response for a non-streaming chat completion. The full content is provided in a single 'message' object, along with usage statistics and other metadata.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_9

LANGUAGE: json
CODE:
```
{
    "choices":[
        {
            "finish_reason":"stop",
            "index":0,
            "logprobs":null,
            "message":{
                "content":"This is a test. If you have any specific questions or need information, feel free to ask, and I will do my best to provide an answer based on the knowledge I have. If your question is unrelated to the provided knowledge base, I will let you know.",
                "role":"assistant"
            }
        }
    ],
    "created":1740543499,
    "id":"chatcmpl-3a9c3572f29311efa69751e139332ced",
    "model":"model",
    "object":"chat.completion",
    "usage":{
        "completion_tokens":246,
        "completion_tokens_details":{
            "accepted_prediction_tokens":246,
            "reasoning_tokens":18,
            "rejected_prediction_tokens":0
        },
        "prompt_tokens":18,
        "total_tokens":264
    }
}
```

----------------------------------------

TITLE: Python: Delete Specific Documents from RagFlow Dataset
DESCRIPTION: Illustrates how to use the `delete_documents` method to remove specific documents from an existing dataset by providing a list of their IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_24

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.list_datasets(name="kb_1")
dataset = dataset[0]
dataset.delete_documents(ids=["id_1","id_2"])
```

----------------------------------------

TITLE: Standard User Information Structure in Python
DESCRIPTION: This snippet defines the standardized dictionary structure for user information returned by all authentication methods. It includes common fields such as email, username, nickname, and a URL for the user's avatar.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/api/apps/auth/README.md#_snippet_4

LANGUAGE: python
CODE:
```
{
    "email": "user@example.com",
    "username": "username",
    "nickname": "User Name",
    "avatar_url": "https://example.com/avatar.jpg"
}
```

----------------------------------------

TITLE: cURL Example: Generate Related Questions
DESCRIPTION: A cURL command example demonstrating how to send a POST request to the /v1/sessions/related_questions endpoint, providing an original user question to generate related queries.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_120

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/v1/sessions/related_questions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_LOGIN_TOKEN>' \
     --data '
     {
          "question": "What are the key advantages of Neovim over Vim?"
     }'
```

----------------------------------------

TITLE: Example: Chat Completions Streaming Success Response (With Session ID)
DESCRIPTION: Presents multiple JSON objects representing a streaming response from the chat completions API when an existing session ID is used. Each object shows incremental parts of the answer, along with references and session details, demonstrating how streaming data is delivered.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_92

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "answer": "I am an intelligent assistant designed to help answer questions by summarizing content from a",
        "reference": {},
        "audio_binary": null,
        "id": "a84c5dd4-97b4-4624-8c3b-974012c8000d",
        "session_id": "82b0ab2a9c1911ef9d870242ac120006"
    }
}
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "answer": "I am an intelligent assistant designed to help answer questions by summarizing content from a knowledge base. My responses are based on the information available in the knowledge base and",
        "reference": {},
        "audio_binary": null,
        "id": "a84c5dd4-97b4-4624-8c3b-974012c8000d",
        "session_id": "82b0ab2a9c1911ef9d870242ac120006"
    }
}
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "answer": "I am an intelligent assistant designed to help answer questions by summarizing content from a knowledge base. My responses are based on the information available in the knowledge base and any relevant chat history.",
        "reference": {},
        "audio_binary": null,
        "id": "a84c5dd4-97b4-4624-8c3b-974012c8000d",
        "session_id": "82b0ab2a9c1911ef9d870242ac120006"
    }
}
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "answer": "I am an intelligent assistant designed to help answer questions by summarizing content from a knowledge base ##0$$. My responses are based on the information available in the knowledge base and any relevant chat history.",
        "reference": {
            "total": 1,
            "chunks": [
                {
                    "id": "faf26c791128f2d5e821f822671063bd",
                    "content": "xxxxxxxx",
                    "document_id": "dd58f58e888511ef89c90242ac120006",
                    "document_name": "1.txt",
                    "dataset_id": "8e83e57a884611ef9d760242ac120006",
                    "image_id": "",
                    "similarity": 0.7,
                    "vector_similarity": 0.0,
                    "term_similarity": 1.0,
                    "positions": [
                        ""
                    ]
                }
            ],
            "doc_aggs": [
                {
                    "doc_name": "1.txt",
                    "doc_id": "dd58f58e888511ef89c90242ac120006",
                    "count": 1
                }
            ]
        },
        "prompt": "xxxxxxxxxxx",
        "id": "a84c5dd4-97b4-4624-8c3b-974012c8000d",
        "session_id": "82b0ab2a9c1911ef9d870242ac120006"
    }
}
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": true
}
```

----------------------------------------

TITLE: General Docker Environment Variables
DESCRIPTION: Defines general environment variables for the Docker environment, including timezone, Hugging Face mirror site configuration, macOS optimizations, and the maximum allowed file size for uploads.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_7

LANGUAGE: APIDOC
CODE:
```
TIMEZONE:
  Description: "The local time zone."
  Default: "'Asia/Shanghai'"
HF_ENDPOINT:
  Description: "The mirror site for huggingface.co. Disabled by default; uncomment to enable if primary domain access is limited."
MACOS:
  Description: "Optimizations for macOS. Disabled by default; uncomment to enable if OS is macOS."
MAX_CONTENT_LENGTH:
  Description: "The maximum file size for each uploaded file, in bytes. Uncomment to change the 128M default limit. Requires updating 'client_max_body_size' in nginx/nginx.conf correspondingly."
```

----------------------------------------

TITLE: DataSet.update API Reference
DESCRIPTION: API reference for updating configurations of an existing dataset. Details the `update_message` dictionary with various attributes like name, avatar, embedding model, permission, pagerank, and chunking method.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_11

LANGUAGE: APIDOC
CODE:
```
DataSet.update(update_message: dict)
Parameters:
  update_message: `dict[str, str|int]`, *Required* - A dictionary representing the attributes to update, with the following keys:
    - `"name"`: `str` The revised name of the dataset.
      - Basic Multilingual Plane (BMP) only
      - Maximum 128 characters
      - Case-insensitive
    - `"avatar"`: (*Body parameter*), `string` - The updated base64 encoding of the avatar.
      - Maximum 65535 characters
    - `"embedding_model"`: (*Body parameter*), `string` - The updated embedding model name.
      - Ensure that `"chunk_count"` is `0` before updating `"embedding_model"`.
      - Maximum 255 characters
      - Must follow `model_name@model_factory` format
    - `"permission"`: (*Body parameter*), `string` - The updated dataset permission. Available options:
      - `"me"`: (Default) Only you can manage the dataset.
      - `"team"`: All team members can manage the dataset.
    - `"pagerank"`: (*Body parameter*), `int` - refer to [Set page rank](https://ragflow.io/docs/dev/set_page_rank)
      - Default: `0`
      - Minimum: `0`
      - Maximum: `100`
    - `"chunk_method"`: (*Body parameter*), `enum<string>` - The chunking method for the dataset. Available options:
      - `"naive"`: General (default)
      - `"book"`: Book
      - `"email"`: Email
      - `"laws"`: Laws
      - `"manual"`: Manual
      - `"one"`: One
      - `"paper"`: Paper
      - `"picture"`: Picture
      - `"presentation"`: Presentation
      - `"qa"`: Q&A
      - `"table"`: Table
      - `"tag"`: Tag
Returns:
- Success: No value is returned.
- Failure: `Exception`
```

----------------------------------------

TITLE: List Agents API: Failure Response JSON Example
DESCRIPTION: Shows the JSON structure for an unsuccessful agent retrieval, typically indicating that no agents matched the criteria or an internal error occurred.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_127

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "The agent doesn't exist."
}
```

----------------------------------------

TITLE: Updating Orders Total Price - SQL
DESCRIPTION: This SQL query updates the 'TotalPrice' column in the 'Orders' table. It joins 'Orders' with a subquery that calculates the sum of 'TotalPrice' for each 'OrderID' from the 'OrderDetails' table. The 'TotalPrice' in the 'Orders' table is then set to the aggregated total from its corresponding order details, ensuring consistency.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/text2sql_agent.md#_snippet_3

LANGUAGE: SQL
CODE:
```
UPDATE Orders o
JOIN (
    SELECT OrderID, SUM(TotalPrice) as order_total
    FROM OrderDetails
    GROUP BY OrderID
) od ON o.OrderID = od.OrderID
SET o.TotalPrice = od.order_total;
```

----------------------------------------

TITLE: List Chunks in Document Example
DESCRIPTION: Python example showing how to initialize RAGFlow, retrieve a dataset and documents, and then list and iterate through chunks within a specific document, filtered by keywords and pagination.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_32

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.list_datasets("123")
dataset = dataset[0]
docs = dataset.list_documents(keywords="test", page=1, page_size=12)
for chunk in docs[0].list_chunks(keywords="rag", page=0, page_size=12):
    print(chunk)
```

----------------------------------------

TITLE: Starting RAGFlow Frontend Development Server - Bash
DESCRIPTION: This command initiates the RAGFlow frontend development server. `npm run dev` typically starts a local server with hot-reloading, allowing developers to view changes in real-time.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_12

LANGUAGE: bash
CODE:
```
npm run dev
```

----------------------------------------

TITLE: Generate Related Questions Success Response JSON
DESCRIPTION: A JSON response indicating successful generation of related questions, including a list of alternative queries derived from the original user question.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_121

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": [
        "What makes Neovim superior to Vim in terms of features?",
        "How do the benefits of Neovim compare to those of Vim?",
        "What advantages does Neovim offer that are not present in Vim?",
        "In what ways does Neovim outperform Vim in functionality?",
        "What are the most significant improvements in Neovim compared to Vim?",
        "What unique advantages does Neovim bring to the table over Vim?",
        "How does the user experience in Neovim differ from Vim in terms of benefits?",
        "What are the top reasons to switch from Vim to Neovim?",
        "What features of Neovim are considered more advanced than those in Vim?"
    ],
    "message": "success"
}
```

----------------------------------------

TITLE: Delete Agent with cURL Example
DESCRIPTION: Example cURL command to delete an agent using its ID. It includes the HTTP method, URL, and necessary headers for content type and authorization.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_139

LANGUAGE: bash
CODE:
```
curl --request DELETE \
     --url http://{address}/api/v1/agents/58af890a2a8911f0a71a11b922ed82d6 \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{}'
```

----------------------------------------

TITLE: Converse with Chat Assistant
DESCRIPTION: Initiates an AI-powered conversation by asking a specified chat assistant a question. Special considerations for streaming mode responses are noted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_86

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/chats/{chat_id}/completions
Notes:
  - In streaming mode, not all responses include a reference.
  - In streaming mode, the last message is an empty message.
```

LANGUAGE: json
CODE:
```
data:
{
  "code": 0,
  "data": true
}
```

----------------------------------------

TITLE: Create Chat Assistant API Endpoint
DESCRIPTION: Documents the API endpoint for creating a new chat assistant. This POST request requires specific headers for content type and authorization, and a JSON body containing the assistant's name, avatar, associated dataset IDs, and configurations for the LLM and prompt.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_60

LANGUAGE: APIDOC
CODE:
```
CHAT ASSISTANT MANAGEMENT
Create chat assistant
Method: POST
URL: /api/v1/chats
Headers:
  'content-Type: application/json'
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "name": string
  "avatar": string
  "dataset_ids": list[string]
  "llm": object
  "prompt": object
```

----------------------------------------

TITLE: Setting RAGFlow Image to Specific Published Release
DESCRIPTION: Updates the `RAGFLOW_IMAGE` variable in the `ragflow/docker/.env` file to specify a particular officially published Docker image version, for example, `v0.19.0`. This ensures that the Docker environment uses the image corresponding to the chosen code release.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/upgrade_ragflow.mdx#_snippet_5

LANGUAGE: bash
CODE:
```
RAGFLOW_IMAGE=infiniflow/ragflow:v0.19.0
```

----------------------------------------

TITLE: Configuring OAuth and OIDC Authentication for RAGFlow
DESCRIPTION: This YAML configuration demonstrates how to set up various third-party authentication methods for RAGFlow, including generic OAuth2, OpenID Connect (OIDC), and GitHub. It specifies required parameters like client IDs, secrets, authorization URLs, token URLs, user info URLs, issuers, scopes, and redirect URIs for each channel, enabling users to sign up or sign in using external accounts.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/configurations.md#_snippet_1

LANGUAGE: YAML
CODE:
```
oauth:
  oauth2:
    display_name: "OAuth2"
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    authorization_url: "https://your-oauth-provider.com/oauth/authorize"
    token_url: "https://your-oauth-provider.com/oauth/token"
    userinfo_url: "https://your-oauth-provider.com/oauth/userinfo"
    redirect_uri: "https://your-app.com/v1/user/oauth/callback/oauth2"

  oidc:
    display_name: "OIDC"
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    issuer: "https://your-oauth-provider.com/oidc"
    scope: "openid email profile"
    redirect_uri: "https://your-app.com/v1/user/oauth/callback/oidc"

  github:
    # https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app
    type: "github"
    icon: "github"
    display_name: "Github"
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    redirect_uri: "https://your-app.com/v1/user/oauth/callback/github"
```

----------------------------------------

TITLE: Python: Update Chat Assistant Properties
DESCRIPTION: This Python example demonstrates how to initialize the RAGFlow SDK, retrieve a dataset ID, create a new chat assistant, and then update its properties, specifically changing its name, LLM temperature, and prompt's top_n setting.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_44

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
datasets = rag_object.list_datasets(name="kb_1")
dataset_id = datasets[0].id
assistant = rag_object.create_chat("Miss R", dataset_ids=[dataset_id])
assistant.update({"name": "Stefan", "llm": {"temperature": 0.8}, "prompt": {"top_n": 8}})
```

----------------------------------------

TITLE: Permanently Set Linux vm.max_map_count
DESCRIPTION: This snippet shows how to permanently set the `vm.max_map_count` kernel parameter by adding or updating the value in the `/etc/sysctl.conf` file. This ensures the change persists across system reboots.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_2

LANGUAGE: config
CODE:
```
vm.max_map_count=262144
```

----------------------------------------

TITLE: List Documents API Endpoint
DESCRIPTION: Describes the GET endpoint for listing documents in a specified dataset, including URL, method, and headers.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_33

LANGUAGE: APIDOC
CODE:
```
GET /api/v1/datasets/{dataset_id}/documents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&keywords={keywords}&id={document_id}&name={document_name}
Lists documents in a specified dataset.

Request:
- Method: GET
- URL: /api/v1/datasets/{dataset_id}/documents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&keywords={keywords}&id={document_id}&name={document_name}
- Headers:
  - 'content-Type: application/json'
  - 'Authorization: Bearer <YOUR_API_KEY>'
```

----------------------------------------

TITLE: Reference: Chunk Object Structure
DESCRIPTION: Defines the structure of a `Chunk` object, which represents a reference to a message. It details various attributes such as ID, content, document information, position, dataset ID, and different similarity scores.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_59

LANGUAGE: APIDOC
CODE:
```
Chunk:
  id: str
    The chunk ID.
  content: str
    The content of the chunk.
  image_id: str
    The ID of the snapshot of the chunk. Applicable only when the source of the chunk is an image, PPT, PPTX, or PDF file.
  document_id: str
    The ID of the referenced document.
  document_name: str
    The name of the referenced document.
  position: list[str]
    The location information of the chunk within the referenced document.
  dataset_id: str
    The ID of the dataset to which the referenced document belongs.
  similarity: float
    A composite similarity score of the chunk ranging from 0 to 1, with a higher value indicating greater similarity. It is the weighted sum of vector_similarity and term_similarity.
  vector_similarity: float
    A vector similarity score of the chunk ranging from 0 to 1, with a higher value indicating greater similarity between vector embeddings.
  term_similarity: float
    A keyword similarity score of the chunk ranging from 0 to 1, with a higher value indicating greater similarity between keywords.
```

----------------------------------------

TITLE: Delete Specific Datasets in RAGFlow (Python)
DESCRIPTION: Example Python code to delete specific datasets by providing a list of their IDs to the `delete_datasets` method.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_8

LANGUAGE: python
CODE:
```
rag_object.delete_datasets(ids=["d94a8dc02c9711f0930f7fbc369eab6d","e94a8dc02c9711f0930f7fbc369eab6e"])
```

----------------------------------------

TITLE: RAGFlow API Success Response with DSL Configuration
DESCRIPTION: This JSON snippet represents a successful response from a RAGFlow API call. It contains an 'agent_id' and the 'dsl' object, which defines the workflow. The 'dsl' includes 'components' like 'Answer', 'Generate', and 'Begin', each with their respective parameters and upstream/downstream connections. The 'Generate' component specifically shows configurations for an LLM, including the prompt, temperature, and penalty settings. The 'graph' section details the visual layout and connections of these components as nodes and edges.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_112

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": [{
        "agent_id": "e9e2b9c2b2f911ef801d0242ac120006",
        "dsl": {
            "answer": [],
            "components": {
                "Answer:OrangeTermsBurn": {
                    "downstream": [],
                    "obj": {
                        "component_name": "Answer",
                        "params": {}
                    },
                    "upstream": []
                },
                "Generate:SocialYearsRemain": {
                    "downstream": [],
                    "obj": {
                        "component_name": "Generate",
                        "params": {
                            "cite": true,
                            "frequency_penalty": 0.7,
                            "llm_id": "gpt-4o___OpenAI-API@OpenAI-API-Compatible",
                            "message_history_window_size": 12,
                            "parameters": [],
                            "presence_penalty": 0.4,
                            "prompt": "Please summarize the following paragraph. Pay attention to the numbers and do not make things up. The paragraph is as follows:\n{input}\nThis is what you need to summarize.",
                            "temperature": 0.1,
                            "top_p": 0.3
                        }
                    },
                    "upstream": []
                },
                "begin": {
                    "downstream": [],
                    "obj": {
                        "component_name": "Begin",
                        "params": {}
                    },
                    "upstream": []
                }
            },
            "graph": {
                "edges": [],
                "nodes": [
                    {
                        "data": {
                            "label": "Begin",
                            "name": "begin"
                        },
                        "height": 44,
                        "id": "begin",
                        "position": {
                            "x": 50,
                            "y": 200
                        },
                        "sourcePosition": "left",
                        "targetPosition": "right",
                        "type": "beginNode",
                        "width": 200
                    },
                    {
                        "data": {
                            "form": {
                                "cite": true,
                                "frequencyPenaltyEnabled": true,
                                "frequency_penalty": 0.7,
                                "llm_id": "gpt-4o___OpenAI-API@OpenAI-API-Compatible",
                                "maxTokensEnabled": true,
                                "message_history_window_size": 12,
                                "parameters": [],
                                "presencePenaltyEnabled": true,
                                "presence_penalty": 0.4,
                                "prompt": "Please summarize the following paragraph. Pay attention to the numbers and do not make things up. The paragraph is as follows:\n{input}\nThis is what you need to summarize.",
                                "temperature": 0.1,
                                "temperatureEnabled": true,
                                "topPEnabled": true,
                                "top_p": 0.3
                            },
                            "label": "Generate",
                            "name": "Generate Answer_0"
                        },
                        "dragging": false,
                        "height": 105,
                        "id": "Generate:SocialYearsRemain",
                        "position": {
                            "x": 561.3457829707513,
                            "y": 178.7211182312641
                        },
                        "positionAbsolute": {
                            "x": 561.3457829707513,
                            "y": 178.7211182312641
                        },
                        "selected": true,
                        "sourcePosition": "right",
                        "targetPosition": "left",
                        "type": "generateNode",
                        "width": 200
                    },
                    {
                        "data": {
                            "form": {},
                            "label": "Answer",
                            "name": "Dialogue_0"
                        },
                        "height": 44,
                        "id": "Answer:OrangeTermsBurn",
                        "position": {
                            "x": 317.2368194777658,
                            "y": 218.30635555445093
                        },
                        "sourcePosition": "right",
                        "targetPosition": "left",
                        "type": "logicNode"
                    }
                ]
            }
        }
    }]
}
```

----------------------------------------

TITLE: Configure Knowledge Graph Entity Resolution
DESCRIPTION: Controls whether similar entities are deduplicated and combined in the knowledge graph. Enabling this feature consumes more tokens but can create a more effective and consolidated graph by merging variations of the same entity.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/dataset/construct_knowledge_graph.md#_snippet_2

LANGUAGE: APIDOC
CODE:
```
Entity resolution:
  Description: Whether to enable entity resolution (deduplication).
  Options:
    - Disable: (Default) Disable entity resolution.
    - Enable: Combine similar entities (e.g., '2025' and 'the year of 2025', or 'IT' and 'Information Technology') to construct a more effective graph. This option consumes more tokens.
```

----------------------------------------

TITLE: API: Message and Chunk Object Structure
DESCRIPTION: Defines the structure and attributes of the `Message` object, which represents a response from the RAGFlow assistant, and its nested `Chunk` objects, which provide detailed references to source documents.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_55

LANGUAGE: APIDOC
CODE:
```
Message:
  id: str
    The auto-generated message ID.
  content: str
    The content of the message. Defaults to "Hi! I am your assistant, can I help you?".
  reference: list[Chunk]
    A list of Chunk objects representing references to the message.
Chunk:
  id: str
    The chunk ID.
  content: str
    The content of the chunk.
  img_id: str
    The ID of the snapshot of the chunk. Applicable only when the source of the chunk is an image, PPT, PPTX, or PDF file.
  document_id: str
    The ID of the referenced document.
  document_name: str
    The name of the referenced document.
  position: list[str]
    The location information of the chunk within the referenced document.
  dataset_id: str
    The ID of the dataset to which the referenced document belongs.
  similarity: float
    A composite similarity score of the chunk ranging from 0 to 1, with a higher value indicating greater similarity. It is the weighted sum of vector_similarity and term_similarity.
  vector_similarity: float
    A vector similarity score of the chunk ranging from 0 to 1, with a higher value indicating greater similarity between vector embeddings.
  term_similarity: float
    A keyword similarity score of the chunk ranging from 0 to 1, with a higher value indicating greater similarity between keywords.
```

----------------------------------------

TITLE: Example: Send Chat Completion Request with Empty Body (Bash)
DESCRIPTION: Demonstrates how to make a POST request to the chat completions endpoint using `curl`. This example shows the basic structure of the request with an empty JSON body, including necessary headers for content type and authorization.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_89

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/chats/{chat_id}/completions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data-binary '
     {
     }'
```

----------------------------------------

TITLE: Create Agent Session (No Required Parameters)
DESCRIPTION: Example cURL command to initiate an agent session when the 'Begin' component does not require any specific parameters in the request body. The request uses 'application/json' content type.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_96

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/agents/{agent_id}/sessions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{ \
     }'
```

----------------------------------------

TITLE: Committing Changes with a Message - Git
DESCRIPTION: This command commits the staged changes to the current branch with a descriptive commit message. The message should clearly summarize the changes made in the commit.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/contribution/contributing.md#_snippet_2

LANGUAGE: bash
CODE:
```
git commit -m 'Provide sufficient info in your commit message'
```

----------------------------------------

TITLE: List Documents API Request Example
DESCRIPTION: A cURL command example demonstrating how to list documents using the GET API endpoint, including authorization.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_34

LANGUAGE: bash
CODE:
```
curl --request GET \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&keywords={keywords}&id={document_id}&name={document_name} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

----------------------------------------

TITLE: RAGFlow API: Delete Datasets
DESCRIPTION: Defines the `delete_datasets` method for RAGFlow's Python API, specifying its parameters for deleting datasets by their IDs. This method allows for the removal of one or more datasets.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_6

LANGUAGE: APIDOC
CODE:
```
RAGFlow.delete_datasets(ids: list[str] | None = None)

Deletes datasets by ID.

Parameters:
```

----------------------------------------

TITLE: JSON Response: Streaming Chat Success with Begin Parameters
DESCRIPTION: This JSON snippet demonstrates a streaming successful response from a chat interaction where parameters were specified in the 'Begin' component. It shows multiple partial answers being returned incrementally, culminating in the full answer, followed by a final success indicator.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_109

LANGUAGE: json
CODE:
```
data:{
    "code": 0,
    "message": "",
    "data": {
        "answer": "How",
        "reference": {},
        "id": "0379ac4c-b26b-4a44-8b77-99cebf313fdf",
        "session_id": "4399c7d0b86311efac5b0242ac120005"
    }
}
data:{
    "code": 0,
    "message": "",
    "data": {
        "answer": "How is",
        "reference": {},
        "id": "0379ac4c-b26b-4a44-8b77-99cebf313fdf",
        "session_id": "4399c7d0b86311efac5b0242ac120005"
    }
}
data:{
    "code": 0,
    "message": "",
    "data": {
        "answer": "How is the",
        "reference": {},
        "id": "0379ac4c-b26b-4a44-8b77-99cebf313fdf",
        "session_id": "4399c7d0b86311efac5b0242ac120005"
    }
}
data:{
    "code": 0,
    "message": "",
    "data": {
        "answer": "How is the weather",
        "reference": {},
        "id": "0379ac4c-b26b-4a44-8b77-99cebf313fdf",
        "session_id": "4399c7d0b86311efac5b0242ac120005"
    }
}
data:{
    "code": 0,
    "message": "",
    "data": {
        "answer": "How is the weather tomorrow",
        "reference": {},
        "id": "0379ac4c-b26b-4a44-8b77-99cebf313fdf",
        "session_id": "4399c7d0b86311efac5b0242ac120005"
    }
}
data:{
    "code": 0,
    "message": "",
    "data": {
        "answer": "How is the weather tomorrow?",
        "reference": {},
        "id": "0379ac4c-b26b-4a44-8b77-99cebf313fdf",
        "session_id": "4399c7d0b86311efac5b0242ac120005"
    }
}
data:{
    "code": 0,
    "message": "",
    "data": {
        "answer": "How is the weather tomorrow?",
        "reference": {},
        "id": "0379ac4c-b26b-4a44-8b77-99cebf313fdf",
        "session_id": "4399c7d0b86311efac5b0242ac120005"
    }
}
data:{
    "code": 0,
    "message": "",
    "data": true
}
```

----------------------------------------

TITLE: Redis Docker Environment Variables
DESCRIPTION: Defines environment variables for configuring the Redis service within the Docker environment, covering external port and password.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_5

LANGUAGE: APIDOC
CODE:
```
REDIS_PORT:
  Description: "The port used to expose the Redis service to the host machine, allowing external access to the Redis service running inside the Docker container."
  Default: "6379"
REDIS_PASSWORD:
  Description: "The password for Redis."
```

----------------------------------------

TITLE: Elasticsearch Docker Environment Variables
DESCRIPTION: Defines environment variables for configuring the Elasticsearch service within the Docker environment, covering version, external port, and authentication password.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_0

LANGUAGE: APIDOC
CODE:
```
STACK_VERSION:
  Description: "The version of Elasticsearch."
  Default: "8.11.3"
ES_PORT:
  Description: "The port used to expose the Elasticsearch service to the host machine, allowing external access to the service running inside the Docker container."
  Default: "1200"
ELASTIC_PASSWORD:
  Description: "The password for Elasticsearch."
```

----------------------------------------

TITLE: Create Agent Session (With Required JSON Parameters)
DESCRIPTION: Example cURL command to initiate an agent session when the 'Begin' component requires specific JSON parameters, such as 'lang' and 'file', in the request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_97

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/agents/{agent_id}/sessions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{ \
            "lang":"Japanese",\
            "file":"Who are you"\
     }'
```

----------------------------------------

TITLE: RAGFlow.list_datasets API Reference
DESCRIPTION: API reference for listing datasets, including parameters for pagination, sorting, and filtering by ID or name. Returns a list of DataSet objects or an Exception on failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_9

LANGUAGE: APIDOC
CODE:
```
RAGFlow.list_datasets(
    page: int = 1, 
    page_size: int = 30, 
    orderby: str = "create_time", 
    desc: bool = True,
    id: str = None,
    name: str = None
) -> list[DataSet]
Parameters:
  page: `int` - Specifies the page on which the datasets will be displayed. Defaults to `1`.
  page_size: `int` - The number of datasets on each page. Defaults to `30`.
  orderby: `str` - The field by which datasets should be sorted. Available options:
    - `"create_time"` (default)
    - `"update_time"`
  desc: `bool` - Indicates whether the retrieved datasets should be sorted in descending order. Defaults to `True`.
  id: `str` - The ID of the dataset to retrieve. Defaults to `None`.
  name: `str` - The name of the dataset to retrieve. Defaults to `None`.
Returns:
- Success: A list of `DataSet` objects.
- Failure: `Exception`.
```

----------------------------------------

TITLE: Document.delete_chunks API Reference
DESCRIPTION: API documentation for deleting chunks from a document. It describes the `chunk_ids` parameter for specifying which chunks to delete, noting that all chunks are deleted if `chunk_ids` is not provided, and the lack of a return value on success.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_33

LANGUAGE: APIDOC
CODE:
```
Document.delete_chunks(chunk_ids: list[str])

Parameters:
  chunk_ids: `list[str]`
    The IDs of the chunks to delete. Defaults to `None`. If it is not specified, all chunks of the current document will be deleted.

Returns:
  Success: No value is returned.
  Failure: `Exception`
```

----------------------------------------

TITLE: Python: Delete Specific Chat Assistants
DESCRIPTION: This Python example demonstrates how to use the RAGFlow SDK to delete specific chat assistants by providing a list of their unique identifiers.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_46

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
rag_object.delete_chats(ids=["id_1","id_2"])
```

----------------------------------------

TITLE: Delete Chat Assistant Sessions with RAGFlow SDK
DESCRIPTION: Removes one or more sessions associated with the current chat assistant. If specific session IDs are provided, only those sessions are deleted; otherwise, all sessions linked to the assistant are removed. No value is returned on success.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_52

LANGUAGE: APIDOC
CODE:
```
Chat.delete_sessions(ids:list[str] = None)
  Deletes sessions of the current chat assistant by ID.
  Parameters:
    ids: list[str]
      The IDs of the sessions to delete. Defaults to None. If it is not specified, all sessions associated with the current chat assistant will be deleted.
  Returns:
    Success: No value is returned.
    Failure: Exception
```

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
assistant = rag_object.list_chats(name="Miss R")
assistant = assistant[0]
assistant.delete_sessions(ids=["id_1","id_2"])
```

----------------------------------------

TITLE: Create Agent Session (With Begin Parameters)
DESCRIPTION: This `curl` command illustrates how to create a new session with the agent completions API when the 'Begin' component expects specific parameters. It includes example parameters like 'lang' and 'file' in the request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_104

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/agents/{agent_id}/completions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data-binary '\n     {\n          "lang":"English",\n          "file":"How is the weather tomorrow?"\n     }'
```