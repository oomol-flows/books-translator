import hashlib
import shutil

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
  source_file = Path(params["source_file"])
  translated_file = params["translated_file"]
  if translated_file is None:
    translated_file = Path(context.session_dir) / "books-translator" / f"{context.job_id}.epub"
    translated_file.parent.mkdir(parents=True, exist_ok=True)
  else:
    translated_file = Path(translated_file)

  working_path = _prepare_working_path(source_file, context)
  logs_dir_path = Path(context.tmp_pkg_dir) / "logs"

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
    log_dir_path=logs_dir_path,
  )
  translate(
    llm=llm,
    source_path=source_file,
    translated_path=translated_file,
    target_language=_parse_language_code(params["language"]),
    user_prompt=params["prompt"],
    working_path=working_path,
    max_chunk_tokens_count=params["max_chunk_tokens"],
    max_threads_count=params["threads"],
    report_progress=lambda p: context.report_progress(100.0 * p),
  )
  return {
    "translated_file": str(translated_file)
  }

def _prepare_working_path(source_file: Path, context: Context) -> Path:
  st_mtime = source_file.stat().st_mtime
  hash = hashlib.new(name="sha512")
  hash.update(f"{st_mtime}:{source_file}".encode("utf-8"))
  hash_hex = hash.hexdigest()
  pkg_path = Path(context.tmp_pkg_dir)
  working_path = pkg_path / hash_hex

  if not working_path.exists() or not working_path.is_dir():
    if pkg_path.exists():
      for file in pkg_path.iterdir():
        if file.is_file():
          file.unlink()
        elif file.is_dir():
          shutil.rmtree(file)
    working_path.mkdir(parents=True, exist_ok=True)

  return working_path

def _parse_language_code(lang_code: str) -> Language:
  for language in Language:
    if language.value == lang_code:
      return language
  raise ValueError(f"Unsupported language code: {lang_code}")