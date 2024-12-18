import spacy
import langid
import threading

from typing import Iterator
from spacy.language import Language
from spacy.tokens import Span

_lan2model: dict = {
  "en": "en_core_web_sm",
  "zh": "zh_core_web_sm",
  "fr": "fr_core_news_sm",
  "ru": "ru_core_news_sm",
  "de": "de_core_news_sm",
}

class NLP:
  def __init__(self, default_lan: str) -> None:
    self._lock: threading.Lock = threading.Lock()
    self._nlp_dict: dict[str, Language] = {}
    self._default_lan: str = default_lan

  def split_into_sents(self, text: str) -> Iterator[Span]:
    lan, _ = langid.classify(text)
    with self._lock:
      nlp = self._nlp_dict.get(lan, None)
      if nlp is None:
        model_id = _lan2model.get(lan, None)
        if model_id is None:
          model_id = _lan2model.get(self._default_lan, None)
          if model_id is None:
            raise ValueError("no model found for input text.")
        nlp = spacy.load(model_id)
        self._nlp_dict[lan] = nlp

    return nlp(text).sents