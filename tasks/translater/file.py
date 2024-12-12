import io
import os
import zipfile
import tempfile
import shutil

from typing import Optional
from lxml.etree import parse
from oocana import Context

from shared.epub import EpubHandler, EpubContent
from .ctx_tqdm import tqdm


def translate_epub_file(
  context: Context,
  handler: EpubHandler, 
  file_path: str, 
  book_title: Optional[str]) -> bytes:

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

    _translate_folder(
      context=context,
      handler=handler,
      path=unzip_path,
      book_title=book_title,
    )
    in_memory_zip = io.BytesIO()

    with zipfile.ZipFile(in_memory_zip, "w") as zip_file:
      for root, _, files in os.walk(unzip_path):
        for file in files:
          file_path = os.path.join(root, file)
          relative_path = os.path.relpath(file_path, unzip_path)
          zip_file.write(file_path, arcname=relative_path)
          
    in_memory_zip.seek(0)
    zip_data = in_memory_zip.read()

    return zip_data

  finally:
    shutil.rmtree(unzip_path)

def _translate_folder(
  context: Context,
  handler: EpubHandler,
  path: str, 
  book_title: Optional[str],
):
  epub_content = EpubContent(path)

  if book_title is None:
    book_title = epub_content.title
    if not book_title is None:
      book_title = _link_translated(book_title, handler.translate([book_title])[0])

  if not book_title is None:
    epub_content.title = book_title

  authors = epub_content.authors
  to_authors = handler.translate(authors)

  for i, author in enumerate(authors):
    authors[i] = _link_translated(author, to_authors[i])

  epub_content.authors = authors
  epub_content.save()

  _transalte_ncx(epub_content, handler)
  _translate_spines(context, epub_content, handler)

def _transalte_ncx(epub_content: EpubContent, handler: EpubHandler):
  ncx_path = epub_content.ncx_path

  if ncx_path is not None:
    tree = parse(ncx_path)
    root = tree.getroot()
    namespaces={ "ns": root.nsmap.get(None) }
    text_doms = []
    text_list = []

    for text_dom in root.xpath("//ns:text", namespaces=namespaces):
      text_doms.append(text_dom)
      text_list.append(text_dom.text)
    
    for index, text in enumerate(handler.translate(text_list)):
      text_dom = text_doms[index]
      text_dom.text = _link_translated(text_dom.text, text)

    tree.write(ncx_path, pretty_print=True)

def _translate_spines(context: Context, epub_content: EpubContent, handler: EpubHandler):
  spines = epub_content.spines
  for spine in tqdm(context, spines):
    if spine.media_type == "application/xhtml+xml":
      file_path = spine.path
      with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        content = handler.translate_page(file_path, content)
      with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

def _link_translated(origin: str, target: str) -> str:
  if origin == target:
    return origin
  else:
    return f"{origin} - {target}"