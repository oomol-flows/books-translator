from typing import Callable
from .llm import AITranslator

Translate = Callable[[list[str]], list[str]]