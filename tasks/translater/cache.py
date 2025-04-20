import os

from typing import Callable
from hashlib import sha256
from json import loads, dumps
from oocana import Context


class CacheTranslater:
  def __init__(
      self,
      context: Context,
      translate: Callable[[list[str], Callable[[float], None]], list[str]],
    ) -> None:
    self._context: Context = context
    self._translate: Callable[[list[str], Callable[[float], None]], list[str]] = translate

  def translate(
        self,
        source_texts: list[str],
        report_progress: Callable[[float], None],
      ) -> list[str]:

    cache_path: str = os.path.join(self._context.tmp_pkg_dir, "translated")
    os.makedirs(cache_path, exist_ok=True)

    hash = self._to_hash(source_texts)
    cache_file_path = os.path.join(cache_path, f"{hash}.json")
    translated_texts: list[str]

    if os.path.exists(cache_file_path):
      with open(cache_file_path, "r", encoding="utf-8") as cache_file:
        translated_texts = loads(cache_file.read())
        report_progress(1.0)
    else:
      translated_texts = self._translate(source_texts, report_progress)
      with open(cache_file_path, "w", encoding="utf-8") as cache_file:
        cache_file.write(dumps(
          obj=translated_texts,
          ensure_ascii=False,
          indent=2,
        ))

    return translated_texts

  def _to_hash(self, texts: list[str]) -> str:
    hash = sha256()
    for text in texts:
      data = text.encode(encoding="utf-8")
      hash.update(data)
      hash.update(b"\x03") # ETX means string's end
    return hash.hexdigest()