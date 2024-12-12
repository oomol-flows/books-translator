from dataclasses import dataclass


@dataclass
class Language:
  llm_name: str
  spacy_model: str

def language(name: str) -> Language:
  if name == "en":
    return Language(
      llm_name="English",
      spacy_model="en_core_web_sm",
    )
  elif name == "cn":
    return Language(
      llm_name="Chinese",
      spacy_model="zh_core_web_sm",
    )
  else:
    raise Exception(f"unknown language: {name}")