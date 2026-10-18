"""Local-only browser fixture; never calls Anthropic or reads a real key."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from types import SimpleNamespace
import uvicorn
from app import ai, main

class FixtureClaude:
    def __init__(self):
        self.messages = SimpleNamespace(create=self.create)
    async def create(self, **kwargs):
        if not any(m['role']=='assistant' for m in kwargs['messages']):
            block={'type':'tool_use','id':'fixture-tool','name':'coin_dossier','input':{'mint':'3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump'}}
            return SimpleNamespace(content=[SimpleNamespace(**block,model_dump=lambda **_:block)],stop_reason='tool_use')
        return SimpleNamespace(content=[SimpleNamespace(type='text',text='The creator has no other recorded launches [E1].')],stop_reason='end_turn')

def owner():
    ai.OWNER=ai.Owner(key='fixture-key-never-sent-to-a-provider',model='fixture-claude',client=FixtureClaude())
ai.load_owner=owner
main.ORIGINS.add("http://127.0.0.1:8081")
uvicorn.run(main.app,host='127.0.0.1',port=8081,log_level='warning')
