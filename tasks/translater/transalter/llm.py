import re
import requests

from typing import Optional

class AITranslator:
  def __init__(
    self,
    model: str,
    api_url: str,
    auth_token: str,
    target_lan: str,
    source_lan: Optional[str]
  ):
    self._model = model
    self._api_url = api_url
    self._admin_prompt: str = _admin_prompt(
      target_lan=target_lan,
      source_lan=source_lan,
    )
    self._headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {auth_token}",
    }

  def translate(self, text_list: list[str]):
    text_buffer_list = []

    for index, text in enumerate(text_list):
      text = re.sub(r"\n", " ", text)
      text = text.strip()
      text_buffer_list.append(f"{index + 1}: {text}")

    response = self._request([{
      "role": "system",
      "content": self._admin_prompt,
    }, {
      "role": "user",
      "content": "\n".join(text_buffer_list),
    }])
    content: str = response["choices"][0]["message"]["content"]
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

  def _request(self, messages: list[dict[str, str]]):
    response = requests.post(
      self._api_url,
      headers=self._headers,
      stream=False,
      json={
        "model": self._model,
        "messages": messages,
      },
    )
    if response.status_code != 200:
      raise Exception(f"request failed: {response.status_code}")

    return response.json()

def _admin_prompt(target_lan: str, source_lan: Optional[str]) -> str:
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