import re
import math

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
    self._group: Group = Group(
      group_max_tokens=group_max_tokens, 
      interval_max_tokens=math.ceil(float(group_max_tokens) * 0.1),
    )
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
      fragments = self._translate_fragments(
        fragments, 
        report_progress=lambda p: report_progress(
          float(operated_id + p) / float(len(source_texts)),
        ),
      )
      for fragment in fragments:
        if operated_id > fragment.id:
          continue # fragment may be duplicated
        operated_id = max(operated_id, fragment.id)
        target_texts[fragment.index] += fragment.target

    return target_texts

  def _translate_fragments(self, fragments: list[Fragment], report_progress: Callable[[float], None]) -> list[Fragment]:
    texts: list[str] = []
    translated_texts: list[str] = []
    indexes: list[int] = []
    for index, fragment in enumerate(fragments):
      text = fragment.origin.strip()
      if text != "":
        texts.append(text)
        indexes.append(index)

    if len(texts) > 0:
      for i, text in enumerate(self._translate_text_by_text(texts)):
        report_progress(min(1.0, float(i) / float(len(texts))))
        translated_texts.append(text)
    report_progress(1.0)

    for index, text in zip(indexes, translated_texts):
      fragments[index].target = text
    return fragments

  def _translate_text_by_text(self, texts: list[str]):
    system=self._admin_prompt
    human="\n".join([f"{i+1}: {t}" for i, t in enumerate(texts)])
    for line in self._llm.invoke_response_lines(system, human):
      match = re.search(r"^\d+\:", line)
      if match:
        yield re.sub(r"^\d+\:\s*", "", line)

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