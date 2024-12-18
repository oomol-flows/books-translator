from typing import Callable
from .translater import AITranslator
from .llm import LLM_API

Translate = Callable[[list[str]], list[str]]