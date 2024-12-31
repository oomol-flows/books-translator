import re

from typing import Callable
from .group import Group
from .llm import LLM, LLM_API

_lan_full_name: dict[str, str] = {
  "en": "English",
  "cn": "simplified Chinese",
  "fr": "French",
  "ru": "Russian",
  "de": "German",
}

class Translater:
  def __init__(
      self,
      group_max_tokens: int,
      api: LLM_API, 
      key: str | None, 
      url: str | None, 
      model: str,
      temperature: float,
      timeout: float | None,
      source_lan: str | None,
      target_lan: str,
    ) -> None:
    self._group: Group = Group(group_max_tokens)
    self._llm = LLM(
      api=api,
      key=key,
      url=url,
      model=model,
      temperature=temperature,
      timeout=timeout,
    )
    self._admin_prompt: str = _gen_admin_prompt(
      target_lan=self._lan_full_name(target_lan),
      source_lan=None if source_lan is None else self._lan_full_name(source_lan),
    )

  def translate(self, source_texts: list[str], report_progress: Callable[[float], None]) -> list[str]:
    target_texts: list[str] = [""] * len(source_texts)
    max_index: int = 0

    for chunk in self._group.split(source_texts):
      chunk_texts: list[str] = []
      chunk_indexes: list[int] = []
      for index, text in chunk:
        text = text.strip()
        if text != "":
          chunk_texts.append(text)
          chunk_indexes.append(index)

      if len(chunk_texts) > 0:
        chunk_texts = self._translate_texts(chunk_texts)
      
      for index, text in zip(chunk_indexes, chunk_texts):
        target_texts[index] = text
        max_index = max(index, max_index)
      
      report_progress(float(max_index + 1) / float(len(source_texts)))

    return target_texts

  def _translate_texts(self, texts: list[str]) -> list[str]:
    content = self._llm.invoke(
      system=self._admin_prompt,
      human="\n".join(texts),
    )
    target_texts: list[str] = []
    for line in content.split("\n"):
      match = re.search(r"^\d+(\:|\.)", line)
      if match:
        text = re.sub(r"^\d+(\:|\.)\s*", "", line)
        target_texts.append(text)

    return target_texts

  def _lan_full_name(self, name: str) -> str:
    full_name = _lan_full_name.get(name, None)
    if full_name is None:
      full_name = _lan_full_name["en"]
    return full_name

def _gen_admin_prompt(target_lan: str, source_lan: str | None) -> str:
  if source_lan is None:
    source_lan = "any language and you will detect the language"
  return f"""
I want you to act as an {target_lan} translator, spelling corrector and improver. 
Next user will speak to you in {source_lan}, translate it and answer in the corrected and improved version of my text, in {target_lan}. 
I want you to replace simplified A0-level words and sentences with more beautiful and elegant, upper level Chinese words and sentences. Keep the meaning same, but make them more literary. 
I want you to only reply the correction, the improvements and nothing else, do not write explanations.
Next user will speak a passage. The passage is divided into multiple lines, each line starting with a number (an Arabic numeral followed by a colon).
Your translation should also respond in multiple lines, with corresponding numbers at the beginning of each line in the translation.
  """