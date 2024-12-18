from oocana import Context
from shared.epub import EpubHandler, CountUnit
from shared.transalter import AITranslator, LLM_API
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

  translater = AITranslator(
    api=api,
    key=_none_if_empty(inputs["api_key"]),
    url=_none_if_empty(inputs["url"]),
    model=inputs["model"],
    temperature=inputs["temperature"],
    timeout=timeout,
    source_lan=inputs["source"],
    target_lan=inputs["target"],
  )
  max_translating_group_unit: CountUnit
  group_unit: str = inputs["max_translating_group_unit"]

  if group_unit == "char":
    max_translating_group_unit = CountUnit.Char
  elif group_unit == "token":
    max_translating_group_unit = CountUnit.Token
  else:
    raise Exception(f"unknown max_translating_group_unit: {group_unit}")

  epub_handler = EpubHandler(
    translate=translater.translate,
    max_translating_group=inputs["max_translating_group"],
    max_translating_group_unit=max_translating_group_unit,
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