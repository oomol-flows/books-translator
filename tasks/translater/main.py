import base64

from .epub import EpubHandler
from .transalter import Translate
from .file import translate_epub_file

def main(inputs: dict):
  translate: Translate = lambda x: x
  epub_handler = EpubHandler(
    translate=translate,
    max_paragraph_characters=inputs["max_paragraph_characters"],
    clean_format=inputs["clean_format"],
  )
  zip_data = translate_epub_file(
    handler=epub_handler,
    file_path=inputs["file"],
    book_title=inputs.get("title", None),
  )
  base64_str = base64.b64encode(zip_data).decode("utf-8")

  return { "bin": base64_str }