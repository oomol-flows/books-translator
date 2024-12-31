from oocana import Context
from shared.epub import EpubHandler
from shared.translater import Translater, LLM_API
from .file import translate_epub_file

def main(inputs: dict, context: Context):
  llm_api: str = inputs["llm_api"]
  api: LLM_API

  if llm_api == "openai":
    api = LLM_API.OpenAI
  elif llm_api == "claude":
    api = LLM_API.Claude
  elif llm_api == "gemini":
    api = LLM_API.Gemini
  else:
    raise Exception(f"unknown llm_api: {llm_api}")

  timeout: float | None = inputs["timeout"]
  if timeout == 0.0:
    timeout = None

  translater = Translater(
    api=api,
    key=_none_if_empty(inputs["api_key"]),
    url=_none_if_empty(inputs["url"]),
    model=inputs["model"],
    temperature=inputs["temperature"],
    timeout=timeout,
    source_lan=inputs["source"],
    target_lan=inputs["target"],
    group_max_tokens=inputs["max_translating_group"],
  )
  epub_handler = EpubHandler(
    translate=translater.translate,
  )
  zip_data = translate_epub_file(
    context=context,
    handler=epub_handler,
    file_path=inputs["file"],
    book_title=inputs.get("title", None),
  )
  return { "binary": zip_data }

def _none_if_empty(text: str) -> str | None:
  return text.strip() == "" if None else text