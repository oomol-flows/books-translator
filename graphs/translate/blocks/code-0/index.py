import io
import os
import time
import zipfile
import tempfile
import base64
import shutil

from logic import Translator, EpubContent

def main(props, context):
  translator = Translator(
    project_id="balmy-mile-348403",
    source_language_code=context.options["source"],
    target_language_code=context.options["target"],
    max_paragraph_characters=context.options.get("max_paragraph_characters", 800),
    clean_format=context.options["clean_format"],
  )
  file_path = context.options["file"]
  unzip_path = tempfile.mkdtemp()

  try:
    with zipfile.ZipFile(file_path, "r") as zip_ref:
      for member in zip_ref.namelist():
        target_path = os.path.join(unzip_path, member)
        if member.endswith("/"):
            os.makedirs(target_path, exist_ok=True)
        else:
          with zip_ref.open(member) as source, open(target_path, "wb") as file:
              file.write(source.read())

    _translate_folder(unzip_path, translator)
    in_memory_zip = io.BytesIO()

    with zipfile.ZipFile(in_memory_zip, "w") as zip_file:
      for root, _, files in os.walk(unzip_path):
        for file in files:
          file_path = os.path.join(root, file)
          relative_path = os.path.relpath(file_path, unzip_path)
          zip_file.write(file_path, arcname=relative_path)
          
    in_memory_zip.seek(0)
    zip_data = in_memory_zip.read()
    base64_str = base64.b64encode(zip_data).decode("utf-8")
    context.result(base64_str, "bin", True)

  finally:
    shutil.rmtree(unzip_path)

def _translate_folder(path: str, translator):
  content = EpubContent(os.path.join(path, "content.opf"))
  for spine in content.spines:
    if spine.media_type == "application/xhtml+xml":
      file_path = os.path.abspath(os.path.join(path, spine.href))
      with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        content = translator.translate_page(file_path, content)
      with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

  # set metadata
  # book.set_identifier("id123456")
  # book.set_title("Sample book")
  # book.set_language("en")

  # book.add_author("Author Authorowski")
  # book.add_author(
  #     "Danko Bananko",
  #     file_as="Gospodin Danko Bananko",
  #     role="ill",
  #     uid="coauthor",
  # )
  # add default NCX and Nav file
  # book.add_item(epub.EpubNcx())
  # book.add_item(epub.EpubNav())

  # define CSS style
  # style = "BODY {color: white;}"
  # nav_css = epub.EpubItem(
  #     uid="style_nav",
  #     file_name="style/nav.css",
  #     media_type="text/css",
  #     content=style,
  # )
  # # add CSS file
  # book.add_item(nav_css)

  # book.toc = origin_book.toc
  # book.spine = origin_book.spine

  # for item in origin_book.items:
  #   if item.get_type() == ITEM_DOCUMENT:
  #     content = item.get_content().decode("utf-8")
  #     print(">>>", item.file_name)
  #     if "titlepage.xhtml" == item.file_name:
  #       print(content)
  #   book.add_item(item)

  # define Table Of Contents
  # book.toc = (
  #     epub.Link("chap_01.xhtml", "Introduction", "intro"),
  #     (epub.Section("Simple book"), (first_chapter,)),
  # )


  # first_chapter = None

  # for item in _get_items(translator, origin_book):
  #   if item.get_type() == ITEM_DOCUMENT:
  #     first_chapter = item
  #   book.add_item(item)

  # basic spine
  # book.spine = ["nav", first_chapter]

  # if "title" in context.options:
  #   new_book.set_title(context.options["title"])
  # else:
  #   new_book.set_title(translator.translate(book.title))

  # for author in book.get_metadata("DC", "creator"):
  #   new_book.add_author(author)