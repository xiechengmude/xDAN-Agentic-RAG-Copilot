import requests
import json

# Disable proxy for localhost
proxies = {"http": None, "https": None}

try:
    response = requests.get("http://localhost:8050/openapi.json", proxies=proxies)
    if response.status_code == 200:
        api_docs = response.json()
        with open("api_docs.json", "w", encoding="utf-8") as f:
            json.dump(api_docs, f, indent=2, ensure_ascii=False)
        print("API documentation saved to api_docs.json")
    else:
        print(f"Failed to fetch API docs: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")