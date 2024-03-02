import io
import os
import time
import zipfile
import tempfile
import base64
import shutil

from lxml import etree
from logic import Adapter, Translator, EpubContent

def main(props, context):
  if context.options["adapter"] == "google":
    adapter=Adapter.Google
  elif context.options["adapter"] == "open_ai":
    adapter=Adapter.OpenAI
  else:
    raise Exception("invalid adapter")

  translator = Translator(
    project_id="balmy-mile-348403",
    source_language_code=context.options["source"],
    target_language_code=context.options["target"],
    max_paragraph_characters=context.options.get("max_paragraph_characters", 800),
    clean_format=context.options["clean_format"],
    adapter=adapter,
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

    _translate_folder(context, unzip_path, translator)
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

def _translate_folder(context, path: str, translator):
  epub_content = EpubContent(path)

  if "title" in context.options:
    book_title = context.options["title"]
  else:
    book_title = epub_content.title
    if not book_title is None:
      book_title = _link_translated(book_title, translator.translate([book_title])[0])

  if not book_title is None:
    epub_content.title = book_title

  authors = epub_content.authors
  to_authors = translator.translate(authors)

  for i, author in enumerate(authors):
    authors[i] = _link_translated(author, to_authors[i])

  epub_content.authors = authors
  epub_content.save()

  _transalte_ncx(epub_content, translator)
  _translate_spines(epub_content, path, translator)

def _transalte_ncx(epub_content: EpubContent, translator):
  ncx_path = epub_content.ncx_path

  if ncx_path is not None:
    tree = etree.parse(ncx_path)
    root = tree.getroot()
    namespaces={ "ns": root.nsmap.get(None) }
    text_doms = []
    text_list = []

    for text_dom in root.xpath("//ns:text", namespaces=namespaces):
      text_doms.append(text_dom)
      text_list.append(text_dom.text)
    
    for index, text in enumerate(translator.translate(text_list)):
      text_dom = text_doms[index]
      text_dom.text = _link_translated(text_dom.text, text)

    tree.write(ncx_path, pretty_print=True)

def _translate_spines(epub_content: EpubContent, path: str, translator):
  for spine in epub_content.spines:
    if spine.media_type == "application/xhtml+xml":
      file_path = spine.path
      with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        content = translator.translate_page(file_path, content)
      with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

def _link_translated(origin: str, target: str) -> str:
  if origin == target:
    return origin
  else:
    return f"{origin} - {target}"