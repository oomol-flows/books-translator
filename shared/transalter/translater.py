import re
from .llm import LLM, LLM_API

_lan_full_name = {
  "en": "English",
  "cn": "simplified Chinese",
  "fr": "French",
  "ru": "Russian",
  "de": "German",
}

class AITranslator:
  def __init__(
    self,
    api: LLM_API, 
    key: str | None, 
    url: str | None, 
    model: str,
    temperature: float,
    timeout: float | None,
    source_lan: str | None,
    target_lan: str,
  ):
    self._admin_prompt: str = _admin_prompt(
      target_lan=self._lan_full_name(target_lan),
      source_lan=None if source_lan is None else self._lan_full_name(source_lan),
    )
    self._llm: LLM = LLM(
      api=api,
      key=key,
      url=url,
      model=model,
      temperature=temperature,
      timeout=timeout,
    )

  def _lan_full_name(self, name: str) -> str:
    full_name = _lan_full_name.get(name, None)
    if full_name is None:
      full_name = _lan_full_name["en"]
    return full_name

  def translate(self, text_list: list[str]):
    text_buffer_list = []

    for index, text in enumerate(text_list):
      text = re.sub(r"\n", " ", text)
      text = text.strip()
      text_buffer_list.append(f"{index + 1}: {text}")

    content = self._llm.invoke(
      system=self._admin_prompt,
      human="\n".join(text_buffer_list),
    )
    to_text_list = [""] * len(text_list)

    for line in content.split("\n"):
      match = re.search(r"^\d+\:", line)
      if match:
        index = re.sub(r"\:$", "",  match.group(0))
        index = int(index) - 1
        text = re.sub(r"^\d+\:\s*", "", line)
        if index < len(to_text_list):
          to_text_list[index] = text

    return to_text_list

def _admin_prompt(target_lan: str, source_lan: str | None) -> str:
  if source_lan is None:
    source_lan = "any language and you will detect the language"
  return f"""
I want you to act as an {target_lan} translator, spelling corrector and improver. 
Next user will speak to you in {source_lan}, translate it and answer in the corrected and improved version of my text, in Chinese. 
I want you to replace simplified A0-level words and sentences with more beautiful and elegant, upper level Chinese words and sentences. Keep the meaning same, but make them more literary. 
I want you to only reply the correction, the improvements and nothing else, do not write explanations.
Next user will speak a passage. The passage is divided into multiple lines, each line starting with a number (an Arabic numeral followed by a colon).
Your translation should also respond in multiple lines, with corresponding numbers at the beginning of each line in the translation.
"""