import os

from pathlib import Path
from oocana import Context
from epub_translator import translate, LLM, Language


#region generated meta
import typing
from oocana import LLMModelOptions
class Inputs(typing.TypedDict):
  model: LLMModelOptions
  source_file: str
  translated_file: str | None
  language: typing.Literal["zh-Hans", "zh-Hant", "en", "fr", "de", "es", "ru", "it", "pt", "ja", "ko"]
  prompt: str | None
  max_chunk_tokens: int
  threads: int
  retry_times: int
  retry_interval_seconds: float
class Outputs(typing.TypedDict):
  translated_file: str
#endregion

def main(params: Inputs, context: Context) -> Outputs:
  base_path = Path(context.session_dir) / "books-translator"
  translated_file = params["translated_file"]
  if translated_file is None:
    translated_file = base_path / "output" / f"{context.job_id}.epub"
  else:
    translated_file = Path(translated_file)

  env = context.oomol_llm_env
  model = params["model"]
  llm=LLM(
    key=env["api_key"],
    url=env["base_url_v1"],
    model=model["model"],
    top_p=float(model["top_p"]),
    temperature=float(model["temperature"]),
    token_encoding="o200k_base",
    retry_times=int(params["retry_times"]),
    retry_interval_seconds=params["retry_interval_seconds"],
  )
  translate(
    llm=llm,
    source_path=Path(params["source_file"]),
    translated_path=translated_file,
    target_language=_parse_language_code(params["language"]),
    user_prompt=params["prompt"],
    working_path=base_path / "workspace",
    max_chunk_tokens_count=params["max_chunk_tokens"],
    max_threads_count=params["threads"],
    report_progress=lambda p: context.report_progress(100.0 * p),
  )
  return {
    "translated_file": str(translated_file)
  }

def _parse_language_code(lang_code: str) -> Language:
  if lang_code == "zh-Hans" or lang_code == "zh-CN":
    return Language.SIMPLIFIED_CHINESE
  elif lang_code == "zh-Hant" or lang_code == "zh-TW":
    return Language.TRADITIONAL_CHINESE
  elif lang_code.startswith("en"):
    return Language.ENGLISH
  elif lang_code.startswith("fr"):
    return Language.FRENCH
  elif lang_code.startswith("de"):
    return Language.GERMAN
  elif lang_code.startswith("es"):
    return Language.SPANISH
  elif lang_code.startswith("ru"):
    return Language.RUSSIAN
  elif lang_code.startswith("it"):
    return Language.ITALIAN
  elif lang_code.startswith("pt"):
    return Language.PORTUGUESE
  elif lang_code.startswith("ja"):
    return Language.JAPANESE
  elif lang_code.startswith("ko"):
    return Language.KOREAN
  else:
    raise ValueError(f"Unsupported language code: {lang_code}")