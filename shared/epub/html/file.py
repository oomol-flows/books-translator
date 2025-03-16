import re

from xml.etree.ElementTree import fromstring, tostring, Element
from ..types import Translate, ReportProgress
from .dom_operator import read_texts, append_texts
from .empty_tags import to_xml, to_html


_FILE_HEAD_PATTERN = re.compile(r"^<\?xml.*?\?>[\s]*<!DOCTYPE.*?>")
_XMLNS_IN_TAG = re.compile(r"\{[^}]+\}")
_BRACES = re.compile(r"(\{|\})")

def translate_html(translate: Translate, file_content: str, report_progress: ReportProgress) -> str:
  match = re.match(_FILE_HEAD_PATTERN, file_content)
  head = match.group() if match else None
  xml_content = re.sub(_FILE_HEAD_PATTERN, "", to_xml(file_content))

  root = fromstring(xml_content)
  root_attrib = {**root.attrib}
  xmlns = _extract_xmlns(root)

  source_texts = list(read_texts(root))
  target_texts = translate(source_texts, report_progress)
  append_texts(root, target_texts)

  if xmlns is not None:
    root_attrib["xmlns"] = xmlns
  root.attrib = root_attrib
  html_content = tostring(root, encoding="unicode")
  html_content = to_html(html_content)

  if head is not None:
    html_content = head + html_content

  return html_content

def _extract_xmlns(root: Element):
  xmlns: str | None = None
  for element in _all_elements(root):
    match = re.match(_XMLNS_IN_TAG, element.tag)
    element.tag = re.sub(_XMLNS_IN_TAG, "", element.tag)
    if match:
      xmlns = re.sub(_BRACES, "", match.group())
  return xmlns

def _all_elements(parent: Element):
  yield parent
  for child in parent:
    yield from _all_elements(child)