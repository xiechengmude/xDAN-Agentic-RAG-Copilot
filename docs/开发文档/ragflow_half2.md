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

```

----------------------------------------

TITLE: Update Chunk API Endpoint
DESCRIPTION: Updates the content or configurations of a specific chunk within a document. Allows modification of text content, important keywords, and availability status. Requires authentication and the chunk ID in the URL.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_55

LANGUAGE: APIDOC
CODE:
```
API Endpoint: PUT /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}
Description: Updates content or configurations for a specified chunk.
Headers:
  - 'Content-Type: application/json'
  - 'Authorization: Bearer <YOUR_API_KEY>'
Path Parameters:
  - dataset_id: The associated dataset ID.
  - document_id: The associated document ID.
  - chunk_id: The ID of the chunk to update.
Body Parameters:
  - content: string - The text content of the chunk.
  - important_keywords: list[string] - A list of key terms or phrases to tag with the chunk.
  - available: boolean - The chunk's availability status in the dataset. Value options: true (Available, default), false (Unavailable).
Responses:
  - Success (200 OK):
    code: 0
  - Failure (Error Code):
    code: 102
    message: string - e.g., "Can't find this chunk 29a2d9987e16ba331fb4d7d30d99b71d2"
```

LANGUAGE: bash
CODE:
```
curl --request PUT \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id} \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {   
          "content": "ragflow123",  
          "important_keywords": []  
     }'
```

LANGUAGE: json
CODE:
```
{
    "code": 0
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "Can't find this chunk 29a2d9987e16ba331fb4d7d30d99b71d2"
}
```

----------------------------------------

TITLE: Curl Example: Parse Documents
DESCRIPTION: Example `curl` command to trigger parsing for specific documents in a dataset. It shows the POST method, URL, headers, and the JSON body with document IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_43

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/datasets/{dataset_id}/chunks \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "document_ids": ["97a5f1c2759811efaa500242ac120004","97ad64b6759811ef9fc30242ac120004"]
     }'
```

----------------------------------------

TITLE: Installing uv for Python Dependency Management - Bash
DESCRIPTION: This command installs 'uv' using pipx, a tool for installing and managing Python applications in isolated environments. 'uv' is used by RAGFlow for efficient dependency management.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_1

LANGUAGE: bash
CODE:
```
pipx install uv
```

----------------------------------------

TITLE: Categorize Component Message Window Size Configuration
DESCRIPTION: Specifies the number of previous dialogue rounds to input into the LLM. This feature is exclusively for multi-turn dialogues and consumes additional tokens.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/agent_component_reference/categorize.mdx#_snippet_2

LANGUAGE: APIDOC
CODE:
```
Message window size: integer
  Default: 1
  Usage: Number of previous dialogue rounds to feed to the LLM.
  Note: This feature is used for multi-turn dialogue ONLY.
```

----------------------------------------

TITLE: APIDOC: Document Update Message Structure
DESCRIPTION: Defines the structure for the `update_message` dictionary used to modify document attributes. It specifies keys like `display_name`, `meta_fields`, `chunk_method`, and `parser_config`, with detailed options for `chunk_method` and its corresponding `parser_config` attributes.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_16

LANGUAGE: APIDOC
CODE:
```
update_message: dict[str, str|dict[]], Required
  A dictionary representing the attributes to update, with the following keys:
  - "display_name": str
    The name of the document to update.
  - "meta_fields": dict[str, Any]
    The meta fields of the document.
  - "chunk_method": str
    The parsing method to apply to the document.
    - "naive": General
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
  - "parser_config": dict[str, Any]
    The parsing configuration for the document. Its attributes vary based on the selected "chunk_method":
    - chunk_method="naive":  
      {"chunk_token_num":128,"delimiter":"\\n","html4excel":False,"layout_recognize":True,"raptor":{"use_raptor":False}}
    - chunk_method="qa":  
      {"raptor": {"use_raptor": False}}
    - chunk_method="manuel":  
      {"raptor": {"use_raptor": False}}
    - chunk_method="table":  
      None
    - chunk_method="paper":  
      {"raptor": {"use_raptor": False}}
    - chunk_method="book":  
      {"raptor": {"use_raptor": False}}
    - chunk_method="laws":  
      {"raptor": {"use_raptor": False}}
    - chunk_method="presentation":  
      {"raptor": {"use_raptor": False}}
    - chunk_method="picture":  
      None
    - chunk_method="one":  
      None
    - chunk_method="knowledge-graph":  
      {"chunk_token_num":128,"delimiter":"\\n","entity_types":["organization","person","location","event","time"]}
    - chunk_method="email":  
      None

Returns:
- Success: No value is returned.
- Failure: Exception
```

----------------------------------------

TITLE: Schema: Failed Response for Creating Chat Session
DESCRIPTION: Defines the JSON structure returned when the creation of a chat session fails, typically indicating an error with code and a descriptive message.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_81

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "Name cannot be empty."
}
```

----------------------------------------

TITLE: JSON Response: Successful Chat with Begin Parameters, No Session ID
DESCRIPTION: This JSON snippet illustrates a successful response when a chat interaction begins with specified parameters but without an initial session ID. It returns a new session ID, an empty answer, and a list of parameters including their keys, names, types, and values.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_108

LANGUAGE: json
CODE:
```
data:{
    "code": 0,
    "message": "",
    "data": {
        "session_id": "eacb36a0bdff11ef97120242ac120006",
        "answer": "",
        "reference": [],
        "param": [
            {
                "key": "lang",
                "name": "Target Language",
                "optional": false,
                "type": "line",
                "value": "English"
            },
            {
                "key": "file",
                "name": "Files",
                "optional": false,
                "type": "file",
                "value": "How is the weather tomorrow?"
            },
            {
                "key": "hhyt",
                "name": "hhty",
                "optional": true,
                "type": "line"
            }
        ]
    }
}
data:
```

----------------------------------------

TITLE: Performing Layout Recognition with Deepdoc Python Tool (Bash)
DESCRIPTION: This command runs the layout recognition process using the `t_recognizer.py` script. It analyzes the structural components of input images or PDFs, such as text, titles, figures, and tables, based on a specified confidence threshold. The results, including images demonstrating detected layouts, are saved to the output directory.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/deepdoc/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python deepdoc/vision/t_recognizer.py --inputs=path_to_images_or_pdfs --threshold=0.2 --mode=layout --output_dir=path_to_store_result
```

----------------------------------------

TITLE: API Reference: Delete Chat Assistants Response Examples
DESCRIPTION: Illustrates the JSON response structures for successful and failed delete operations on chat assistants.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_72

LANGUAGE: APIDOC
CODE:
```
Success:
{
    "code": 0
}

Failure:
{
    "code": 102,
    "message": "ids are required"
}
```

----------------------------------------

TITLE: API Reference: Update Chat Assistant Response Examples
DESCRIPTION: Illustrates the JSON response structures for successful and failed update operations on a chat assistant.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_68

LANGUAGE: APIDOC
CODE:
```
Success:
{
    "code": 0
}

Failure:
{
    "code": 102,
    "message": "Duplicated chat name in updating dataset."
}
```

----------------------------------------

TITLE: API: Detailed Parameters for Updating Dataset Configurations
DESCRIPTION: Comprehensive breakdown of all parameters available for updating a dataset, including path and body parameters, their types, constraints, and default values, especially for parser_config based on chunk_method.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_21

LANGUAGE: APIDOC
CODE:
```
Request parameters:
  dataset_id: (Path parameter)
    The ID of the dataset to update.
  "name": (Body parameter), string
    The revised name of the dataset.
    - Basic Multilingual Plane (BMP) only
    - Maximum 128 characters
    - Case-insensitive
  "avatar": (Body parameter), string
    The updated base64 encoding of the avatar.
    - Maximum 65535 characters
  "embedding_model": (Body parameter), string
    The updated embedding model name.
    - Ensure that "chunk_count" is 0 before updating "embedding_model".
    - Maximum 255 characters
    - Must follow model_name@model_factory format
  "permission": (Body parameter), string
    The updated dataset permission. Available options:
    - "me": (Default) Only you can manage the dataset.
    - "team": All team members can manage the dataset.
  "pagerank": (Body parameter), int
    refer to [Set page rank](https://ragflow.io/docs/dev/set_page_rank)
    - Default: 0
    - Minimum: 0
    - Maximum: 100
  "chunk_method": (Body parameter), enum<string>
    The chunking method for the dataset. Available options:
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
  "parser_config": (Body parameter), object
    The configuration settings for the dataset parser. The attributes in this JSON object vary with the selected "chunk_method":
    - If "chunk_method" is "naive", the "parser_config" object contains the following attributes:
      - "auto_keywords": int
        - Defaults to 0
        - Minimum: 0
        - Maximum: 32
      - "auto_questions": int
        - Defaults to 0
        - Minimum: 0
        - Maximum: 10
      - "chunk_token_num": int
        - Defaults to 128
        - Minimum: 1
        - Maximum: 2048
      - "delimiter": string
        - Defaults to "\\n".
      - "html4excel": bool Indicates whether to convert Excel documents into HTML format.
        - Defaults to false
      - "layout_recognize": string
        - Defaults to DeepDOC
      - "tag_kb_ids": array<string> refer to [Use tag set](https://ragflow.io/docs/dev/use_tag_sets)
        - Must include a list of dataset IDs, where each dataset is parsed using the ​​Tag Chunk Method
      - "task_page_size": int For PDF only.
        - Defaults to 12
        - Minimum: 1
      - "raptor": object RAPTOR-specific settings.
        - Defaults to: {\"use_raptor\": false}
      - "graphrag": object GRAPHRAG-specific settings.
        - Defaults to: {\"use_graphrag\": false}
    - If "chunk_method" is "qa", "manuel", "paper", "book", "laws", or "presentation", the "parser_config" object contains the following attribute:
      - "raptor": object RAPTOR-specific settings.
        - Defaults to: {\"use_raptor\": false}.
    - If "chunk_method" is "table", "picture", "one", or "email", "parser_config" is an empty JSON object.
```

----------------------------------------

TITLE: API: Create Session with Chat Assistant
DESCRIPTION: Documents the API endpoint for initiating a new session linked to a specific chat assistant. It outlines the HTTP method, URL structure with a path parameter, required headers, and the JSON body parameters for session creation.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_78

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/chats/{chat_id}/sessions
Headers:
  'content-Type: application/json'
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "name": string
  "user_id": string (optional)
Request parameters:
  chat_id: (Path parameter)
    The ID of the associated chat assistant.
  "name": (Body parameter), string
    The name of the chat session to create.
  "user_id": (Body parameter), string
    Optional user-defined ID.
```

----------------------------------------

TITLE: Pulling Ollama Model on Linux (Bash)
DESCRIPTION: Pulls a specified Ollama model (e.g., 'qwen2:latest') from the Ollama registry. This command is executed in a new terminal after the Ollama service is running.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_16

LANGUAGE: bash
CODE:
```
./ollama pull <model_name>
```

----------------------------------------

TITLE: Curl Example: Delete Documents by ID
DESCRIPTION: Example `curl` command to delete specific documents from a dataset using their IDs. It demonstrates the DELETE method, URL structure, required headers, and JSON request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_39

LANGUAGE: bash
CODE:
```
curl --request DELETE \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "ids": ["id_1","id_2"]
     }'
```

----------------------------------------

TITLE: Curl Example for Create Agent Completion
DESCRIPTION: This curl command demonstrates how to make a POST request to the `/api/v1/agents_openai/{agent_id}/chat/completions` endpoint. It includes setting the necessary headers for content type and authorization, and provides a JSON body with model, messages, and stream parameters.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_7

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/agents_openai/{agent_id}/chat/completions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
        "model": "model",
        "messages": [{"role": "user", "content": "Say this is a test!"}],
        "stream": true
      }'
```

----------------------------------------

TITLE: TCF API Consent Event Listener - JavaScript
DESCRIPTION: Registers an event listener with the TCF API to respond to consent changes. Upon `useractioncomplete` or `tcloaded` events, it processes Google Consent Mode V2, handles Ezoic consent decisions, reloads ads based on consent, and potentially logs consent denial if certain purposes are not granted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/sdk/python/test/test_sdk_api/test_data/test.html#_snippet_29

LANGUAGE: JavaScript
CODE:
```
__tcfapi("addEventListener",2,function(tcdata,success){if(!success||!tcdata){window._emitEzConsentEvent();return;} if(!tcdata.gdprApplies){_setAllEzConsentTrue();window._emitEzConsentEvent();return;} if(tcdata.eventStatus==="useractioncomplete"||tcdata.eventStatus==="tcloaded"){if(typeof gtag!='undefined'){_handleGoogleConsentV2(tcdata);} _handleConsentDecision(tcdata);if(tcdata.purpose.consents["1"]===true&&tcdata.vendor.consents["755"]!==false){window.ezgconsent=true;(adsbygoogle=window.adsbygoogle||[]).pauseAdRequests=0;_reloadAds();}else{_reloadAds();} if(window.__ezconsent){__ezconsent.setEzoicConsentSettings(ezConsentCategories);} __tcfapi("removeEventListener",2,function(success){return null;},tcdata.listenerId);if(!(tcdata.purpose.consents["1"]===true&&_ezAllowed(tcdata,"2")&&_ezAllowed(tcdata,"3")&&_ezAllowed(tcdata,"4"))){if(typeof __ez=="object"&&typeof __ez.bit=="object"&&typeof window["_ezaq"]=="object"&&typeof window["_ezaq"]["page_view_id"]=="string"){__ez.bit.Add(window["_ezaq"]["page_view_id"],"ezoic_consent_denied");}}}},true);
```

----------------------------------------

TITLE: Python: Delete Specific Agent Sessions Example
DESCRIPTION: Illustrates how to use the `Agent.delete_sessions` method in Python to delete specific agent sessions by providing a list of session IDs. It initializes the RAGFlow SDK and retrieves an agent.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_64

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
AGENT_id = "AGENT_ID"
agent = rag_object.list_agents(id = AGENT_id)[0]
agent.delete_sessions(ids=["id_1","id_2"])
```

----------------------------------------

TITLE: Clone RAGFlow Repository and Install Python Dependencies
DESCRIPTION: Clones the RAGFlow source code repository, navigates into it, and installs all required Python dependencies for Python 3.10 using `uv`. It also runs a script to download additional dependencies and installs pre-commit hooks for development.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_14

LANGUAGE: bash
CODE:
```
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/
uv sync --python 3.10 --all-extras # install RAGFlow dependent python modules
uv run download_deps.py
pre-commit install
```

----------------------------------------

TITLE: Successful Chat Assistant Operation Response JSON
DESCRIPTION: Example JSON structure returned upon successful creation or retrieval of a chat assistant, detailing its configuration, associated datasets, LLM settings, and prompt parameters.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_63

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "avatar": "",
        "create_date": "Thu, 24 Oct 2024 11:18:29 GMT",
        "create_time": 1729768709023,
        "dataset_ids": [
            "527fa74891e811ef9c650242ac120006"
        ],
        "description": "A helpful Assistant",
        "do_refer": "1",
        "id": "b1f2f15691f911ef81180242ac120003",
        "language": "English",
        "llm": {
            "frequency_penalty": 0.7,
            "model_name": "qwen-plus@Tongyi-Qianwen",
            "presence_penalty": 0.4,
            "temperature": 0.1,
            "top_p": 0.3
        },
        "name": "12234",
        "prompt": {
            "empty_response": "Sorry! No relevant content was found in the knowledge base!",
            "keywords_similarity_weight": 0.3,
            "opener": "Hi! I'm your assistant, what can I do for you?",
            "prompt": "You are an intelligent assistant. Please summarize the content of the knowledge base to answer the question. Please list the data in the knowledge base and answer in detail. When all knowledge base content is irrelevant to the question, your answer must include the sentence \"The answer you are looking for is not found in the knowledge base!\" Answers need to consider chat history.\n ",
            "rerank_model": "",
            "similarity_threshold": 0.2,
            "top_n": 6,
            "variables": [
                {
                    "key": "knowledge",
                    "optional": false
                }
            ]
        },
        "prompt_type": "simple",
        "status": "1",
        "tenant_id": "69736c5e723611efb51b0242ac120007",
        "top_k": 1024,
        "update_date": "Thu, 24 Oct 2024 11:18:29 GMT",
        "update_time": 1729768709023
    }
}
```

----------------------------------------

TITLE: RAGFlow API Error Codes
DESCRIPTION: A list of common error codes returned by the RAGFlow API, along with their messages and descriptions. These codes help in diagnosing issues when interacting with the API.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_1

LANGUAGE: APIDOC
CODE:
```
| Code | Message | Description |
|---|---|---|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Unauthorized access |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error| Server internal error |
| 1001 | Invalid Chunk ID | Invalid Chunk ID |
| 1002 | Chunk Update Failed | Chunk update failed |
```

----------------------------------------

TITLE: List Chunks in Ragflow Document (GET)
DESCRIPTION: This API endpoint retrieves a list of chunks associated with a specific document. It supports filtering by keywords, pagination, and direct retrieval by chunk ID.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_52

LANGUAGE: APIDOC
CODE:
```
Method: GET
URL: /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks?keywords={keywords}&page={page}&page_size={page_size}&id={chunk_id}
Headers:
  'Authorization: Bearer <YOUR_API_KEY>'

Request parameters:
- dataset_id: (Path parameter) The associated dataset ID.
- document_id: (Path parameter) The associated document ID.
- keywords: (Filter parameter), string. The keywords used to match chunk content.
- page: (Filter parameter), integer. Specifies the page on which the chunks will be displayed. Defaults to 1.
- page_size: (Filter parameter), integer. The maximum number of chunks on each page. Defaults to 1024.
- id: (Filter parameter), string. The ID of the chunk to retrieve.
```

LANGUAGE: bash
CODE:
```
curl --request GET \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks?keywords={keywords}&page={page}&page_size={page_size}&id={chunk_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "chunks": [
            {
                "available": true,
                "content": "This is a test content.",
                "docnm_kwd": "1.txt",
                "document_id": "b330ec2e91ec11efbc510242ac120004",
                "id": "b48c170e90f70af998485c1065490726",
                "image_id": "",
                "important_keywords": "",
                "positions": [
                    ""
                ]
            }
        ],
        "doc": {
            "chunk_count": 1,
            "chunk_method": "naive",
            "create_date": "Thu, 24 Oct 2024 09:45:27 GMT",
            "create_time": 1729763127646,
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
            "process_begin_at": "Thu, 24 Oct 2024 09:56:44 GMT",
            "process_duation": 0.54213,
            "progress": 0.0,
            "progress_msg": "Task dispatched...",
            "run": "2",
            "size": 17966,
            "source_type": "local",
            "status": "1",
            "thumbnail": "",
            "token_count": 8,
            "type": "doc",
            "update_date": "Thu, 24 Oct 2024 11:03:15 GMT",
            "update_time": 1729767795721
        },
        "total": 1
    }
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "You don't own the document 5c5999ec7be811ef9cab0242ac12000e5."
}
```

----------------------------------------

TITLE: Python: Asynchronously Parse Documents in RagFlow Dataset
DESCRIPTION: Shows how to upload multiple documents and then trigger an asynchronous parsing operation for them using their IDs, indicating that the parsing process has begun.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_26

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
```

----------------------------------------

TITLE: MySQL Database Configuration
DESCRIPTION: Defines the connection parameters for the MySQL database used by RAGFlow, including credentials, port, maximum connections, and stale timeout.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_9

LANGUAGE: APIDOC
CODE:
```
mysql:
  name: The MySQL database name. Defaults to rag_flow.
  user: The username for MySQL.
  password: The password for MySQL.
  port: The MySQL serving port inside the Docker container. Defaults to 3306.
  max_connections: The maximum number of concurrent connections to the MySQL database. Defaults to 100.
  stale_timeout: Timeout in seconds.
```

----------------------------------------

TITLE: Configuring RAGFlow Chat Plugin for Server Connection (JSON)
DESCRIPTION: This JSON snippet shows the `config.json` file for the `ragflow_chat` plugin, used to establish a connection with the RAGFlow server. It requires setting the `ragflow_api_key` for authentication and `ragflow_host` to specify the server's address and port. This configuration is crucial for the plugin to leverage RAGFlow's knowledge retrieval capabilities.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/intergrations/chatgpt-on-wechat/plugins/README.md#_snippet_1

LANGUAGE: json
CODE:
```
{
  "ragflow_api_key": "YOUR_API_KEY",
  "ragflow_host": "127.0.0.1:80"
}
```

----------------------------------------

TITLE: Update Agent Failure Response
DESCRIPTION: JSON structure for a failed agent update operation, typically indicating an authorization issue or other error.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_137

LANGUAGE: json
CODE:
```
{
    "code": 103,
    "message": "Only owner of canvas authorized for this operation."
}
```

----------------------------------------

TITLE: List Agents API: Success Response JSON Example
DESCRIPTION: Illustrates the JSON structure returned upon successful retrieval of a list of agents, including detailed agent properties like ID, title, creation/update times, and DSL.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_126

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": [
        {
            "avatar": null,
            "canvas_type": null,
            "create_date": "Thu, 05 Dec 2024 19:10:36 GMT",
            "create_time": 1733397036424,
            "description": null,
            "dsl": {
                "answer": [],
                "components": {
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
                        }
                    ]
                },
                "history": [],
                "messages": [],
                "path": [],
                "reference": []
            },
            "id": "8d9ca0e2b2f911ef9ca20242ac120006",
            "title": "123465",
            "update_date": "Thu, 05 Dec 2024 19:10:56 GMT",
            "update_time": 1733397056801,
            "user_id": "69736c5e723611efb51b0242ac120007"
        }
    ]
}
```

----------------------------------------

TITLE: Running RAGFlow Task Executor Service - Shell
DESCRIPTION: This command launches the RAGFlow task executor service. It uses `LD_PRELOAD` with `jemalloc` for memory optimization and executes `task_executor.py` with an argument of `1`, indicating a specific mode of operation.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_9

LANGUAGE: shell
CODE:
```
JEMALLOC_PATH=$(pkg-config --variable=libdir jemalloc)/libjemalloc.so;
LD_PRELOAD=$JEMALLOC_PATH python rag/svr/task_executor.py 1;
```

----------------------------------------

TITLE: Schema: Successful Response for Creating Chat Session
DESCRIPTION: Defines the JSON structure returned upon successful creation of a chat session. It includes the code field for status and the data object containing details of the newly created session, such as id, chat_id, name, and initial messages.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_80

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "chat_id": "2ca4b22e878011ef88fe0242ac120005",
        "create_date": "Fri, 11 Oct 2024 08:46:14 GMT",
        "create_time": 1728636374571,
        "id": "4606b4ec87ad11efbc4f0242ac120006",
        "messages": [
            {
                "content": "Hi! I am your assistant, can I help you?",
                "role": "assistant"
            }
        ],
        "name": "new session",
        "update_date": "Fri, 11 Oct 2024 08:46:14 GMT",
        "update_time": 1728636374571
    }
}
```

----------------------------------------

TITLE: Example Success JSON Response for Agent Conversation
DESCRIPTION: This JSON object represents a successful response from the agent conversation API. It includes the agent ID, the DSL (Domain Specific Language) graph, and the assistant's initial message, indicating a successful interaction.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_100

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "agent_id": "b4a39922b76611efaa1a0242ac120006",
        "dsl": {
            "answer": [],
            "components": {
                "Answer:GreenReadersDrum": {
                    "downstream": [],
                    "obj": {
                        "component_name": "Answer",
                        "inputs": [],
                        "output": null,
                        "params": {}
                    },
                    "upstream": []
                },
                "begin": {
                    "downstream": [],
                    "obj": {
                        "component_name": "Begin",
                        "inputs": [],
                        "output": {},
                        "params": {}
                    },
                    "upstream": []
                }
            },
            "embed_id": "",
            "graph": {
                "edges": [],
                "nodes": [
                    {
                        "data": {
                            "label": "Begin",
                            "name": "begin"
                        },
                        "dragging": false,
                        "height": 44,
                        "id": "begin",
                        "position": {
                            "x": 53.25688640427177,
                            "y": 198.37155679786412
                        },
                        "positionAbsolute": {
                            "x": 53.25688640427177,
                            "y": 198.37155679786412
                        },
                        "selected": false,
                        "sourcePosition": "left",
                        "targetPosition": "right",
                        "type": "beginNode",
                        "width": 200
                    },
                    {
                        "data": {
                            "form": {},
                            "label": "Answer",
                            "name": "dialog_0"
                        },
                        "dragging": false,
                        "height": 44,
                        "id": "Answer:GreenReadersDrum",
                        "position": {
                            "x": 360.43473114516974,
                            "y": 207.29298425089348
                        },
                        "positionAbsolute": {
                            "x": 360.43473114516974,
                            "y": 207.29298425089348
                        },
                        "selected": false,
                        "sourcePosition": "right",
                        "targetPosition": "left",
                        "type": "logicNode",
                        "width": 200
                    }
                ]
            },
            "history": [],
            "messages": [],
            "path": [
                [
                    "begin"
                ],
                []
            ],
            "reference": []
        },
        "id": "2581031eb7a311efb5200242ac120005",
        "message": [
            {
                "content": "Hi! I'm your smart assistant. What can I do for you?",
                "role": "assistant"
            }
        ],
        "source": "agent",
        "user_id": "69736c5e723611efb51b0242ac120007"
    }
}
```

----------------------------------------

TITLE: Deploying Local Model with Jina (Python/Bash)
DESCRIPTION: Runs the 'jina_server.py' script to deploy a local model, specifying the model name (e.g., 'gpt2'). This script only supports models downloaded from Hugging Face and requires being in the 'rag/svr' directory.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_23

LANGUAGE: bash
CODE:
```
python jina_server.py  --model_name gpt2
```

----------------------------------------

TITLE: APIDOC: DataSet.delete_documents Method
DESCRIPTION: API documentation for the `DataSet.delete_documents` method, which allows deletion of documents by their IDs. If no IDs are specified, all documents in the dataset are deleted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_23

LANGUAGE: APIDOC
CODE:
```
DataSet.delete_documents(ids: list[str] = None)

Parameters:
- ids: `list[list]`
  The IDs of the documents to delete. Defaults to `None`. If it is not specified, all documents in the dataset will be deleted.

Returns:
- Success: No value is returned.
- Failure: `Exception`
```

----------------------------------------

TITLE: API: Update Dataset Response Formats
DESCRIPTION: Illustrates the JSON response structures for both successful and failed update operations on a dataset, including specific error codes and messages.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_22

LANGUAGE: json
CODE:
```
{
    "code": 0 
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "Can't change tenant_id."
}
```

----------------------------------------

TITLE: Activating Python Virtual Environment - Bash
DESCRIPTION: These commands activate the Python virtual environment created by 'uv' and set the `PYTHONPATH` environment variable to the current directory. This ensures that Python scripts can find RAGFlow modules correctly.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_7

LANGUAGE: bash
CODE:
```
source .venv/bin/activate
export PYTHONPATH=$(pwd)
```

----------------------------------------

TITLE: JSON Response: Chat Failure due to Missing Question
DESCRIPTION: This JSON snippet represents a failure response from a chat interaction. It indicates an error with code 102 and a message stating that the 'question' parameter is required, suggesting an invalid or incomplete request.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_110

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "`question` is required."
}
```

----------------------------------------

TITLE: Delete Agent API Endpoint Definition
DESCRIPTION: Defines the HTTP method, URL, and required headers for deleting an agent by its ID. This operation requires authentication.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_138

LANGUAGE: APIDOC
CODE:
```
API Endpoint:
Method: DELETE
URL: /api/v1/agents/{agent_id}
Description: Delete an agent by id.
Headers:
  - 'Content-Type: application/json'
  - 'Authorization: Bearer <YOUR_API_KEY>'
```

----------------------------------------

TITLE: Configure Hugging Face Mirror for RAGFlow Module Downloads
DESCRIPTION: To resolve FileNotFoundError when RAGFlow cannot access huggingface.co for OCR and embedding modules, configure hf-mirror.com as the endpoint. This involves stopping containers, uncommenting the HF_ENDPOINT variable in the .env file, and restarting Docker.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/faq.mdx#_snippet_3

LANGUAGE: bash
CODE:
```
cd ragflow/docker/
docker compose down

# Uncomment the following line in ragflow/docker/.env:
HF_ENDPOINT=https://hf-mirror.com

docker compose up -d
```

----------------------------------------

TITLE: API Reference: Delete Documents
DESCRIPTION: Deletes documents by their IDs from a specified dataset. This operation requires authentication and a JSON body containing the document IDs to be deleted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_38

LANGUAGE: APIDOC
CODE:
```
Method: DELETE
URL: /api/v1/datasets/{dataset_id}/documents
Headers:
  Content-Type: application/json
  Authorization: Bearer <YOUR_API_KEY>
Body:
  "ids": list[string]
Request Parameters:
  dataset_id (Path parameter): The associated dataset ID.
  "ids" (Body parameter, list[string]): The IDs of the documents to delete. If it is not specified, all documents in the specified dataset will be deleted.
```

----------------------------------------

TITLE: Chat Assistant Creation API Request Parameters
DESCRIPTION: Detailed specification of parameters required to create or configure a chat assistant, including LLM and prompt settings.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_62

LANGUAGE: APIDOC
CODE:
```
Request parameters:
- "name": (Body parameter), string, Required
  The name of the chat assistant.
- "avatar": (Body parameter), string
  Base64 encoding of the avatar.
- "dataset_ids": (Body parameter), list[string]
  The IDs of the associated datasets.
- "llm": (Body parameter), object
  The LLM settings for the chat assistant to create. If it is not explicitly set, a JSON object with the following values will be generated as the default. An `llm` JSON object contains the following attributes:
  - "model_name": string
    The chat model name. If not set, the user's default chat model will be used.
  - "temperature": float
    Controls the randomness of the model's predictions. A lower temperature results in more conservative responses, while a higher temperature yields more creative and diverse responses. Defaults to 0.1.
  - "top_p": float
    Also known as “nucleus sampling”, this parameter sets a threshold to select a smaller set of words to sample from. It focuses on the most likely words, cutting off the less probable ones. Defaults to 0.3
  - "presence_penalty": float
    This discourages the model from repeating the same information by penalizing words that have already appeared in the conversation. Defaults to 0.4.
  - "frequency penalty": float
    Similar to the presence penalty, this reduces the model’s tendency to repeat the same words frequently. Defaults to 0.7.
- "prompt": (Body parameter), object
  Instructions for the LLM to follow. If it is not explicitly set, a JSON object with the following values will be generated as the default. A `prompt` JSON object contains the following attributes:
  - "similarity_threshold": float
    RAGFlow employs either a combination of weighted keyword similarity and weighted vector cosine similarity, or a combination of weighted keyword similarity and weighted reranking score during retrieval. This argument sets the threshold for similarities between the user query and chunks. If a similarity score falls below this threshold, the corresponding chunk will be excluded from the results. The default value is 0.2.
  - "keywords_similarity_weight": float
    This argument sets the weight of keyword similarity in the hybrid similarity score with vector cosine similarity or reranking model similarity. By adjusting this weight, you can control the influence of keyword similarity in relation to other similarity measures. The default value is 0.7.
  - "top_n": int
    This argument specifies the number of top chunks with similarity scores above the `similarity_threshold` that are fed to the LLM. The LLM will *only* access these 'top N' chunks. The default value is 6.
  - "variables": object[]
    This argument lists the variables to use in the 'System' field of **Chat Configurations**. Note that:
    - "knowledge" is a reserved variable, which represents the retrieved chunks.
    - All the variables in 'System' should be curly bracketed.
    - The default value is [{"key": "knowledge", "optional": true}].
  - "rerank_model": string
    If it is not specified, vector cosine similarity will be used; otherwise, reranking score will be used.
  - "top_k": int
    Refers to the process of reordering or selecting the top-k items from a list or set based on a specific ranking criterion. Default to 1024.
  - "empty_response": string
    If nothing is retrieved in the dataset for the user's question, this will be used as the response. To allow the LLM to improvise when nothing is found, leave this blank.
  - "opener": string
    The opening greeting for the user. Defaults to "Hi! I am your assistant, can I help you?".
  - "show_quote": boolean
    Indicates whether the source of text should be displayed. Defaults to true.
  - "prompt": string
    The prompt content.
```

----------------------------------------

TITLE: Python: Download RagFlow Document Content
DESCRIPTION: Illustrates how to download a document's content using the RagFlow SDK. It initializes the SDK, retrieves a dataset and a document, then calls `doc.download()` to save the content to a local file.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_19

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
dataset = rag_object.list_datasets(id="id")
dataset = dataset[0]
doc = dataset.list_documents(id="wdfxb5t547d")
doc = doc[0]
open("~/ragflow.txt", "wb+").write(doc.download())
print(doc)
```

----------------------------------------

TITLE: Update Agent API: cURL Request Example
DESCRIPTION: Provides a cURL command example for sending a PUT request to update an agent by its ID, demonstrating how to include the agent ID in the URL and the updated fields in the JSON body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_134

LANGUAGE: bash
CODE:
```
curl --request PUT \
     --url http://{address}/api/v1/agents/58af890a2a8911f0a71a11b922ed82d6 \
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

TITLE: Curl Example: Stop Parsing Documents
DESCRIPTION: Example `curl` command to stop the parsing process for specific documents in a dataset. It demonstrates the DELETE method, URL, headers, and the JSON body with document IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_47

LANGUAGE: bash
CODE:
```
curl --request DELETE \
     --url http://{address}/api/v1/datasets/{dataset_id}/chunks \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "document_ids": ["97a5f1c2759811efaa500242ac120004","97ad64b6759811ef9fc30242ac120004"]
     }'
```

----------------------------------------

TITLE: Defining Metadata for LLM Tool Plugin in Python
DESCRIPTION: This snippet defines the `get_metadata` class method, which provides a `LLMToolMetadata` object describing the tool. This metadata includes the tool's name, display names, descriptions for both LLM and RAGFlow frontend, and detailed parameter definitions, including type, description, and required status.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/plugin/README.md#_snippet_2

LANGUAGE: Python
CODE:
```
@classmethod
def get_metadata(cls) -> LLMToolMetadata:
    return {
        # Name of this tool, providing to LLM
        "name": "bad_calculator",
        # Display name of this tool, providing to RAGFlow frontend
        "displayName": "$t:bad_calculator.name",
        # Description of the usage of this tool, providing to LLM
        "description": "A tool to calculate the sum of two numbers (will give wrong answer)",
        # Description of this tool, providing to RAGFlow frontend
        "displayDescription": "$t:bad_calculator.description",
        # Parameters of this tool
        "parameters": {
            # The first parameter - a
            "a": {
                # Parameter type, options are: number, string, or whatever the LLM can recognise
                "type": "number",
                # Description of this parameter, providing to LLM
                "description": "The first number",
                # Description of this parameter, provding to RAGFlow frontend
                "displayDescription": "$t:bad_calculator.params.a",
                # Whether this parameter is required
                "required": True
            },
            # The second parameter - b
            "b": {
                "type": "number",
                "description": "The second number",
                "displayDescription": "$t:bad_calculator.params.b",
                "required": True
            }
        }
    }
```

----------------------------------------

TITLE: APIDOC: Delete Chat Assistants Method
DESCRIPTION: API documentation for the `RAGFlow.delete_chats` method, which allows for the deletion of one or more chat assistants by their IDs. If no IDs are provided, all chat assistants in the system will be deleted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_45

LANGUAGE: APIDOC
CODE:
```
RAGFlow.delete_chats(ids: list[str] = None)
Parameters:
  ids: list[str] - The IDs of the chat assistants to delete. Defaults to None. If it is empty or not specified, all chat assistants in the system will be deleted.
Returns:
  Success: No value is returned.
  Failure: Exception
```

----------------------------------------

TITLE: Monitor Sandbox Executor Manager Logs
DESCRIPTION: Commands to view the real-time logs of the sandbox executor manager container for monitoring purposes.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/sandbox_quickstart.md#_snippet_3

LANGUAGE: bash
CODE:
```
docker logs -f sandbox-executor-manager
```

LANGUAGE: bash
CODE:
```
make logs
```

----------------------------------------

TITLE: Setting Agent Welcome Message (Plaintext)
DESCRIPTION: This snippet defines the initial welcome message or 'opener' for the Text2SQL agent. It provides a friendly introduction to the user, indicating the agent's role as an electronic products online store business data analysis assistant and prompting the user for their query.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/text2sql_agent.md#_snippet_9

LANGUAGE: plaintext
CODE:
```
Hi! I'm your electronic products online store business data analysis assistant. What can I do for you?
```

----------------------------------------

TITLE: Agent Session Creation API Endpoint Details
DESCRIPTION: Defines the HTTP method, URL structure, required headers, and body parameters for initiating a new session with an agent.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_95

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/agents/{agent_id}/sessions?user_id={user_id}
Headers:
  'content-Type: application/json' or 'multipart/form-data'
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  the required parameters: str
  other parameters: The parameters specified in the Begin component.
```

----------------------------------------

TITLE: Example: Chat Completions Success Response (No Session ID)
DESCRIPTION: Shows the JSON structure of a successful response from the chat completions API when no session ID is initially provided. It includes the generated answer, a new session ID, and other relevant data fields.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_91

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "message": "",
    "data": {
        "answer": "Hi! I'm your assistant, what can I do for you?",
        "reference": {},
        "audio_binary": null,
        "id": null,
        "session_id": "b01eed84b85611efa0e90242ac120005"
    }
}
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "message": "",
    "data": true
}
```

----------------------------------------

TITLE: API: Delete Datasets Request Parameters and Responses
DESCRIPTION: Describes the request parameters for deleting datasets, allowing for selective or complete deletion based on provided IDs. Includes JSON examples for successful and failed responses.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_18

LANGUAGE: APIDOC
CODE:
```
Request parameters:
  "ids": list[string] or null (Body parameter, Required)
    Specifies the datasets to delete:
    - If null, all datasets will be deleted.
    - If an array of IDs, only the specified datasets will be deleted.
    - If an empty array, no datasets will be deleted.
```

LANGUAGE: json
CODE:
```
{
    "code": 0 
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "You don't own the dataset."
}
```

----------------------------------------

TITLE: Delete Datasets API Request Example with cURL
DESCRIPTION: A cURL command example demonstrating how to send a DELETE request to remove specific datasets by their IDs, including necessary headers for content type and authorization.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_17

LANGUAGE: bash
CODE:
```
curl --request DELETE \
     --url http://{address}/api/v1/datasets \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
     "ids": ["d94a8dc02c9711f0930f7fbc369eab6d", "e94a8dc02c9711f0930f7fbc369eab6e"]
     }'
```

----------------------------------------

TITLE: API: Update Dataset Configuration with cURL Example
DESCRIPTION: Provides a cURL command example for updating a dataset's name, demonstrating how to construct the PUT request with necessary headers and a JSON body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_20

LANGUAGE: bash
CODE:
```
curl --request PUT \
     --url http://{address}/api/v1/datasets/{dataset_id} \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "name": "updated_dataset"
     }'
```

----------------------------------------

TITLE: RAGFlow Dataset Deletion API Reference
DESCRIPTION: API reference for deleting datasets. Specifies parameters for identifying datasets to delete and details return values.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_7

LANGUAGE: APIDOC
CODE:
```
ids: list[str] or None, *Required*
  The IDs of the datasets to delete. Defaults to `None`.
  - If `None`, all datasets will be deleted.
  - If an array of IDs, only the specified datasets will be deleted.
  - If an empty array, no datasets will be deleted.
Returns:
- Success: No value is returned.
- Failure: `Exception`
```

----------------------------------------

TITLE: Stopping RAGFlow Containers (Docker Compose)
DESCRIPTION: This command stops all currently running Docker containers defined in the `docker-compose.yml` file. The `-v` flag also removes associated volumes, which will clear existing data. This is a prerequisite for changing the document engine.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/switch_doc_engine.md#_snippet_0

LANGUAGE: bash
CODE:
```
docker compose -f docker/docker-compose.yml down -v
```

----------------------------------------

TITLE: Query API Failure Response Example
DESCRIPTION: Provides an example of the JSON response structure when a query API request fails. It typically includes an error code and a descriptive message indicating the reason for the failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_59

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "`datasets` is required."
}
```

----------------------------------------

TITLE: Failed Chat Assistant Operation Response JSON
DESCRIPTION: Example JSON structure returned when an operation on a chat assistant fails, providing an error code and a descriptive message.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_64

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "Duplicated chat name in creating dataset."
}
```

----------------------------------------

TITLE: Example: Chat Completions Failure Response
DESCRIPTION: Illustrates the JSON response structure for a failed chat completions request. It typically includes an error code and a descriptive message indicating the reason for the failure, such as missing required parameters.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_93

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "Please input your question."
}
```

----------------------------------------

TITLE: Update Agent Success Response
DESCRIPTION: JSON structure for a successful agent update operation, indicating the operation completed successfully.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_136

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": true,
    "message": "success"
}
```

----------------------------------------

TITLE: Categorize Component Model Configuration
DESCRIPTION: Configures the Large Language Model (LLM) used by the Categorize component, including model selection and parameters that influence response generation such as randomness and token diversity.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/agent_component_reference/categorize.mdx#_snippet_1

LANGUAGE: APIDOC
CODE:
```
Model:
  Model: The chat model to use. Ensure it's set correctly on the Model providers page.
  Freedom: A shortcut to Temperature, Top P, Presence penalty, and Frequency penalty settings.
    - Improvise: Produces more creative responses.
    - Precise: (Default) Produces more conservative responses.
    - Balance: A middle ground between Improvise and Precise.
  Temperature: The randomness level of the model's output. Default: 0.1.
    - Lower values lead to more deterministic outputs.
    - Higher values lead to more creative and varied outputs.
  Top P: Nucleus sampling. Default: 0.3.
    - Reduces the likelihood of generating repetitive or unnatural text.
  Presence penalty: Encourages the model to include a more diverse range of tokens. Default: 0.4.
    - A higher value results in the model being more likely to generate tokens not yet included.
  Frequency penalty: Discourages the model from repeating the same words or phrases. Default: 0.7.
    - A higher value results in the model being more conservative in its use of repeated tokens.
```

----------------------------------------

TITLE: Launch RAGFlow Backend Service
DESCRIPTION: Activates the Python virtual environment, sets the `PYTHONPATH` to the current directory, and executes a shell script to start the RAGFlow backend service.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_20

LANGUAGE: bash
CODE:
```
source .venv/bin/activate
export PYTHONPATH=$(pwd)
bash docker/launch_backend_service.sh
```

----------------------------------------

TITLE: Example: Retrieve Chat Assistants using cURL
DESCRIPTION: Provides a cURL command demonstrating how to make a GET request to the /api/v1/chats endpoint, including URL parameters and the authorization header.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_75

LANGUAGE: bash
CODE:
```
curl --request GET \
     --url http://{address}/api/v1/chats?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={chat_name}&id={chat_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

----------------------------------------

TITLE: Retrieve Datasets from RagFlow API
DESCRIPTION: This API endpoint allows users to retrieve a list of datasets. It supports filtering by page, page size, order, and specific dataset name or ID, providing detailed information about each dataset.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_24

LANGUAGE: bash
CODE:
```
curl --request GET \
     --url http://{address}/api/v1/datasets?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={dataset_name}&id={dataset_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

LANGUAGE: APIDOC
CODE:
```
Request Parameters:
- page: (Filter parameter) Specifies the page on which the datasets will be displayed. Defaults to `1`.
- page_size: (Filter parameter) The number of datasets on each page. Defaults to `30`.
- orderby: (Filter parameter) The field by which datasets should be sorted. Available options:
  - `create_time` (default)
  - `update_time`
- desc: (Filter parameter) Indicates whether the retrieved datasets should be sorted in descending order. Defaults to `true`.
- name: (Filter parameter) The name of the dataset to retrieve.
- id: (Filter parameter) The ID of the dataset to retrieve.
```

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": [
        {
            "avatar": "",
            "chunk_count": 59,
            "create_date": "Sat, 14 Sep 2024 01:12:37 GMT",
            "create_time": 1726276357324,
            "created_by": "69736c5e723611efb51b0242ac120007",
            "description": null,
            "document_count": 1,
            "embedding_model": "BAAI/bge-large-zh-v1.5",
            "id": "6e211ee0723611efa10a0242ac120007",
            "language": "English",
            "name": "mysql",
            "chunk_method": "naive",
            "parser_config": {
                "chunk_token_num": 8192,
                "delimiter": "\\n",
                "entity_types": [
                    "organization",
                    "person",
                    "location",
                    "event",
                    "time"
                ]
            },
            "permission": "me",
            "similarity_threshold": 0.2,
            "status": "1",
            "tenant_id": "69736c5e723611efb51b0242ac120007",
            "token_num": 12744,
            "update_date": "Thu, 10 Oct 2024 04:07:23 GMT",
            "update_time": 1728533243536,
            "vector_similarity_weight": 0.3
        }
    ]
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "The dataset doesn't exist"
}
```

----------------------------------------

TITLE: Update Document API Request Parameters
DESCRIPTION: Details the parameters required for updating a document, including path parameters, body parameters, and the configurable parser settings based on the chunking method.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_27

LANGUAGE: APIDOC
CODE:
```
Request parameters:
- `dataset_id`: (Path parameter)
  The ID of the associated dataset.
- `document_id`: (Path parameter)
  The ID of the document to update.
- "name": (Body parameter), `string`
- "meta_fields": (Body parameter), `dict[str, Any]` The meta fields of the document.
- "chunk_method": (Body parameter), `string`
  The parsing method to apply to the document:
  - "naive": General
  - "manual`: Manual
  - "qa": Q&A
  - "table": Table
  - "paper": Paper
  - "book": Book
  - "laws": Laws
  - "presentation": Presentation
  - "picture": Picture
  - "one": One
  - "email": Email
- "parser_config": (Body parameter), `object`
  The configuration settings for the dataset parser. The attributes in this JSON object vary with the selected "chunk_method":
  - If "chunk_method" is "naive", the "parser_config" object contains the following attributes:
    - "chunk_token_count": Defaults to `256`.
    - "layout_recognize": Defaults to `true`.
    - "html4excel": Indicates whether to convert Excel documents into HTML format. Defaults to `false`.
    - "delimiter": Defaults to `"\n"`.
    - "task_page_size": Defaults to `12`. For PDF only.
    - "raptor": RAPTOR-specific settings. Defaults to: `{"use_raptor": false}`.
  - If "chunk_method" is "qa", "manuel", "paper", "book", "laws", or "presentation", the "parser_config" object contains the following attribute:
    - "raptor": RAPTOR-specific settings. Defaults to: `{"use_raptor": false}`.
  - If "chunk_method" is "table", "picture", "one", or "email", "parser_config" is an empty JSON object.
```

----------------------------------------

TITLE: APIDOC: Document Download Method
DESCRIPTION: Specifies the `Document.download()` method, which retrieves the content of the current document. It returns the document's content as bytes.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_18

LANGUAGE: APIDOC
CODE:
```
Document.download() -> bytes

Downloads the current document.

Returns:
The downloaded document in bytes.
```

----------------------------------------

TITLE: JSON Response: Example Document List Success
DESCRIPTION: Illustrates a successful JSON response containing a list of document metadata, including details like ID, name, size, and parsing configuration.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_36

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": {
        "docs": [
            {
                "chunk_count": 0,
                "create_date": "Mon, 14 Oct 2024 09:11:01 GMT",
                "create_time": 1728897061948,
                "created_by": "69736c5e723611efb51b0242ac120007",
                "id": "3bcfbf8a8a0c11ef8aba0242ac120006",
                "knowledgebase_id": "7898da028a0511efbf750242ac120005",
                "location": "Test_2.txt",
                "name": "Test_2.txt",
                "parser_config": {
                    "chunk_token_count": 128,
                    "delimiter": "\n",
                    "layout_recognize": true,
                    "task_page_size": 12
                },
                "chunk_method": "naive",
                "process_begin_at": null,
                "process_duation": 0.0,
                "progress": 0.0,
                "progress_msg": "",
                "run": "0",
                "size": 7,
                "source_type": "local",
                "status": "1",
                "thumbnail": null,
                "token_count": 0,
                "type": "doc",
                "update_date": "Mon, 14 Oct 2024 09:11:01 GMT",
                "update_time": 1728897061948
            }
        ],
        "total": 1
    }
}
```

----------------------------------------

TITLE: Download Document API Endpoint
DESCRIPTION: Describes the GET endpoint for downloading a document from a specified dataset, including URL, method, headers, and output.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_29

LANGUAGE: APIDOC
CODE:
```
GET /api/v1/datasets/{dataset_id}/documents/{document_id}
Downloads a document from a specified dataset.

Request:
- Method: GET
- URL: /api/v1/datasets/{dataset_id}/documents/{document_id}
- Headers:
  - 'Authorization: Bearer <YOUR_API_KEY>'
- Output:
  - '{PATH_TO_THE_FILE}'
```

----------------------------------------

TITLE: Download Document API Request Parameters
DESCRIPTION: Details the path parameters required for downloading a document.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_31

LANGUAGE: APIDOC
CODE:
```
Request parameters:
- `dataset_id`: (Path parameter)
  The associated dataset ID.
- `documents_id`: (Path parameter)
  The ID of the document to download.
```

----------------------------------------

TITLE: API Failure Response Example
DESCRIPTION: Demonstrates the JSON structure for an API error response. It includes a numeric 'code' and a human-readable 'message' explaining the reason for the failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_10

LANGUAGE: json
CODE:
```
{
  "code": 102,
  "message": "The last content of this conversation is not from user."
}
```

----------------------------------------

TITLE: API Reference: Add Chunk to Document
DESCRIPTION: Adds a new chunk to a specified document within a specified dataset. This is a POST request.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_50

LANGUAGE: APIDOC
CODE:
```
Method: POST
URL: /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks
```

----------------------------------------

TITLE: APIDOC: DataSet.async_parse_documents Method
DESCRIPTION: API documentation for the `DataSet.async_parse_documents` method, which initiates asynchronous parsing for specified documents within the current dataset.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_25

LANGUAGE: APIDOC
CODE:
```
DataSet.async_parse_documents(document_ids:list[str]) -> None

Parameters:
- document_ids: `list[str]`, *Required*
  The IDs of the documents to parse.

Returns:
- Success: No value is returned.
- Failure: `Exception`
```

----------------------------------------

TITLE: Delete RAGFlow Agent
DESCRIPTION: This snippet demonstrates how to delete an agent using its unique ID. The operation returns nothing on success and an Exception on failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_70

LANGUAGE: APIDOC
CODE:
```
RAGFlow.delete_agent(
  agent_id: str
) -> None

Parameters:
  agent_id: str - Specifies the id of the agent to be deleted.

Returns:
  Success: Nothing.
  Failure: Exception.
```

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow
rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
rag_object.delete_agent("58af890a2a8911f0a71a11b922ed82d6")
```

----------------------------------------

TITLE: Launch RAGFlow Frontend Service
DESCRIPTION: Starts the RAGFlow frontend development server using `npm run dev`, making the web interface accessible.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_22

LANGUAGE: bash
CODE:
```
npm run dev
```

----------------------------------------

TITLE: List Chat Assistants with RAGFlow SDK
DESCRIPTION: Retrieves a list of available chat assistants. This method allows filtering by name and returns `Chat` objects. It handles potential exceptions on failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_48

LANGUAGE: APIDOC
CODE:
```
RAGFlow.list_chats(name: str = None) -> list[Chat]
  name: The name of the chat assistant to retrieve. Defaults to None.
Returns:
  Success: A list of Chat objects.
  Failure: Exception.
```

LANGUAGE: python
CODE:
```
from ragflow_sdk import RAGFlow

rag_object = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://<YOUR_BASE_URL>:9380")
for assistant in rag_object.list_chats():
    print(assistant)
```

----------------------------------------

TITLE: Delete Chunks from Document Example
DESCRIPTION: Python example demonstrating how to initialize RAGFlow, retrieve a dataset and document, add a chunk, and then delete specific chunks by their IDs from that document.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_34

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
doc.delete_chunks(["id_1","id_2"])
```

----------------------------------------

TITLE: MinIO Docker Environment Variables
DESCRIPTION: Defines environment variables for configuring the MinIO object storage service within the Docker environment, covering console port, API port, username, and password.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_4

LANGUAGE: APIDOC
CODE:
```
MINIO_CONSOLE_PORT:
  Description: "The port used to expose the MinIO console interface to the host machine, allowing external access to the web-based console running inside the Docker container."
  Default: "9001"
MINIO_PORT:
  Description: "The port used to expose the MinIO API service to the host machine, allowing external access to the MinIO object storage service inside the Docker container."
  Default: "9000"
MINIO_USER:
  Description: "The username for MinIO."
MINIO_PASSWORD:
  Description: "The password for MinIO."
```

----------------------------------------

TITLE: MySQL Docker Environment Variables
DESCRIPTION: Defines environment variables for configuring the MySQL database service within the Docker environment, covering password and external port.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_3

LANGUAGE: APIDOC
CODE:
```
MYSQL_PASSWORD:
  Description: "The password for MySQL."
MYSQL_PORT:
  Description: "The port used to expose the MySQL service to the host machine, allowing external access to the MySQL database running inside the Docker container."
  Default: "5455"
```

----------------------------------------

TITLE: Pulling Ollama Model on Windows (CMD)
DESCRIPTION: Pulls a specified Ollama model (e.g., 'qwen2:latest') from the Ollama registry. This command is executed in a new terminal after the Ollama service is running.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_17

LANGUAGE: cmd
CODE:
```
ollama.exe pull <model_name>
```

----------------------------------------

TITLE: Running Layout/TSR Recognition Test Program in DeepDoc (Bash)
DESCRIPTION: This command demonstrates how to execute the `t_recognizer.py` test program within DeepDoc for layout or table structure recognition (TSR). It outlines the available command-line options, including specifying input files, an output directory, a confidence threshold for detections, and the specific task mode (layout or tsr). This program allows users to evaluate DeepDoc's recognition capabilities.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/deepdoc/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python deepdoc/vision/t_recognizer.py -h
usage: t_recognizer.py [-h] --inputs INPUTS [--output_dir OUTPUT_DIR] [--threshold THRESHOLD] [--mode {layout,tsr}]

options:
  -h, --help            show this help message and exit
  --inputs INPUTS       Directory where to store images or PDFs, or a file path to a single image or PDF
  --output_dir OUTPUT_DIR
                        Directory where to store the output images. Default: './layouts_outputs'
  --threshold THRESHOLD
                        A threshold to filter out detections. Default: 0.5
  --mode {layout,tsr}   Task mode: layout recognition or table structure recognition
```

----------------------------------------

TITLE: Running OCR Test Program in DeepDoc (Bash)
DESCRIPTION: This command shows how to run the `t_ocr.py` test program in DeepDoc to perform Optical Character Recognition (OCR). It displays the command-line arguments for specifying input files (images or PDFs) and an optional output directory for the OCR results. This program helps users test the OCR capabilities of DeepDoc.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/deepdoc/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
python deepdoc/vision/t_ocr.py -h
usage: t_ocr.py [-h] --inputs INPUTS [--output_dir OUTPUT_DIR]

options:
  -h, --help            show this help message and exit
  --inputs INPUTS       Directory where to store images or PDFs, or a file path to a single image or PDF
  --output_dir OUTPUT_DIR
                        Directory where to store the output images. Default: './ocr_outputs'
```

----------------------------------------

TITLE: Initializing Ollama with IPEX-LLM on Linux (Bash)
DESCRIPTION: These commands activate the `llm-cpp` Conda environment, which is set up for IPEX-LLM, and then initialize the Ollama service. This prepares Ollama to run with IPEX-LLM accelerations on Linux systems.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_11

LANGUAGE: bash
CODE:
```
conda activate llm-cpp
init-ollama
```

----------------------------------------

TITLE: Delete Agent API Request Parameters
DESCRIPTION: Defines the path parameter required for deleting an agent, which is the agent's unique identifier.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_140

LANGUAGE: APIDOC
CODE:
```
Request parameters:
- `agent_id`: (Path parameter), `string`
  The id of the agent to be deleted.
```

----------------------------------------

TITLE: Cloning RAGFlow Repository
DESCRIPTION: Clones the RAGFlow GitHub repository to obtain the latest code. This is the initial step for any upgrade process, ensuring your local codebase is synchronized with the remote repository.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/upgrade_ragflow.mdx#_snippet_0

LANGUAGE: bash
CODE:
```
git clone https://github.com/infiniflow/ragflow.git
```

----------------------------------------

TITLE: Starting Xinference Local Instance (Bash)
DESCRIPTION: This command starts a local Xinference instance, making it accessible on all network interfaces (`0.0.0.0`) via port `9997`. This is a prerequisite for launching and serving local AI models.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_8

LANGUAGE: bash
CODE:
```
$ xinference-local --host 0.0.0.0 --port 9997
```

----------------------------------------

TITLE: Delete Chunks in Ragflow Document (DELETE)
DESCRIPTION: This API endpoint allows for the deletion of specific chunks from a document within a dataset, identified by their IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_53

LANGUAGE: APIDOC
CODE:
```
Method: DELETE
URL: /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks
```

----------------------------------------

TITLE: Clone RAGFlow Git Repository
DESCRIPTION: This snippet provides the command to clone the RAGFlow GitHub repository, which is the first step to obtaining the project source code. It fetches the entire repository to your local machine.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
$ git clone https://github.com/infiniflow/ragflow.git
```

----------------------------------------

TITLE: Update Agent API: Endpoint and Request Overview
DESCRIPTION: Specifies the HTTP method (PUT), URL path (including `agent_id`), required headers, and the expected structure of the request body for updating an existing agent.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_133

LANGUAGE: APIDOC
CODE:
```
Method: PUT
URL: /api/v1/agents/{agent_id}
Headers:
  'Content-Type: application/json
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "title": string
  "description": string
  "dsl": object
```

----------------------------------------

TITLE: API Documentation: Generate Related Questions
DESCRIPTION: Comprehensive documentation for the POST /v1/sessions/related_questions endpoint. This API generates five to ten alternative question strings from a user's original query to retrieve more relevant search results, requiring a Bearer Login Token.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_119

LANGUAGE: APIDOC
CODE:
```
Endpoint: POST /v1/sessions/related_questions
Description: Generates five to ten alternative question strings from the user's original query to retrieve more relevant search results. Requires a Bearer Login Token.

Request:
  Method: POST
  URL: /v1/sessions/related_questions
  Headers:
    'content-Type: application/json'
    'Authorization: Bearer <YOUR_LOGIN_TOKEN>'
  Body:
    "question": string - The original user question.

Request Parameters:
  "question": (Body Parameter), string The original user question.

Response (Success):
  code: 0
  data: list[string] - A list of generated alternative questions.
  message: "success"

Response (Failure):
  code: 401
  data: null
  message: "<Unauthorized '401: Unauthorized'>"
```

----------------------------------------

TITLE: API Documentation: List Agent Sessions
DESCRIPTION: This section documents the API endpoint for listing sessions associated with a specific agent. It details the GET method, URL structure, required headers, and all available query and path parameters with their types, descriptions, and default values.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_111

LANGUAGE: APIDOC
CODE:
```
API Endpoint: GET /api/v1/agents/{agent_id}/sessions
Description: Lists sessions associated with a specified agent.

Request Headers:
  - Authorization: Bearer <YOUR_API_KEY>

Request Parameters:
  - agent_id (Path parameter): The ID of the associated agent.
  - page (Filter parameter, integer): Specifies the page on which the sessions will be displayed. Defaults to 1.
  - page_size (Filter parameter, integer): The number of sessions on each page. Defaults to 30.
  - orderby (Filter parameter, string): The field by which sessions should be sorted. Available options: create_time (default), update_time.
  - desc (Filter parameter, boolean): Indicates whether the retrieved sessions should be sorted in descending order. Defaults to true.
  - id (Filter parameter, string): The ID of the agent session to retrieve.
  - user_id (Filter parameter, string): The optional user-defined ID passed in when creating session.
  - dsl (Filter parameter, boolean): Indicates whether to include the dsl field of the sessions in the response. Defaults to true.
```

LANGUAGE: bash
CODE:
```
curl --request GET \
     --url http://{address}/api/v1/agents/{agent_id}/sessions?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&id={session_id}&user_id={user_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

----------------------------------------

TITLE: cURL Example: Delete Agent Sessions
DESCRIPTION: A cURL command example demonstrating how to send a DELETE request to the /api/v1/agents/{agent_id}/sessions endpoint, specifying session IDs to be deleted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_116

LANGUAGE: bash
CODE:
```
curl --request DELETE \
     --url http://{address}/api/v1/agents/{agent_id}/sessions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "ids": ["test_1", "test_2"]
     }'
```

----------------------------------------

TITLE: Configure Knowledge Graph Entity Types
DESCRIPTION: Defines the types of entities to extract for the knowledge graph. Users can add or remove types to customize extraction based on their specific knowledge base content.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/dataset/construct_knowledge_graph.md#_snippet_0

LANGUAGE: APIDOC
CODE:
```
Entity types (*Required*):
  Description: The types of entities to extract from your knowledge base.
  Default: organization, person, event, category
  Customization: Add or remove types to suit your specific knowledge base.
```

----------------------------------------

TITLE: Switch RAGFlow Document Engine to Infinity
DESCRIPTION: Steps to change the RAGFlow document engine from Elasticsearch to Infinity. This involves stopping Docker containers, updating the 'DOC_ENGINE' variable in 'docker/.env', and restarting the Docker image.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/faq.mdx#_snippet_13

LANGUAGE: bash
CODE:
```
docker compose -f docker/docker-compose.yml down -v
```

LANGUAGE: env
CODE:
```
DOC_ENGINE=${DOC_ENGINE:-infinity}
```

LANGUAGE: bash
CODE:
```
docker compose -f docker-compose.yml up -d
```

----------------------------------------

TITLE: API Reference: Delete Chat Assistants Request Parameters
DESCRIPTION: Details the `ids` body parameter used to specify which chat assistants to delete. If not provided, all chat assistants will be deleted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_71

LANGUAGE: APIDOC
CODE:
```
"ids": (Body parameter), list[string]
  The IDs of the chat assistants to delete. If it is not specified, all chat assistants in the system will be deleted.
```

----------------------------------------

TITLE: JavaScript Example for External API Call with Axios
DESCRIPTION: This JavaScript example showcases an asynchronous 'main' function that uses the 'axios' library to make an HTTP GET request to a specified URL. It demonstrates how to handle successful responses by logging the body and how to catch and log errors during the API call, useful for integrating external services into the Agent.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/agent_component_reference/code.mdx#_snippet_1

LANGUAGE: JavaScript
CODE:
```
    const axios = require('axios');
    async function main(args) {
      try {
        const response = await axios.get('https://github.com/infiniflow/ragflow');
        console.log('Body:', response.data);
      } catch (error) {
        console.error('Error:', error.message);
      }
    }
```

----------------------------------------

TITLE: API: Delete Agent Sessions
DESCRIPTION: Documents the `Agent.delete_sessions` method, used to remove one or more sessions associated with an agent by their IDs. If no IDs are specified, all sessions for the agent are deleted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_63

LANGUAGE: APIDOC
CODE:
```
Agent.delete_sessions(ids: list[str] = None)
Parameters:
  ids: list[str]
    The IDs of the sessions to delete. Defaults to None. If it is not specified, all sessions associated with the agent will be deleted.
Returns:
  Success: No value is returned.
  Failure: Exception
```

----------------------------------------

TITLE: Performing Table Structure Recognition with Deepdoc Python Tool (Bash)
DESCRIPTION: This command executes the Table Structure Recognition (TSR) process using the `t_recognizer.py` script. It identifies and structures complex data tables within input images or PDFs, including elements like columns, rows, and spanning cells. The output directory contains images and HTML pages visualizing the detection results, with content reassembled into LLM-comprehensible sentences.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/deepdoc/README.md#_snippet_5

LANGUAGE: bash
CODE:
```
python deepdoc/vision/t_recognizer.py --inputs=path_to_images_or_pdfs --threshold=0.2 --mode=tsr --output_dir=path_to_store_result
```

----------------------------------------

TITLE: cURL Example for Updating Chat Assistant
DESCRIPTION: A cURL command example demonstrating how to send a PUT request to update a chat assistant's name, including necessary headers and a minimal JSON body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_66

LANGUAGE: bash
CODE:
```
curl --request PUT \
     --url http://{address}/api/v1/chats/{chat_id} \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "name":"Test"
     }'
```

----------------------------------------

TITLE: Document.list_chunks API Reference
DESCRIPTION: API documentation for listing chunks within a document. It specifies parameters for filtering by keywords, pagination (`page`, `page_size`), and retrieving by ID, along with the return type of a list of `Chunk` objects.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_31

LANGUAGE: APIDOC
CODE:
```
Document.list_chunks(keywords: str = None, page: int = 1, page_size: int = 30, id : str = None) -> list[Chunk]

Parameters:
  keywords: `str`
    The keywords used to match chunk content. Defaults to `None`
  page: `int`
    Specifies the page on which the chunks will be displayed. Defaults to `1`.
  page_size: `int`
    The maximum number of chunks on each page. Defaults to `30`.
  id: `str`
    The ID of the chunk to retrieve. Default: `None`

Returns:
  Success: A list of `Chunk` objects.
  Failure: `Exception`.
```

----------------------------------------

TITLE: API: List Agent Sessions
DESCRIPTION: Documents the `Agent.list_sessions` method, which retrieves a list of sessions associated with a specific agent. It details parameters for pagination, sorting, and filtering by ID, along with return types.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_61

LANGUAGE: APIDOC
CODE:
```
Agent.list_sessions(
    page: int = 1, 
    page_size: int = 30, 
    orderby: str = "update_time", 
    desc: bool = True,
    id: str = None
) -> List[Session]
Parameters:
  page: int
    Specifies the page on which the sessions will be displayed. Defaults to 1.
  page_size: int
    The number of sessions on each page. Defaults to 30.
  orderby: str
    The field by which sessions should be sorted. Available options: "create_time", "update_time"(default)
  desc: bool
    Indicates whether the retrieved sessions should be sorted in descending order. Defaults to True.
  id: str
    The ID of the agent session to retrieve. Defaults to None.
Returns:
  Success: A list of Session objects associated with the current agent.
  Failure: Exception.
```

----------------------------------------

TITLE: Defining E-commerce Database Schema - SQL
DESCRIPTION: This SQL snippet defines the schema for an e-commerce database, including 'Customers', 'Products', 'Orders', and 'OrderDetails' tables. Each 'CREATE TABLE' statement specifies column names, data types, constraints (like PRIMARY KEY, AUTO_INCREMENT), and character sets, providing the foundational structure for storing transactional data.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/text2sql_agent.md#_snippet_5

LANGUAGE: SQL
CODE:
```
CREATE TABLE Customers (
  CustomerID int NOT NULL AUTO_INCREMENT,
  UserName varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  Email varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PhoneNumber varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (CustomerID)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Products (
  ProductID int NOT NULL AUTO_INCREMENT,
  ProductName varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  Description text COLLATE utf8mb4_unicode_ci,
  Price decimal(10,2) DEFAULT NULL,
  StockQuantity int DEFAULT NULL,
  PRIMARY KEY (ProductID)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Orders (
  OrderID int NOT NULL AUTO_INCREMENT,
  CustomerID int DEFAULT NULL,
  OrderDate date DEFAULT NULL,
  TotalPrice decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (OrderID),
  KEY CustomerID (CustomerID)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE OrderDetails (
  OrderDetailID int NOT NULL AUTO_INCREMENT,
  OrderID int DEFAULT NULL,
  ProductID int DEFAULT NULL,
  UnitPrice decimal(10,2) DEFAULT NULL,
  Quantity int DEFAULT NULL,
  TotalPrice decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (OrderDetailID),
  KEY OrderID (OrderID),
  KEY ProductID (ProductID)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

----------------------------------------

TITLE: Installing RAGFlow Frontend Dependencies - Bash
DESCRIPTION: These commands navigate into the `web` directory and then use `npm install` to download and set up all required Node.js packages for the RAGFlow frontend application.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_11

LANGUAGE: bash
CODE:
```
cd web
npm install
```

----------------------------------------

TITLE: API: Update Dataset Endpoint and Request Body Schema
DESCRIPTION: Details the PUT endpoint for updating dataset configurations, including URL, required headers, and the structure of the request body with all available parameters and their types.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_19

LANGUAGE: APIDOC
CODE:
```
Update dataset:
  Method: PUT
  URL: /api/v1/datasets/{dataset_id}
  Headers:
    'content-Type: application/json'
    'Authorization: Bearer <YOUR_API_KEY>'
  Body:
    "name": string
    "avatar": string
    "description": string
    "embedding_model": string
    "permission": string
    "chunk_method": string
    "pagerank": int
    "parser_config": object
```

----------------------------------------

TITLE: APIDOC: Update Chat Assistant Attributes Schema
DESCRIPTION: Detailed schema for the `update_message` dictionary used to modify chat assistant properties. It includes fields for basic attributes like name and avatar, as well as nested configurations for LLM behavior and RAG prompt settings.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_43

LANGUAGE: APIDOC
CODE:
```
update_message: dict[str, str|list[str]|dict[]], Required
  "name": str - The revised name of the chat assistant.
  "avatar": str - Base64 encoding of the avatar. Defaults to "".
  "dataset_ids": list[str] - The datasets to update.
  "llm": dict - The LLM settings:
    "model_name": str - The chat model name.
    "temperature": float - Controls the randomness of the model's predictions. A lower temperature results in more conservative responses, while a higher temperature yields more creative and diverse responses.
    "top_p": float - Also known as “nucleus sampling”, this parameter sets a threshold to select a smaller set of words to sample from.
    "presence_penalty": float - This discourages the model from repeating the same information by penalizing words that have appeared in the conversation.
    "frequency penalty": float - Similar to presence penalty, this reduces the model’s tendency to repeat the same words.
  "prompt": dict - Instructions for the LLM to follow:
    "similarity_threshold": float - RAGFlow employs either a combination of weighted keyword similarity and weighted vector cosine similarity, or a combination of weighted keyword similarity and weighted rerank score during retrieval. This argument sets the threshold for similarities between the user query and chunks. If a similarity score falls below this threshold, the corresponding chunk will be excluded from the results. The default value is 0.2.
    "keywords_similarity_weight": float - This argument sets the weight of keyword similarity in the hybrid similarity score with vector cosine similarity or reranking model similarity. By adjusting this weight, you can control the influence of keyword similarity in relation to other similarity measures. The default value is 0.7.
    "top_n": int - This argument specifies the number of top chunks with similarity scores above the similarity_threshold that are fed to the LLM. The LLM will *only* access these 'top N' chunks. The default value is 8.
    "variables": list[dict[]] - This argument lists the variables to use in the 'System' field of Chat Configurations. Note that: 'knowledge' is a reserved variable, which represents the retrieved chunks. All the variables in 'System' should be curly bracketed. The default value is [{"key": "knowledge", "optional": True}].
    "rerank_model": str - If it is not specified, vector cosine similarity will be used; otherwise, reranking score will be used. Defaults to "".
    "empty_response": str - If nothing is retrieved in the dataset for the user's question, this will be used as the response. To allow the LLM to improvise when nothing is retrieved, leave this blank. Defaults to None.
    "opener": str - The opening greeting for the user. Defaults to "Hi! I am your assistant, can I help you?".
    "show_quote": bool - Indicates whether the source of text should be displayed Defaults to True.
    "prompt": str - The prompt content.
Returns:
  Success: No value is returned.
  Failure: Exception
```

----------------------------------------

TITLE: Configure RAGFlow File Size Limit
DESCRIPTION: Instructions to adjust the maximum content length for file uploads in a locally deployed RAGFlow instance. This involves modifying the 'MAX_CONTENT_LENGTH' variable in the 'docker/.env' file and ensuring 'client_max_body_size' in 'nginx/nginx.conf' is updated accordingly.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/faq.mdx#_snippet_12

LANGUAGE: env
CODE:
```
MAX_CONTENT_LENGTH=1073741824
```

LANGUAGE: nginx-conf
CODE:
```
client_max_body_size 1G;
```

----------------------------------------

TITLE: Delete Chunks API Endpoint
DESCRIPTION: Deletes specified chunks from a document within a dataset. If no chunk IDs are provided, all chunks for the document are deleted. Requires authentication and chunk IDs in the request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_54

LANGUAGE: APIDOC
CODE:
```
API Endpoint: DELETE /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks
Description: Deletes specified chunks from a document within a dataset.
Headers:
  - 'Content-Type: application/json'
  - 'Authorization: Bearer <YOUR_API_KEY>'
Path Parameters:
  - dataset_id: The associated dataset ID.
  - document_id: The associated document ID.
Body Parameters:
  - chunk_ids: list[string] - The IDs of the chunks to delete. If not specified, all chunks of the specified document will be deleted.
Responses:
  - Success (200 OK):
    code: 0
  - Failure (Error Code):
    code: 102
    message: string - e.g., '`chunk_ids` is required'
```

LANGUAGE: bash
CODE:
```
curl --request DELETE \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "chunk_ids": ["test_1", "test_2"]
     }'
```

LANGUAGE: json
CODE:
```
{
    "code": 0
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "`chunk_ids` is required"
}
```

----------------------------------------

TITLE: Download Document API Request Example
DESCRIPTION: A cURL command example demonstrating how to download a document using the GET API endpoint, including authorization and output redirection.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_30

LANGUAGE: bash
CODE:
```
curl --request GET \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --output ./ragflow.txt
```

----------------------------------------

TITLE: Implementing Product Analytics and Cookie Retrieval in JavaScript
DESCRIPTION: This snippet defines a utility function to retrieve cookies based on specified prefixes and a main function `productAnalytics` that collects various data points (URL, page view ID, visit UUID, AB test ID, referrer, and specific cookies) and sends them to an analytics endpoint via an XMLHttpRequest POST request. It also includes logic to handle the XHR response and add a script dynamically.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/sdk/python/test/test_sdk_api/test_data/test.html#_snippet_19

LANGUAGE: JavaScript
CODE:
```
kiesWithPrefix = {}; for (var i = 0; i < allCookies.length; i++) { var cookie = allCookies[i].trim(); for (var j = 0; j < arguments.length; j++) { var prefix = arguments[j]; if (cookie.indexOf(prefix) === 0) { var cookieParts = cookie.split('='); var cookieName = cookieParts[0]; var cookieValue = cookieParts.slice(1).join('='); cookiesWithPrefix[cookieName] = decodeURIComponent(cookieValue); break; } } } return cookiesWithPrefix; } function productAnalytics() { var d = {"pr":[1,6,3],"aop":{"2":0,"4":147},"omd5":"6d6bb459461be9d3f11aa7f4f6b6031d"}; d.u = _ezaq.url; d.p = _ezaq.page_view_id; d.v = _ezaq.visit_uuid; d.ab = _ezaq.ab_test_id; d.e = JSON.stringify(_ezaq); d.ref = document.referrer; d.c = getCookiesWithPrefix('active_template', 'ez', 'lp_'); if(typeof ez_utmParams !== 'undefined') { d.utm = ez_utmParams; } var dataText = JSON.stringify(d); var xhr = new XMLHttpRequest(); xhr.open('POST','/ezais/analytics?cb=1', true); xhr.onload = function () { if (xhr.status!=200) { return; } if(document.readyState !== 'loading') { analyticsAddScript(xhr.response); return; } var eventFunc = function() { if(document.readyState === 'loading') { return; } document.removeEventListener('readystatechange', eventFunc, false); analyticsAddScript(xhr.response); }; document.addEventListener('readystatechange', eventFunc, false); }; xhr.setRequestHeader('Content-Type','text/plain'); xhr.send(dataText); } __ez.queue.addFunc("productAnalytics", "productAnalytics", null, true, ['ezaqBaseReady'], false, false, false, true);
```

----------------------------------------

TITLE: Navigating to RAG Server Directory (Bash)
DESCRIPTION: Changes the current directory to 'rag/svr', which is necessary before running the Jina server script.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_22

LANGUAGE: bash
CODE:
```
cd rag/svr
```

----------------------------------------

TITLE: Displaying Recognizer Script Help (Python)
DESCRIPTION: This snippet provides help for the `t_recognizer.py` script, which handles layout and table structure recognition. It details options like `--inputs`, `--output_dir`, `--threshold` for filtering detections, and `--mode` to select between 'layout' or 'tsr' tasks.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/deepdoc/README_zh.md#_snippet_1

LANGUAGE: bash
CODE:
```
python deepdoc/vision/t_recognizer.py -h
usage: t_recognizer.py [-h] --inputs INPUTS [--output_dir OUTPUT_DIR] [--threshold THRESHOLD] [--mode {layout,tsr}]

options:
  -h, --help            show this help message and exit
  --inputs INPUTS       Directory where to store images or PDFs, or a file path to a single image or PDF
  --output_dir OUTPUT_DIR
                        Directory where to store the output images. Default: './layouts_outputs'
  --threshold THRESHOLD
                        A threshold to filter out detections. Default: 0.5
  --mode {layout,tsr}   Task mode: layout recognition or table structure recognition
```

----------------------------------------

TITLE: Stop RAGFlow Frontend and Backend Services
DESCRIPTION: Terminates the RAGFlow frontend and backend processes by killing processes matching specific names (`ragflow_server.py` or `task_executor.py`), used to gracefully shut down services after development.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_23

LANGUAGE: bash
CODE:
```
pkill -f "ragflow_server.py|task_executor.py"
```

----------------------------------------

TITLE: Enable RAGFlow MCP Server in Docker Compose
DESCRIPTION: Configuration snippet for `docker-compose.yml` to enable the RAGFlow Model Context Protocol (MCP) server as an optional component. This involves uncommenting the `services.ragflow.command` section and setting various MCP server parameters like host, port, base URL, script path, mode, and API key for self-host mode within the Docker environment.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/mcp/launch_mcp_server.md#_snippet_1

LANGUAGE: yaml
CODE:
```
  services:
    ragflow:
      ...
      image: ${RAGFLOW_IMAGE}
      # Example configuration to set up an MCP server:
      command:
        - --enable-mcpserver
        - --mcp-host=0.0.0.0
        - --mcp-port=9382
        - --mcp-base-url=http://127.0.0.1:9380
        - --mcp-script-path=/ragflow/mcp/server/server.py
        - --mcp-mode=self-host
        - --mcp-host-api-key=ragflow-xxxxxxx
```

----------------------------------------

TITLE: API Reference: Stop Parsing Documents
DESCRIPTION: Halts the ongoing parsing process for specified documents within a dataset. This is a DELETE request requiring document IDs in the request body.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_46

LANGUAGE: APIDOC
CODE:
```
Method: DELETE
URL: /api/v1/datasets/{dataset_id}/chunks
Headers:
  Content-Type: application/json
  Authorization: Bearer <YOUR_API_KEY>
Body:
  "document_ids": list[string]
Request Parameters:
  dataset_id (Path parameter): The associated dataset ID.
  "document_ids" (Body parameter, list[string], Required): The IDs of the documents for which the parsing should be stopped.
```

----------------------------------------

TITLE: Running OCR on Images or PDFs (Python)
DESCRIPTION: This command executes the `t_ocr.py` script to perform Optical Character Recognition. It requires `--inputs` to specify the path to images or PDFs (a directory or single file) and `--output_dir` to define where the OCR results (images and text files) will be stored.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/deepdoc/README_zh.md#_snippet_3

LANGUAGE: bash
CODE:
```
python deepdoc/vision/t_ocr.py --inputs=path_to_images_or_pdfs --output_dir=path_to_store_result
```

----------------------------------------

TITLE: Building Sandbox Executor Manager Docker Image
DESCRIPTION: This snippet builds the Docker image for the sandbox executor manager. This image orchestrates the secure execution of code snippets within the RAGFlow Sandbox environment.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/sandbox/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
docker build -t sandbox-executor-manager:latest ./executor_manager
```

----------------------------------------

TITLE: Generate Related Questions Failure Response JSON
DESCRIPTION: A JSON response indicating a failure during the generation of related questions, typically due to an unauthorized request.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_122

LANGUAGE: json
CODE:
```
{
    "code": 401,
    "data": null,
    "message": "<Unauthorized '401: Unauthorized'>"
}
```

----------------------------------------

TITLE: Delete Agent Sessions Failure Response JSON
DESCRIPTION: A JSON response indicating a failure during the deletion of agent sessions, typically due to the agent not owning the specified session.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_118

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "The agent doesn't own the session cbd31e52f73911ef93b232903b842af6"
}
```

----------------------------------------

TITLE: Schema: Failed Response for Retrieving Chat Assistants
DESCRIPTION: Defines the JSON structure returned when the retrieval of chat assistants fails, typically indicating an error with code and a descriptive message.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_77

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "The chat doesn't exist"
}
```

----------------------------------------

TITLE: JSON Response: Parse Documents Failure
DESCRIPTION: A failed JSON response for document parsing, often due to missing required parameters like `document_ids`.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_45

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "`document_ids` is required"
}
```

----------------------------------------

TITLE: JSON Response: Stop Parsing Documents Failure
DESCRIPTION: A failed JSON response for stopping document parsing, typically due to missing required parameters.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_49

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "`document_ids` is required"
}
```

----------------------------------------

TITLE: Configure Knowledge Graph Community Report Generation
DESCRIPTION: Determines if the LLM generates an abstract (community report) for each community, which is a cluster of entities linked by relationships, within the knowledge graph. Enabling this option consumes more tokens.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/dataset/construct_knowledge_graph.md#_snippet_3

LANGUAGE: APIDOC
CODE:
```
Community report generation:
  Description: Whether to generate an abstract for each community (cluster of entities linked by relationships).
  Options:
    - Generate: Generate community reports. This option consumes more tokens.
    - Do not generate: (Default) Do not generate community reports.
```

----------------------------------------

TITLE: Testing Standalone RAGFlow Sandbox
DESCRIPTION: This sequence of commands activates the Python virtual environment, sets the `PYTHONPATH`, installs required dependencies using `uv`, and then runs the full security test suite for the standalone RAGFlow Sandbox.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/sandbox/README.md#_snippet_6

LANGUAGE: bash
CODE:
```
source .venv/bin/activate
export PYTHONPATH=$(pwd)
uv pip install -r executor_manager/requirements.txt
uv run tests/sandbox_security_tests_full.py
```

----------------------------------------

TITLE: Start RAGFlow Docker Containers
DESCRIPTION: Starts RAGFlow Docker containers in detached mode. This command is used after configuring the `DOC_ENGINE` variable in the `.env` file, for example, to switch to Infinity.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_10

LANGUAGE: bash
CODE:
```
docker compose -f docker-compose.yml up -d
```

----------------------------------------

TITLE: Obtaining Authorization URL for OAuth/OIDC in Python
DESCRIPTION: This snippet shows how to retrieve the authorization URL from an initialized authentication client. This URL is used to redirect the user to the identity provider's login page to grant permissions to the application.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/api/apps/auth/README.md#_snippet_1

LANGUAGE: python
CODE:
```
auth_url = client.get_authorization_url()
```

----------------------------------------

TITLE: Monitor RAGFlow Application Logs
DESCRIPTION: This command allows you to continuously monitor the application logs generated by RAGFlow, which is useful for general debugging and observing system behavior in real-time.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/faq.mdx#_snippet_8

LANGUAGE: bash
CODE:
```
tail -f ragflow/docker/ragflow-logs/*.log
```

----------------------------------------

TITLE: Launch MCP Server Independently with Docker Compose
DESCRIPTION: This command launches only the MCP server in detached mode, allowing it to run in the background without upgrading RAGFlow. This is useful for scenarios where a standalone MCP instance is required. It necessitates prior preparation of MCP-specific files and modification of the `docker-compose.yml`.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/mcp/launch_mcp_server.md#_snippet_3

LANGUAGE: bash
CODE:
```
docker compose -f docker-compose.yml up -d
```

----------------------------------------

TITLE: Update Chat Assistant Session Name with RAGFlow SDK
DESCRIPTION: Modifies the name of an existing chat session. This method requires a dictionary specifying the new name. No value is returned on success, but an `Exception` is raised on failure.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_50

LANGUAGE: APIDOC
CODE:
```
Session.update(update_message: dict)
  Updates the current session of the current chat assistant.
  Parameters:
    update_message: dict[str, Any], Required
      A dictionary representing the attributes to update, with only one key:
      "name": str The revised name of the session.
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
session = assistant.create_session("session_name")
session.update({"name": "updated_name"})
```

----------------------------------------

TITLE: Configuring API Key for RAGFlow MCP Client in Python
DESCRIPTION: This snippet demonstrates how to include an API key in the client's request headers when connecting to an RAGFlow MCP server running in host mode. It uses `sse_client` to establish a connection, passing the API key within the `headers` dictionary. This is crucial for authentication and authorization with the server.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/mcp/mcp_client_example.md#_snippet_0

LANGUAGE: Python
CODE:
```
async with sse_client("http://localhost:9382/sse", headers={"api_key": "YOUR_KEY_HERE"}) as streams:
    # Rest of your code...
```

----------------------------------------

TITLE: Example: Delete Chat Assistants with cURL
DESCRIPTION: Provides a cURL command demonstrating how to send a DELETE request to remove specific chat assistants by their IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_70

LANGUAGE: bash
CODE:
```
curl --request DELETE \
     --url http://{address}/api/v1/chats \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "ids": ["test_1", "test_2"]
     }'
```

----------------------------------------

TITLE: Create Agent API: Request Body Parameters
DESCRIPTION: Details the required and optional parameters to be included in the JSON request body when creating an agent, specifying their types and purpose.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_130

LANGUAGE: APIDOC
CODE:
```
- `title`: (Body parameter), `string`, *Required*. The title of the agent.
- `description`: (Body parameter), `string`. The description of the agent. Defaults to `None`.
- `dsl`: (Body parameter), `object`, *Required*. The canvas DSL object of the agent.
```

----------------------------------------

TITLE: API Endpoints for Disabling RAGFlow Stream Output
DESCRIPTION: Stream output is enabled by default in RAGFlow's chat assistant and agent. To disable it, use the specific Python or RESTful API endpoints, as this option is not available through the UI.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/faq.mdx#_snippet_2

LANGUAGE: Python
CODE:
```
Python API Endpoints:
- Create chat completion: ./references/python_api_reference.md#create-chat-completion
- Converse with chat assistant: ./references/python_api_reference.md#converse-with-chat-assistant
- Converse with agent: ./references/python_api_reference.md#converse-with-agent
```

LANGUAGE: RESTful
CODE:
```
RESTful API Endpoints:
- Create chat completion: ./references/http_api_reference.md#create-chat-completion
- Converse with chat assistant: ./references/http_api_reference.md#converse-with-chat-assistant
- Converse with agent: ./references/http_api_reference.md#converse-with-agent
```

----------------------------------------

TITLE: Saving RAGFlow Docker Image to Tar File
DESCRIPTION: Saves a specified RAGFlow Docker image (e.g., `infiniflow/ragflow:v0.19.0`) to a `.tar` file. This is a crucial step for offline upgrades, allowing the image to be transferred to an environment without internet access.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/upgrade_ragflow.mdx#_snippet_6

LANGUAGE: bash
CODE:
```
docker save -o ragflow.v0.19.0.tar infiniflow/ragflow:v0.19.0
```

----------------------------------------

TITLE: JSON Response: Delete Documents Failure
DESCRIPTION: A failed JSON response indicating an error during document deletion, typically due to insufficient permissions or incorrect dataset ownership.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_41

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "You do not own the dataset 7898da028a0511efbf750242ac1220005."
}
```

----------------------------------------

TITLE: Running Ollama Model on Windows (CMD)
DESCRIPTION: Runs the specified Ollama model (e.g., 'qwen2:latest') on Windows. This command initiates the model for inference or interaction.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_19

LANGUAGE: cmd
CODE:
```
ollama run qwen2:latest
```

----------------------------------------

TITLE: JSON Response: Example Document List Failure
DESCRIPTION: Illustrates a failed JSON response indicating an authorization or ownership issue when attempting to retrieve document information.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_37

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "You don't own the dataset 7898da028a0511efbf750242ac1220005. "
}
```

----------------------------------------

TITLE: Chunk.update API Reference
DESCRIPTION: API documentation for updating a chunk's content or configurations. It details the `update_message` dictionary parameter, specifying keys like `content`, `important_keywords`, and `available` for modification, and indicates no return value on success.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_35

LANGUAGE: APIDOC
CODE:
```
Chunk.update(update_message: dict)

Parameters:
  update_message: `dict[str, str|list[str]|int]` *Required*
    A dictionary representing the attributes to update, with the following keys:
    "content": `str` The text content of the chunk.
    "important_keywords": `list[str]` A list of key terms or phrases to tag with the chunk.
    "available": `bool` The chunk's availability status in the dataset. Value options:
      False: Unavailable
      True: Available (default)

Returns:
  Success: No value is returned.
  Failure: `Exception`
```

----------------------------------------

TITLE: Configuring UFW Firewall for Ollama (Bash)
DESCRIPTION: This command configures the Uncomplicated Firewall (UFW) on Linux to allow inbound TCP connections on port `11434`. This port is required for the Ollama service to be accessible, which is used by IPEX-LLM.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_10

LANGUAGE: bash
CODE:
```
sudo ufw allow 11434/tcp
```

----------------------------------------

TITLE: Initializing Ollama with IPEX-LLM on Windows (CMD)
DESCRIPTION: These commands, run with administrator privileges in Miniforge Prompt, activate the `llm-cpp` Conda environment and then initialize the Ollama service. This prepares Ollama to run with IPEX-LLM accelerations on Windows systems.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_12

LANGUAGE: cmd
CODE:
```
conda activate llm-cpp
init-ollama.bat
```

----------------------------------------

TITLE: Python Function for String Concatenation
DESCRIPTION: This Python example demonstrates a simple 'main' function that takes two string arguments, 'arg1' and 'arg2', and returns a dictionary containing their concatenated value under the key 'result'. It illustrates basic function definition and return types for dynamic data processing within the Agent.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/agent_component_reference/code.mdx#_snippet_0

LANGUAGE: Python
CODE:
```
    def main(arg1: str, arg2: str) -> dict:
        return {
            "result": arg1 + arg2,
        }
```

----------------------------------------

TITLE: Launching Ollama Service on Linux (Bash)
DESCRIPTION: Configures environment variables for GPU usage, proxy settings, system management, and SYCL cache persistence, then starts the Ollama service on Linux. It ensures all model layers run on Intel GPU and optimizes performance.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_14

LANGUAGE: bash
CODE:
```
export OLLAMA_NUM_GPU=999
export no_proxy=localhost,127.0.0.1
export ZES_ENABLE_SYSMAN=1
source /opt/intel/oneapi/setvars.sh
export SYCL_CACHE_PERSISTENT=1

./ollama serve
```

----------------------------------------

TITLE: Update Agent API Request Parameters
DESCRIPTION: Defines the parameters available for updating an agent. Parameters include path and body parameters, specifying the agent ID, title, description, and DSL object. Only specified parameters will be updated.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_135

LANGUAGE: APIDOC
CODE:
```
Request parameters:
- `agent_id`: (Path parameter), `string`
  The id of the agent to be updated.
- `title`: (Body parameter), `string`
  The title of the agent.
- `description`: (Body parameter), `string`
  The description of the agent.
- `dsl`: (Body parameter), `object`
  The canvas DSL object of the agent.
```

----------------------------------------

TITLE: Schema: Successful Response for Retrieving Chat Assistants
DESCRIPTION: Defines the JSON structure returned upon successful retrieval of chat assistants. It includes the code field for status and the data array containing detailed chat assistant objects with properties like id, name, create_time, llm configuration, and prompt settings.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_76

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": [
        {
            "avatar": "",
            "create_date": "Fri, 18 Oct 2024 06:20:06 GMT",
            "create_time": 1729232406637,
            "description": "A helpful Assistant",
            "do_refer": "1",
            "id": "04d0d8e28d1911efa3630242ac120006",
            "dataset_ids": ["527fa74891e811ef9c650242ac120006"],
            "language": "English",
            "llm": {
                "frequency_penalty": 0.7,
                "model_name": "qwen-plus@Tongyi-Qianwen",
                "presence_penalty": 0.4,
                "temperature": 0.1,
                "top_p": 0.3
            },
            "name": "13243",
            "prompt": {
                "empty_response": "Sorry! No relevant content was found in the knowledge base!",
                "keywords_similarity_weight": 0.3,
                "opener": "Hi! I'm your assistant, what can I do for you?",
                "prompt": "You are an intelligent assistant. Please summarize the content of the knowledge base to answer the question. Please list the data in the knowledge base and answer in detail. When all knowledge base content is irrelevant to the question, your answer must include the sentence \"The answer you are looking for is not found in the knowledge base!\" Answers need to consider chat history.\n",
                "rerank_model": "",
                "similarity_threshold": 0.2,
                "top_n": 6,
                "variables": [
                    {
                        "key": "knowledge",
                        "optional": false
                    }
                ]
            },
            "prompt_type": "simple",
            "status": "1",
            "tenant_id": "69736c5e723611efb51b0242ac120007",
            "top_k": 1024,
            "update_date": "Fri, 18 Oct 2024 06:20:06 GMT",
            "update_time": 1729232406638
        }
    ]
}
```

----------------------------------------

TITLE: Cloning Forked RAGFlow Repository - Git
DESCRIPTION: This command clones your forked RAGFlow GitHub repository to your local machine. Replace <yourname> with your actual GitHub username to ensure you clone your personal fork.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/contribution/contributing.md#_snippet_0

LANGUAGE: bash
CODE:
```
git clone git@github.com:<yourname>/ragflow.git
```

----------------------------------------

TITLE: Set HuggingFace Mirror Endpoint
DESCRIPTION: Sets the `HF_ENDPOINT` environment variable to use a mirror site for HuggingFace, which is useful for users who cannot access HuggingFace directly.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_17

LANGUAGE: bash
CODE:
```
export HF_ENDPOINT=https://hf-mirror.com
```

----------------------------------------

TITLE: Setting HuggingFace Mirror Endpoint (Optional) - Bash
DESCRIPTION: This optional command sets the `HF_ENDPOINT` environment variable to a mirror site. This is useful if direct access to HuggingFace is restricted or slow, allowing RAGFlow to fetch models from an alternative source.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_8

LANGUAGE: bash
CODE:
```
export HF_ENDPOINT=https://hf-mirror.com
```

----------------------------------------

TITLE: Agent Session Request Parameters Definition
DESCRIPTION: Detailed definitions for the path and filter parameters used in the agent session creation API, including their types and descriptions.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_99

LANGUAGE: APIDOC
CODE:
```
agent_id: (Path parameter)
  The ID of the associated agent.
user_id: (Filter parameter)
  The optional user-defined ID for parsing docs (especially images) when creating a session while uploading files.
```

----------------------------------------

TITLE: Delete Chat Assistant Sessions
DESCRIPTION: Deletes one or more sessions of a chat assistant by their IDs. If no IDs are specified in the request body, all sessions associated with the specified chat assistant will be deleted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_85

LANGUAGE: APIDOC
CODE:
```
Method: DELETE
URL: /api/v1/chats/{chat_id}/sessions
Headers:
  'content-Type: application/json'
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "ids": list[string]
Parameters:
  Path:
    chat_id: The ID of the associated chat assistant.
  Body:
    "ids": list[string] - The IDs of the sessions to delete. If not specified, all sessions will be deleted.
```

LANGUAGE: bash
CODE:
```
curl --request DELETE \
     --url http://{address}/api/v1/chats/{chat_id}/sessions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "ids": ["test_1", "test_2"]
     }'
```

LANGUAGE: json
CODE:
```
{
    "code": 0
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "The chat doesn't own the session"
}
```

----------------------------------------

TITLE: Running Standalone Sandbox with Makefile
DESCRIPTION: This command uses the `Makefile` to perform a complete setup, build, launch, and test sequence for the RAGFlow Sandbox in standalone mode, simplifying the entire process.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/sandbox/README.md#_snippet_7

LANGUAGE: bash
CODE:
```
make
```

----------------------------------------

TITLE: RAPTOR Cluster Summarization Prompt Configuration
DESCRIPTION: This prompt is applied recursively for cluster summarization within the RAPTOR process. The '{cluster_content}' serves as an internal parameter, representing the content of the current cluster to be summarized. It is recommended to keep this prompt as-is for optimal performance, though the design may be updated in the future.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/dataset/enable_raptor.md#_snippet_0

LANGUAGE: Plain Text
CODE:
```
Please summarize the following paragraphs... Paragraphs as following:
      {cluster_content}
The above is the content you need to summarize.
```

----------------------------------------

TITLE: Generating Test Data in SQL
DESCRIPTION: This SQL script generates comprehensive test data for a relational database schema, including `Customers`, `Products`, `Orders`, and `OrderDetails` tables. It starts a transaction to ensure atomicity, inserting multiple records into each table. The `OrderDetails` insertions dynamically calculate `UnitPrice` and `TotalPrice` by querying the `Products` table, demonstrating inter-table dependencies.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/text2sql_agent.md#_snippet_1

LANGUAGE: SQL
CODE:
```
START TRANSACTION;
INSERT INTO Customers (UserName, Email, PhoneNumber) VALUES
('Alice', 'alice@example.com', '123456789'),
('Bob', 'bob@example.com', '987654321'),
('Charlie', 'charlie@example.com', '112233445'),
('Diana', 'diana@example.com', '555666777'),
('Eve', 'eve@example.com', '999888777'),
('Frank', 'frank@example.com', '123123123'),
('Grace', 'grace@example.com', '456456456'),
('Hugo', 'hugo@example.com', '789789789'),
('Ivy', 'ivy@example.com', '321321321'),
('Jack', 'jack@example.com', '654654654');

INSERT INTO Products (ProductName, Description, Price, StockQuantity) VALUES
('Laptop', 'High performance laptop', 1200.00, 50),
('Smartphone', 'Latest model smartphone', 800.00, 100),
('Tablet', 'Portable tablet device', 300.00, 75),
('Headphones', 'Noise-cancelling headphones', 150.00, 200),
('Camera', 'Professional camera', 600.00, 30),
('Monitor', '24-inch Full HD monitor', 200.00, 45),
('Keyboard', 'Mechanical keyboard', 100.00, 150),
('Mouse', 'Ergonomic gaming mouse', 50.00, 250),
('Speaker', 'Wireless Bluetooth speaker', 80.00, 120),
('Router', 'Wi-Fi router with high speed', 120.00, 90);

INSERT INTO Orders (CustomerID, OrderDate, TotalPrice) VALUES
(1, '2024-01-15', 0),
(2, '2024-02-01', 0),
(3, '2024-03-05', 0),
(4, '2024-04-10', 0),
(5, '2024-05-15', 0),
(6, '2024-06-20', 0),
(7, '2024-07-25', 0),
(8, '2024-08-30', 0),
(9, '2024-09-05', 0),
(10, '2024-10-10', 0),
(1, '2024-11-15', 0),
(2, '2024-12-01', 0),
(3, '2024-01-05', 0),
(4, '2024-02-10', 0),
(5, '2024-03-15', 0),
(6, '2024-04-20', 0),
(7, '2024-05-25', 0),
(8, '2024-06-30', 0),
(9, '2024-07-05', 0),
(10, '2024-08-10', 0);

INSERT INTO OrderDetails (OrderID, ProductID, UnitPrice, Quantity, TotalPrice) VALUES
(1, 1, (SELECT Price FROM Products WHERE ProductID = 1), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 1)), 
(1, 2, (SELECT Price FROM Products WHERE ProductID = 2), 1, (SELECT Price FROM Products WHERE ProductID = 2)),
(2, 3, (SELECT Price FROM Products WHERE ProductID = 3), 3, (SELECT Price * 3 FROM Products WHERE ProductID = 3)),
(2, 4, (SELECT Price FROM Products WHERE ProductID = 4), 1, (SELECT Price FROM Products WHERE ProductID = 4)),
(3, 5, (SELECT Price FROM Products WHERE ProductID = 5), 1, (SELECT Price FROM Products WHERE ProductID = 5)),
(3, 6, (SELECT Price FROM Products WHERE ProductID = 6), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 6)),
(4, 7, (SELECT Price FROM Products WHERE ProductID = 7), 5, (SELECT Price * 5 FROM Products WHERE ProductID = 7)),
(5, 8, (SELECT Price FROM Products WHERE ProductID = 8), 3, (SELECT Price * 3 FROM Products WHERE ProductID = 8)),
(5, 9, (SELECT Price FROM Products WHERE ProductID = 9), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 9)),
(6, 10, (SELECT Price FROM Products WHERE ProductID = 10), 4, (SELECT Price * 4 FROM Products WHERE ProductID = 10)),
(7, 2, (SELECT Price FROM Products WHERE ProductID = 2), 4, (SELECT Price * 4 FROM Products WHERE ProductID = 2)),
(7, 8, (SELECT Price FROM Products WHERE ProductID = 8), 3, (SELECT Price * 3 FROM Products WHERE ProductID = 8)),
(8, 1, (SELECT Price FROM Products WHERE ProductID = 1), 1, (SELECT Price FROM Products WHERE ProductID = 1)),
(8, 9, (SELECT Price FROM Products WHERE ProductID = 9), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 9)),
(8, 10, (SELECT Price FROM Products WHERE ProductID = 10), 5, (SELECT Price * 5 FROM Products WHERE ProductID = 10)),
(9, 3, (SELECT Price FROM Products WHERE ProductID = 3), 5, (SELECT Price * 5 FROM Products WHERE ProductID = 3)),
(9, 6, (SELECT Price FROM Products WHERE ProductID = 6), 1, (SELECT Price FROM Products WHERE ProductID = 6)),
(10, 4, (SELECT Price FROM Products WHERE ProductID = 4), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 4)),
(10, 7, (SELECT Price FROM Products WHERE ProductID = 7), 3, (SELECT Price * 3 FROM Products WHERE ProductID = 7)),
(11, 5, (SELECT Price FROM Products WHERE ProductID = 5), 1, (SELECT Price FROM Products WHERE ProductID = 5)),
(11, 10, (SELECT Price FROM Products WHERE ProductID = 10), 4, (SELECT Price * 4 FROM Products WHERE ProductID = 10)),
(12, 1, (SELECT Price FROM Products WHERE ProductID = 1), 3, (SELECT Price * 3 FROM Products WHERE ProductID = 1)),
(12, 8, (SELECT Price FROM Products WHERE ProductID = 8), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 8)),
(13, 2, (SELECT Price FROM Products WHERE ProductID = 2), 1, (SELECT Price FROM Products WHERE ProductID = 2)),
(13, 9, (SELECT Price FROM Products WHERE ProductID = 9), 3, (SELECT Price * 3 FROM Products WHERE ProductID = 9)),
(14, 3, (SELECT Price FROM Products WHERE ProductID = 3), 4, (SELECT Price * 4 FROM Products WHERE ProductID = 3)),
(14, 6, (SELECT Price FROM Products WHERE ProductID = 6), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 6)),
(15, 4, (SELECT Price FROM Products WHERE ProductID = 4), 5, (SELECT Price * 5 FROM Products WHERE ProductID = 4))
```

----------------------------------------

TITLE: API: Retrieve Chat Assistants
DESCRIPTION: Details the API endpoint for fetching a list of chat assistants. It specifies the HTTP method, URL structure with query parameters, required authorization header, and a comprehensive list of filter parameters with their types and descriptions.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_74

LANGUAGE: APIDOC
CODE:
```
Method: GET
URL: /api/v1/chats?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={chat_name}&id={chat_id}
Headers:
  'Authorization: Bearer <YOUR_API_KEY>'
Request parameters:
  page: (Filter parameter), integer
    Specifies the page on which the chat assistants will be displayed. Defaults to 1.
  page_size: (Filter parameter), integer
    The number of chat assistants on each page. Defaults to 30.
  orderby: (Filter parameter), string
    The attribute by which the results are sorted. Available options:
      create_time (default)
      update_time
  desc: (Filter parameter), boolean
    Indicates whether the retrieved chat assistants should be sorted in descending order. Defaults to true.
  id: (Filter parameter), string
    The ID of the chat assistant to retrieve.
  name: (Filter parameter), string
    The name of the chat assistant to retrieve.
```

----------------------------------------

TITLE: Configure Local Hosts File for RAGFlow Services
DESCRIPTION: Adds an entry to the `/etc/hosts` file to map RAGFlow's internal service hostnames (e.g., es01, infinity) to `127.0.0.1`, enabling local resolution for these services.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_16

LANGUAGE: bash
CODE:
```
127.0.0.1       es01 infinity mysql minio redis sandbox-executor-manager
```

----------------------------------------

TITLE: Update Chat Session Name
DESCRIPTION: Updates the name of a specific chat session for a given chat assistant. This operation requires authentication and a JSON body containing the new session name.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_83

LANGUAGE: APIDOC
CODE:
```
Method: PUT
URL: /api/v1/chats/{chat_id}/sessions/{session_id}
Headers:
  'content-Type: application/json'
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "name": string
  "user_id": string (optional)
Parameters:
  Path:
    chat_id: The ID of the associated chat assistant.
    session_id: The ID of the session to update.
  Body:
    "name": string - The revised name of the session.
    "user_id": string - Optional user-defined ID.
```

LANGUAGE: bash
CODE:
```
curl --request PUT \
     --url http://{address}/api/v1/chats/{chat_id}/sessions/{session_id} \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "name": "<REVISED_SESSION_NAME_HERE>"
     }'
```

LANGUAGE: json
CODE:
```
{
    "code": 0
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "Name cannot be empty."
}
```

----------------------------------------

TITLE: Configuring Firewall for Jina on Linux (Bash)
DESCRIPTION: Allows inbound TCP connections on port 12345 through the 'ufw' firewall, which is required for the Jina service to operate correctly. This ensures the host machine can accept connections for the Jina model.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/models/deploy_local_llm.mdx#_snippet_20

LANGUAGE: bash
CODE:
```
sudo ufw allow 12345/tcp
```

----------------------------------------

TITLE: API Reference: List Chat Assistants Endpoint
DESCRIPTION: Defines the GET endpoint for retrieving a list of chat assistants, supporting pagination, ordering, and filtering by name or ID.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_73

LANGUAGE: APIDOC
CODE:
```
Method: GET
URL: /api/v1/chats?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={chat_name}&id={chat_id}
```

----------------------------------------

TITLE: API Reference: Delete Chat Assistants Endpoint
DESCRIPTION: Defines the DELETE endpoint for removing one or more chat assistants by ID.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_69

LANGUAGE: APIDOC
CODE:
```
Method: DELETE
URL: /api/v1/chats
Headers:
  'content-Type: application/json'
  'Authorization: Bearer <YOUR_API_KEY>'
Body:
  "ids": list[string]
```

----------------------------------------

TITLE: Initializing Standalone Sandbox Environment
DESCRIPTION: This command copies the example environment file to `.env`, which is necessary to configure the standalone RAGFlow Sandbox environment before launching services.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/sandbox/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
cp .env.example .env
```

----------------------------------------

TITLE: Populating Order Details Data - SQL
DESCRIPTION: This snippet provides a series of value tuples, likely intended for bulk insertion into an 'OrderDetails' table. Each tuple represents an order detail, including 'OrderID', 'ProductID', 'UnitPrice' (derived from 'Products' table), 'Quantity', and 'TotalPrice' (calculated based on 'UnitPrice' and 'Quantity'). It demonstrates how to populate order detail records with calculated prices.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/text2sql_agent.md#_snippet_2

LANGUAGE: SQL
CODE:
```
(15, 7, (SELECT Price FROM Products WHERE ProductID = 7), 1, (SELECT Price FROM Products WHERE ProductID = 7)),
(16, 5, (SELECT Price FROM Products WHERE ProductID = 5), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 5)),
(16, 10, (SELECT Price FROM Products WHERE ProductID = 10), 3, (SELECT Price * 3 FROM Products WHERE ProductID = 10)),
(17, 1, (SELECT Price FROM Products WHERE ProductID = 1), 4, (SELECT Price * 4 FROM Products WHERE ProductID = 1)),
(17, 8, (SELECT Price FROM Products WHERE ProductID = 8), 1, (SELECT Price FROM Products WHERE ProductID = 8)),
(18, 2, (SELECT Price FROM Products WHERE ProductID = 2), 5, (SELECT Price * 5 FROM Products WHERE ProductID = 2)),
(18, 9, (SELECT Price FROM Products WHERE ProductID = 9), 2, (SELECT Price * 2 FROM Products WHERE ProductID = 9)),
(19, 3, (SELECT Price FROM Products WHERE ProductID = 3), 3, (SELECT Price * 3 FROM Products WHERE ProductID = 3)),
(19, 6, (SELECT Price FROM Products WHERE ProductID = 6), 4, (SELECT Price * 4 FROM Products WHERE ProductID = 6)),
(20, 4, (SELECT Price FROM Products WHERE ProductID = 4), 1, (SELECT Price FROM Products WHERE ProductID = 4)),
(20, 7, (SELECT Price FROM Products WHERE ProductID = 7), 5, (SELECT Price * 5 FROM Products WHERE ProductID = 7));
```

----------------------------------------

TITLE: Creating Database Tables in SQL
DESCRIPTION: This SQL snippet defines the schema for four core tables: `Customers`, `Products`, `Orders`, and `OrderDetails`. It includes `DROP TABLE IF EXISTS` for idempotency and sets up primary and foreign key relationships (implicitly for `Orders` and `OrderDetails` via `CustomerID` and `ProductID` keys, though not explicitly defined as foreign key constraints in the DDL).
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/text2sql_agent.md#_snippet_0

LANGUAGE: SQL
CODE:
```
SET NAMES utf8mb4;

-- ----------------------------
-- Table structure for Customers
-- ----------------------------
DROP TABLE IF EXISTS `Customers`;
CREATE TABLE `Customers` (
  `CustomerID` int NOT NULL AUTO_INCREMENT,
  `UserName` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `PhoneNumber` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`CustomerID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for Products
-- ----------------------------
DROP TABLE IF EXISTS `Products`;
CREATE TABLE `Products` (
  `ProductID` int NOT NULL AUTO_INCREMENT,
  `ProductName` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Description` text COLLATE utf8mb4_unicode_ci,
  `Price` decimal(10,2) DEFAULT NULL,
  `StockQuantity` int DEFAULT NULL,
  PRIMARY KEY (`ProductID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for Orders
-- ----------------------------
DROP TABLE IF EXISTS `Orders`;
CREATE TABLE `Orders` (
  `OrderID` int NOT NULL AUTO_INCREMENT,
  `CustomerID` int DEFAULT NULL,
  `OrderDate` date DEFAULT NULL,
  `TotalPrice` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`OrderID`),
  KEY `CustomerID` (`CustomerID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for OrderDetails
-- ----------------------------
DROP TABLE IF EXISTS `OrderDetails`;
CREATE TABLE `OrderDetails` (
  `OrderDetailID` int NOT NULL AUTO_INCREMENT,
  `OrderID` int DEFAULT NULL,
  `ProductID` int DEFAULT NULL,
  `UnitPrice` decimal(10,2) DEFAULT NULL,
  `Quantity` int DEFAULT NULL,
  `TotalPrice` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`OrderDetailID`),
  KEY `OrderID` (`OrderID`),
  KEY `ProductID` (`ProductID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

----------------------------------------

TITLE: Building RAGFlow Docker Image without Embedding Models (Bash)
DESCRIPTION: This snippet provides a sequence of Bash commands to clone the RAGFlow repository, download dependencies, and build a Docker image without embedding models. This results in a smaller image (approx. 2 GB) that relies on external LLM and embedding services. It's suitable for development, debugging, or testing purposes.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/build_docker_image.mdx#_snippet_0

LANGUAGE: bash
CODE:
```
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/
uv run download_deps.py
docker build -f Dockerfile.deps -t infiniflow/ragflow_deps .
docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:nightly-slim .
```

----------------------------------------

TITLE: API: Update Chat Assistant's Session
DESCRIPTION: Documents the API endpoint for updating an existing session associated with a specific chat assistant. It specifies the HTTP method and the URL structure with path parameters for both chat and session IDs.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_82

LANGUAGE: APIDOC
CODE:
```
Method: PUT
URL: /api/v1/chats/{chat_id}/sessions/{session_id}
```

----------------------------------------

TITLE: Resolve MaxRetryError for Hugging Face Mirror Connection
DESCRIPTION: If MaxRetryError occurs when connecting to hf-mirror.com, manually download resource files from huggingface.co/InfiniFlow/deepdoc to ~/deepdoc and add a volume mapping in docker-compose.yml to make them accessible to RAGFlow.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/faq.mdx#_snippet_4

LANGUAGE: yaml
CODE:
```
- ~/deepdoc:/ragflow/rag/res/deepdoc
```

----------------------------------------

TITLE: Updating /etc/hosts for Service Resolution - Bash
DESCRIPTION: This snippet shows the entry to be added to the `/etc/hosts` file. It maps several service hostnames (es01, infinity, mysql, minio, redis) to the loopback address `127.0.0.1`, ensuring local resolution for Docker-based services.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_5

LANGUAGE: bash
CODE:
```
127.0.0.1       es01 infinity mysql minio redis
```

----------------------------------------

TITLE: List Agents API: Request Query Parameters
DESCRIPTION: Defines the optional query parameters for filtering and sorting when retrieving a collection of agents. Parameters include pagination, ordering, and specific agent identification.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_125

LANGUAGE: APIDOC
CODE:
```
- `page`: (Filter parameter), `integer`. Specifies the page on which the agents will be displayed. Defaults to `1`.
- `page_size`: (Filter parameter), `integer`. The number of agents on each page. Defaults to `30`.
- `orderby`: (Filter parameter), `string`. The attribute by which the results are sorted. Available options:
  - `create_time` (default)
  - `update_time`
- `desc`: (Filter parameter), `boolean`. Indicates whether the retrieved agents should be sorted in descending order. Defaults to `true`.
- `id`: (Filter parameter), `string`. The ID of the agent to retrieve.
- `name`: (Filter parameter), `string`. The name of the agent to retrieve.
```

----------------------------------------

TITLE: OSS Object Storage Configuration
DESCRIPTION: Configures access details for Alibaba Cloud OSS, including authentication keys, endpoint URL, region, and the bucket name for storing files. An optional prefix path can be used for organization.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_11

LANGUAGE: APIDOC
CODE:
```
oss:
  access_key: The access key ID used to authenticate requests to the OSS service.
  secret_key: The secret access key used to authenticate requests to the OSS service.
  endpoint_url: The URL of the OSS service endpoint.
  region: The OSS region where the bucket is located.
  bucket: The name of the OSS bucket where files will be stored. When you want to store all files in a specified bucket, you need this configuration item.
  prefix_path: Optional. A prefix path to prepend to file names in the OSS bucket, which can help organize files within the bucket.
```

----------------------------------------

TITLE: Create Agent Session (With Required File Parameters)
DESCRIPTION: Example cURL command to initiate an agent session when the 'Begin' component requires file uploads. This uses 'multipart/form-data' content type and includes a user ID in the URL.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_98

LANGUAGE: bash
CODE:
```
curl --request POST \
     --url http://{address}/api/v1/agents/{agent_id}/sessions?user_id={user_id} \
     --header 'Content-Type: multipart/form-data' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --form '<FILE_KEY>=@./test1.png'
```

----------------------------------------

TITLE: Installing Node.js Packages
DESCRIPTION: Install desired Node.js packages using the `npm install` command, for example, `npm install lodash`. These dependencies will be automatically saved to `package.json` and `package-lock.json` and included when the Docker image is rebuilt.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/sandbox/README.md#_snippet_14

LANGUAGE: Bash
CODE:
```
npm install lodash
```

----------------------------------------

TITLE: Kibana Docker Environment Variables
DESCRIPTION: Defines environment variables for configuring the Kibana service within the Docker environment, covering external port, username, and password.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_1

LANGUAGE: APIDOC
CODE:
```
KIBANA_PORT:
  Description: "The port used to expose the Kibana service to the host machine, allowing external access to the service running inside the Docker container."
  Default: "6601"
KIBANA_USER:
  Description: "The username for Kibana."
  Default: "rag_flow"
KIBANA_PASSWORD:
  Description: "The password for Kibana."
  Default: "infini_rag_flow"
```

----------------------------------------

TITLE: Update Document API Response Examples
DESCRIPTION: Examples of successful and failure responses for the document update API call, showing the 'code' and 'message' fields.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_28

LANGUAGE: json
CODE:
```
{
    "code": 0
}
```

LANGUAGE: json
CODE:
```
{
    "code": 102,
    "message": "The dataset does not have the document."
}
```

----------------------------------------

TITLE: JSON Response: Parse Documents Success
DESCRIPTION: A successful JSON response indicating that the document parsing request was accepted.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_44

LANGUAGE: json
CODE:
```
{
    "code": 0
}
```

----------------------------------------

TITLE: APIDOC: DataSet.async_cancel_parse_documents Method
DESCRIPTION: API documentation for the `DataSet.async_cancel_parse_documents` method, used to stop the parsing process for specified documents.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/python_api_reference.md#_snippet_27

LANGUAGE: APIDOC
CODE:
```
DataSet.async_cancel_parse_documents(document_ids:list[str])-> None

Parameters:
- document_ids: `list[str]`, *Required*
  The IDs of the documents for which parsing should be stopped.

Returns:
- Success: No value is returned.
- Failure: `Exception`
```

----------------------------------------

TITLE: Create Agent API: Success Response JSON Example
DESCRIPTION: Presents the JSON response structure for a successful agent creation, confirming the operation's completion.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_131

LANGUAGE: json
CODE:
```
{
    "code": 0,
    "data": true,
    "message": "success"
}
```

----------------------------------------

TITLE: RAGFlow Docker Environment Variables
DESCRIPTION: Defines environment variables for configuring the RAGFlow application within the Docker environment, including its HTTP API port and available Docker image editions with their included embedding models. Also provides alternative mirror sites for image downloads.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docker/README.md#_snippet_6

LANGUAGE: APIDOC
CODE:
```
SVR_HTTP_PORT:
  Description: "The port used to expose RAGFlow's HTTP API service to the host machine, allowing external access to the service running inside the Docker container."
  Default: "9380"
RAGFLOW_IMAGE:
  Description: "The Docker image edition for RAGFlow."
  Available Editions:
    - "infiniflow/ragflow:v0.19.0-slim" (default): "The RAGFlow Docker image without embedding models."
    - "infiniflow/ragflow:v0.19.0": "The RAGFlow Docker image with embedding models including: BAAI/bge-large-zh-v1.5, maidalun1020/bce-embedding-base_v1"
  Mirror Sites (for nightly-slim):
    - "RAGFLOW_IMAGE=swr.cn-north-4.myhuaweicloud.com/infiniflow/ragflow:nightly-slim"
    - "RAGFLOW_IMAGE=registry.cn-hangzhou.aliyuncs.com/infiniflow/ragflow:nightly-slim"
  Mirror Sites (for nightly):
    - "RAGFLOW_IMAGE=swr.cn-north-4.myhuaweicloud.com/infiniflow/ragflow:nightly"
    - "RAGFLOW_IMAGE=registry.cn-hangzhou.aliyuncs.com/infiniflow/ragflow:nightly"
```

----------------------------------------

TITLE: Agent Message Success Response JSON
DESCRIPTION: This JSON object represents a successful response from an agent message interaction. It includes the agent's configuration, conversation history, current messages, and source information.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/references/http_api_reference.md#_snippet_113

LANGUAGE: json
CODE:
```
{
    "agent": {
        "config": {
            "conversation_mode": "chat",
            "max_tokens": 2000,
            "model": "gpt-3.5-turbo",
            "name": "test",
            "prompt": "You are a helpful AI assistant.",
            "temperature": 0.7,
            "top_p": 1,
            "tools": [
                {
                    "name": "search",
                    "properties": {
                        "description": "Search the web for information.",
                        "parameters": {
                            "properties": {
                                "query": {
                                    "description": "The search query.",
                                    "type": "string"
                                }
                            },
                            "required": [
                                "query"
                            ],
                            "type": "object"
                        },
                        "tool_code": "def search(query: str):\n    return \"search result\"\n",
                        "tool_name": "search"
                    },
                    "type": "tool",
                    "width": 200
                }
            ]
        },
        "history": [],
        "messages": [],
        "path": [],
        "reference": []
    },
    "id": "792dde22b2fa11ef97550242ac120006",
    "message": [
        {
            "content": "Hi! I'm your smart assistant. What can I do for you?",
            "role": "assistant"
        }
    ],
    "source": "agent",
    "user_id": ""
}
```

----------------------------------------

TITLE: Building Sandbox Base Docker Images Manually
DESCRIPTION: This snippet demonstrates how to manually build the Python and Node.js base Docker images for the RAGFlow Sandbox. These images are isolated and used for secure containerized execution of code. It requires Docker to be installed.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/sandbox/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
docker build -t sandbox-base-python:latest ./sandbox_base_image/python
docker build -t sandbox-base-nodejs:latest ./sandbox_base_image/nodejs
```

----------------------------------------

TITLE: Commenting Out Nginx in entrypoint.sh - Shell
DESCRIPTION: This snippet illustrates how to comment out the Nginx startup line in the `docker/entrypoint.sh` script. This is necessary when launching RAGFlow from source to prevent Nginx from interfering with direct service execution.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/launch_ragflow_from_source.md#_snippet_6

LANGUAGE: shell
CODE:
```
# /usr/sbin/nginx
```

----------------------------------------

TITLE: Build RAGFlow Docker Image (Slim, No Embeddings)
DESCRIPTION: Builds a lightweight Docker image for RAGFlow (approximately 2 GB) that relies on external LLM and embedding services. This uses the `LIGHTEN=1` build argument to exclude embedding models.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/README.md#_snippet_11

LANGUAGE: bash
CODE:
```
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/
docker build --platform linux/amd64 --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:nightly-slim .
```

----------------------------------------

TITLE: Launch RAGFlow and MCP Servers with Docker Compose
DESCRIPTION: This command initiates the RAGFlow server alongside the MCP server using the specified Docker Compose configuration. The extensive log output that follows confirms the successful startup, detailing service initializations, port bindings, and version information for both components.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/develop/mcp/launch_mcp_server.md#_snippet_2

LANGUAGE: bash
CODE:
```
docker compose -f docker-compose.yml
```

LANGUAGE: bash
CODE:
```
  ragflow-server  | Starting MCP Server on 0.0.0.0:9382 with base URL http://127.0.0.1:9380...
  ragflow-server  | Starting 1 task executor(s) on host 'dd0b5e07e76f'...
  ragflow-server  | 2025-04-18 15:41:18,816 INFO     27 ragflow_server log path: /ragflow/logs/ragflow_server.log, log levels: {'peewee': 'WARNING', 'pdfminer': 'WARNING', 'root': 'INFO'}
  ragflow-server  | 
  ragflow-server  | __  __  ____ ____       ____  _____ ______     _______ ____
  ragflow-server  | |  \/  |/ ___|  _ \     / ___|| ____|  _ \ \   / / ____|  _ \
  ragflow-server  | | |\/| | |   | |_) |    \___ \|  _| | |_) \ \ / /|  _| | |_) |
  ragflow-server  | | |  | | |___|  __/      ___) | |___|  _ < \ V / | |___|  _ <
  ragflow-server  | |_|  |_|\____|_|        |____/|_____|_| \_\ \_/  |_____|_| \_\
  ragflow-server  |     
  ragflow-server  | MCP launch mode: self-host
  ragflow-server  | MCP host: 0.0.0.0
  ragflow-server  | MCP port: 9382
  ragflow-server  | MCP base_url: http://127.0.0.1:9380
  ragflow-server  | INFO:     Started server process [26]
  ragflow-server  | INFO:     Waiting for application startup.
  ragflow-server  | INFO:     Application startup complete.
  ragflow-server  | INFO:     Uvicorn running on http://0.0.0.0:9382 (Press CTRL+C to quit)
  ragflow-server  | 2025-04-18 15:41:20,469 INFO     27 found 0 gpus
  ragflow-server  | 2025-04-18 15:41:23,263 INFO     27 init database on cluster mode successfully
  ragflow-server  | 2025-04-18 15:41:25,318 INFO     27 load_model /ragflow/rag/res/deepdoc/det.onnx uses CPU
  ragflow-server  | 2025-04-18 15:41:25,367 INFO     27 load_model /ragflow/rag/res/deepdoc/rec.onnx uses CPU
  ragflow-server  |         ____   ___    ______ ______ __               
  ragflow-server  |        / __ \ /   |  / ____// ____// /____  _      __
  ragflow-server  |       / /_/ // /| | / / __ / /_   / // __ \| | /| / /
  ragflow-server  |      / _, _// ___ |/ /_/ // __/  / // /_/ /| |/ |/ / 
  ragflow-server  |     /_/ |_|/_/  |_|\____//_/    /_/ \____/ |__/|__/                             
  ragflow-server  | 
  ragflow-server  |     
  ragflow-server  | 2025-04-18 15:41:29,088 INFO     27 RAGFlow version: v0.18.0-285-gb2c299fa full
  ragflow-server  | 2025-04-18 15:41:29,088 INFO     27 project base: /ragflow
  ragflow-server  | 2025-04-18 15:41:29,088 INFO     27 Current configs, from /ragflow/conf/service_conf.yaml:
  ragflow-server  |  ragflow: {'host': '0.0.0.0', 'http_port': 9380}
  ragflow-server  |  * Running on all addresses (0.0.0.0)
  ragflow-server  |  * Running on http://127.0.0.1:9380
  ragflow-server  |  * Running on http://172.19.0.6:9380
  ragflow-server  |   ______           __      ______                     __            
  ragflow-server  |  /_  __/___ ______/ /__   / ____/  _____  _______  __/ /_____  _____
  ragflow-server  |   / / / __ `/ ___/ //_/  / __/ | |/_/ _ \/ ___/ / / / __/ __ \/ ___/
  ragflow-server  |  / / / /_/ (__  ) ,<    / /____>  </  __/ /__/ /_/ / /_/ /_/ / /    
  ragflow-server  | /_/  \__,_/____/_/|_|  /_____/_/|_|\___/\___/\__,_/\__/\____/_/                               
  ragflow-server  |     
  ragflow-server  | 2025-04-18 15:41:34,501 INFO     32 TaskExecutor: RAGFlow version: v0.18.0-285-gb2c299fa full
  ragflow-server  | 2025-04-18 15:41:34,501 INFO     32 Use Elasticsearch http://es01:9200 as the doc engine.
```

----------------------------------------

TITLE: Loading RAGFlow Docker Image from Tar File
DESCRIPTION: Loads a Docker image from a `.tar` file into the local Docker daemon. This command is used in offline environments to import the RAGFlow image that was previously saved, making it available for use by Docker Compose.
SOURCE: https://github.com/infiniflow/ragflow/blob/main/docs/guides/upgrade_ragflow.mdx#_snippet_7

LANGUAGE: bash
CODE:
```
docker load -i ragflow.v0.19.0.tar
```