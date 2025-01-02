from oocana import Context
from shared.epub import EpubHandler
from shared.translater import Translater, LLM_API
from .file import translate_epub_file
from .llm_parser import parse

def main(params: dict, context: Context):
  llm = parse(params, context)
  timeout: float | None = params["timeout"]
  if timeout == 0.0:
    timeout = None

  translater = Translater(
    api=llm.api,
    key=llm.key,
    url=llm.url,
    model=llm.model,
    temperature=params["temperature"],
    timeout=timeout,
    source_lan=params["source"],
    target_lan=params["target"],
    group_max_tokens=params["max_translating_group"],
  )
  epub_handler = EpubHandler(
    translate=translater.translate,
  )
  zip_data = translate_epub_file(
    context=context,
    handler=epub_handler,
    file_path=params["file"],
    book_title=params.get("title", None),
  )
  return { "binary": zip_data }