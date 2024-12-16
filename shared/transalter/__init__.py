from typing import Callable
from .translater import AITranslator

Translate = Callable[[list[str]], list[str]]