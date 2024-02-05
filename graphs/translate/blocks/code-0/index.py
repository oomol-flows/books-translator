import base64

from io import BytesIO
from ebooklib import epub, ITEM_DOCUMENT
from logic import Translator

def main(props, context):
  book = epub.read_epub(context.options["file"])
  translater = Translator(
    project_id="balmy-mile-348403",
    source_language_code=context.options["source"],
    target_language_code=context.options["target"],
    max_paragraph_characters=context.options.get("max_paragraph_characters", 800),
    clean_format=context.options["clean_format"],
  )
  if "title" in context.options:
    title = context.options["title"]
  else:
    title = translater.translate(book.title)

  book.set_title(title)

  for item in book.get_items():
    if item.get_type() == ITEM_DOCUMENT:
      content = item.get_content().decode("utf-8")
      content = translater.translate_page(content)
      item.set_content(content)

  bytes_io = BytesIO()
  epub.write_epub(bytes_io, book, {})
  base64_str = base64.b64encode(bytes_io.getvalue()).decode("utf-8")

  context.result(base64_str, "bin", True)
