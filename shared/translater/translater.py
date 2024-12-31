import re

from typing import Callable
from .group import Group, Fragment
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
      source_lan: str,
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
      source_lan=self._lan_full_name(source_lan),
      target_lan=self._lan_full_name(target_lan),
    )

  def translate(self, source_texts: list[str], report_progress: Callable[[float], None]) -> list[str]:
    target_texts: list[str] = [""] * len(source_texts)
    grouped_fragments = self._group.split(source_texts)
    operated_id: int = 0

    for fragments in grouped_fragments:
      for fragment in self._translate_fragments(fragments):
        if operated_id > fragment.id:
          continue # fragment may be duplicated
        operated_id = max(operated_id, fragment.id)
        target_texts[fragment.index] += fragment.text
      report_progress(float(operated_id + 1) / float(len(source_texts)))

    return target_texts

  def _translate_fragments(self, fragments: list[Fragment]) -> list[Fragment]:
    texts: list[str] = []
    indexes: list[int] = []
    for index, fragment in enumerate(fragments):
      text = fragment.text.strip()
      if text != "":
        texts.append(text)
        indexes.append(index)
    if len(texts) > 0:
      texts = self._translate_texts(texts)
    for index, text in zip(indexes, texts):
      fragments[index].text = text
    return fragments

  def _translate_texts(self, texts: list[str]) -> list[str]:
    texts = [f"{i+1}: {t}" for i, t in enumerate(texts)]
    content = self._llm.invoke(
      system=self._admin_prompt,
      human="\n".join(texts),
    )
    target_texts: list[str] = []
    for line in content.split("\n"):
      match = re.search(r"^\d+\:", line)
      if match:
        text = re.sub(r"^\d+\:\s*", "", line)
        target_texts.append(text)

    return target_texts

  def _lan_full_name(self, name: str) -> str:
    full_name = _lan_full_name.get(name, None)
    if full_name is None:
      full_name = _lan_full_name["en"]
    return full_name

def _gen_admin_prompt(target_lan: str, source_lan: str) -> str:
  return f"""
You are a translator and need to translate the user's {source_lan} text into {target_lan}.
I want you to replace simplified A0-level words and sentences with more beautiful and elegant, upper level {target_lan} words and sentences. Keep the meaning same, but make them more literary. 
I want you to only reply the translation and nothing else, do not write explanations.
A number and colon are added to the top of each line of text entered by the user. This number is only used to align the translation text for you and has no meaning in itself. You should delete the number in your mind to understand the user's original text.
Your translation results should be split into a number of lines, the number of lines is equal to the number of lines in the user's original text. The content of each line should correspond to the corresponding line of the user's original text.
The translated lines must not be missing, added, misplaced, or have their order changed. They must correspond exactly to the original text of the user.

Here is an example. First, the user submits the original text in English (this is just an example):
1: This true without lying, certain & most true:
2: That which is below is like that which is above and that which is above is like that which is below to do ye miracles of one only thing.
3: And as all things have been and arose from one by ye mediation of one: so all things have their birth from this one thing by adaptation.

If you are asked to translate into Chinese, you need to submit the translated content in the following format:
1: 这是真的，没有任何虚妄，是确定的，最真实的：
2: 上如其下，下如其上，以此来展现“一”的奇迹。
3: 万物皆来自“一”的沉思，万物在“一”的安排下诞生。
"""