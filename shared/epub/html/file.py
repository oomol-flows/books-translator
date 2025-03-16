import re

from xml.etree.ElementTree import fromstring, tostring, Element
from ..types import Translate, ReportProgress
from .dom_operator import read_texts, append_texts
from .empty_tags import to_xml, to_html


_FILE_HEAD_PATTERN = re.compile(r"^<\?xml.*?\?>[\s]*<!DOCTYPE.*?>")

def translate_html(translate: Translate, file_content: str, report_progress: ReportProgress) -> str:
  match = re.match(_FILE_HEAD_PATTERN, file_content)
  head = match.group() if match else None
  xml_content = re.sub(_FILE_HEAD_PATTERN, "", to_xml(file_content))

  root = fromstring(xml_content)
  root_attrib = {**root.attrib}

  for element in _all_elements(root):
    element.tag = re.sub(r"\{[^}]+\}", "", element.tag)

  source_texts = list(read_texts(root))
  target_texts = translate(source_texts, report_progress)
  append_texts(root, target_texts)

  root.attrib = {
    **root_attrib,
    "xmlns": "http://www.w3.org/1999/xhtml",
  }
  html_content = tostring(root, encoding="unicode")
  html_content = to_html(html_content)

  if head is not None:
    html_content = head + html_content

  return html_content

def _all_elements(parent: Element):
  yield parent
  for child in parent:
    yield from _all_elements(child)