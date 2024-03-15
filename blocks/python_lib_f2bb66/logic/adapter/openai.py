import re
import requests

_AdminPrompt = """
I want you to act as an Chinese translator, spelling corrector and improver. 
Next user will speak to you in any language and you will detect the language, translate it and answer in the corrected and improved version of my text, in Chinese. 
I want you to replace simplified A0-level words and sentences with more beautiful and elegant, upper level Chinese words and sentences. Keep the meaning same, but make them more literary. 
I want you to only reply the correction, the improvements and nothing else, do not write explanations.
Next user will speak a passage. The passage is divided into multiple lines, each line starting with a number (an Arabic numeral followed by a colon). Your translation should also respond in multiple lines, with corresponding numbers at the beginning of each line in the translation.
"""

class OpenAITranslator:
  def __init__(self):
    with open("/app/workspace/token.txt", "r") as file:
      auth_token = file.read()
    self._model = "gpt-3.5-turbo"
    self._api_url = "https://aigptx.top/v1/chat/completions"
    self._headers = headers = {
      "Authorization": f"Bearer {auth_token}",
    }

  def translate(self, text_list: list[str], mime_type: str):
    text_buffer_list = []

    for index, text in enumerate(text_list):
      text = re.sub(r"\n", " ", text)
      text = text.strip()
      text_buffer_list.append(f"{index + 1}: {text}")

    response = self._request([{
      "role": "system",
      "content": _AdminPrompt,
    }, {
      "role": "user",
      "content": "\n".join(text_buffer_list),
    }])
    response: str = response["choices"][0]["message"]["content"]
    to_text_list = [""] * len(text_list)

    for line in response.split("\n"):
      match = re.search(r"^\d+\:", line)
      if match:
        index = re.sub(r"\:$", "",  match.group(0))
        index = int(index) - 1
        text = re.sub(r"^\d+\:\s*", "", line)
        if index < len(to_text_list):
          to_text_list[index] = text

    return to_text_list

  def _request(self, messages: list):
    response = requests.post(
      self._api_url,
      headers=self._headers,
      stream=False,
      json={
        "model": self._model,
        "messages": messages,
      },
    )
    return response.json()

# run python graphs/translate/blocks/code-0/logic/adapter/openai.py
if __name__ == "__main__":
  translator = OpenAITranslator()
  print(translator.translate([
    "Among the medical schools of classical Greece the most famous was that founded in the fifth century B.C. by Hippocrates of Cos.",
    "But Hippocratic thinking remained in the realm of techne, or professional medical practice, which it essentially founded; it did not generate autonomous sciences (in our sense).",
    "C., of anatomy and physiology based on the dissection of the human body. This was done by Herophilus of Chalcedon, active in Alexandria, and by Erasistratus of Ceos.",
    "Again in this field, tradition favored the works still understandable in the Middle Ages.",
    "no treatise by Herophilus or Erasistratus exists. But from frag- ments and testimonies it is possible to recover a certain fraction of their results, enough for a qualitative evaluation.",
  ]))