import io
import os
import zipfile
import tempfile
import shutil

from typing import Optional
from lxml import etree
from oocana import Context

from .progress import Progress, SubProgress
from .epub import EpubHandler, EpubContent

def translate_epub_file(
  context: Context,
  handler: EpubHandler, 
  file_path: str, 
  book_title: Optional[str]) -> bytes:

  progress = Progress(context)
  unzip_path = tempfile.mkdtemp()

  unzip_progress = progress.sub(0.05)
  zip_progress = progress.sub(0.05)
  translate_others_progress = progress.sub(0.1)
  translate_spines_progress = progress.sub(0.1)

  try:
    with zipfile.ZipFile(file_path, "r") as zip_ref:
      for member in zip_ref.namelist():
        target_path = os.path.join(unzip_path, member)
        if member.endswith("/"):
            os.makedirs(target_path, exist_ok=True)
        else:
          with zip_ref.open(member) as source, open(target_path, "wb") as file:
            file.write(source.read())

    unzip_progress(1.0)
    _translate_folder(
      handler=handler,
      path=unzip_path,
      book_title=book_title,
      translate_others_progress=translate_others_progress,
      translate_spines_progress=translate_spines_progress,
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
    zip_progress(1.0)

    return zip_data

  finally:
    shutil.rmtree(unzip_path)

def _translate_folder(
  handler: EpubHandler,
  translate_others_progress: SubProgress,
  translate_spines_progress: SubProgress,
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
  
  translate_others_progress(0.3)
  authors = epub_content.authors
  to_authors = handler.translate(authors)

  for i, author in enumerate(authors):
    authors[i] = _link_translated(author, to_authors[i])

  epub_content.authors = authors
  epub_content.save()
  translate_others_progress(0.7)

  _transalte_ncx(epub_content, handler)
  translate_others_progress(1.0)

  _translate_spines(translate_spines_progress, epub_content, handler)

def _transalte_ncx(epub_content: EpubContent, handler: EpubHandler):
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
    
    for index, text in enumerate(handler.translate(text_list)):
      text_dom = text_doms[index]
      text_dom.text = _link_translated(text_dom.text, text)

    tree.write(ncx_path, pretty_print=True)

def _translate_spines(progress: SubProgress, epub_content: EpubContent, handler: EpubHandler):
  spines = epub_content.spines
  for i, spine in enumerate(spines):
    if spine.media_type == "application/xhtml+xml":
      file_path = spine.path
      with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        content = handler.translate_page(file_path, content)
      with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    progress(float(i) / float(len(spines)))

def _link_translated(origin: str, target: str) -> str:
  if origin == target:
    return origin
  else:
    return f"{origin} - {target}"