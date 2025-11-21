from __future__ import annotations
import os
import sys
# Ensure repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.clients.llm_client import DeepSeekLLMClient, PLACEHOLDER_API_KEY

api_key = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('LLM_API_KEY')
print('env api_key repr:', repr(api_key), 'len=', len(api_key) if api_key else 0)
settings = {'llm_api_key': api_key}
client = DeepSeekLLMClient(settings)
print('client._api_key repr:', repr(client._api_key))
print('is placeholder?', client._api_key == PLACEHOLDER_API_KEY)
