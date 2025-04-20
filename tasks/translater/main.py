from oocana import Context
from typing import Literal, TypedDict
from shared.translater import Translater
from .file import translate_epub_file
from .cache import CacheTranslater


class LLMModelOptions(TypedDict):
  model: str
  temperature: float
  top_p: float
  max_tokens: int

class Input(TypedDict):
  file: str
  title: str | None
  max_translating_group: int
  source: Literal["en", "cn", "ja", "fr", "ru", "de"]
  target: Literal["en", "cn", "ja", "fr", "ru", "de"]
  timeout: float
  llm: LLMModelOptions

def main(params: Input, context: Context):
  llm_model = params["llm"]
  llm_env = context.oomol_llm_env
  timeout: float | None = params["timeout"]
  if timeout == 0.0:
    timeout = None

  translater = Translater(
    key=llm_env["api_key"],
    url=llm_env["base_url_v1"],
    model=llm_model["model"],
    temperature=float(llm_model["temperature"]),
    timeout=timeout,
    source_lan=params["source"],
    target_lan=params["target"],
    group_max_tokens=params["max_translating_group"],
    streaming=True,
  )
  cache = CacheTranslater(
    context=context,
    translate=translater.translate,
  )
  zip_data = translate_epub_file(
    context=context,
    translate=cache.translate,
    file_path=params["file"],
    book_title=params.get("title", None),
  )
  return { "binary": zip_data }