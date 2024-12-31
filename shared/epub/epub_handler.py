import re

from typing import Any
from lxml.etree import tostring, fromstring, HTMLParser
from .text_picker import TextPicker
from .types import Translate, ReportProgress
from .utils import create_node

class _XML:
  def __init__(self, page_content: str, parser: HTMLParser):
    regex = r"^<\?xml.*\?>"
    match = re.match(regex, page_content)
    xml = re.sub(regex, "", page_content)

    if match:
      self.head = match.group()
    else:
      self.head = ""

    self.root: Any = fromstring(xml, parser=parser)
    self._nsmap: dict = self.root.nsmap.copy()
    self.root.nsmap.clear()

  def encode(self) -> str:
    for key, value in self._nsmap.items():
      self.root.nsmap[key] = value

    text = tostring(self.root, method="html", encoding="utf-8")
    text = text.decode("utf-8")

    # HTML 规定了一系列自闭标签，这些标签需要改成非自闭的，因为 EPub 格式不支持
    # https://www.tutorialspoint.com/which-html-tags-are-self-closing
    text = re.sub(r"<((img|br|hr|input|col|base|meta|link|area)[^>]*?)(?<!/)>", r"<\1/>", text)
    text = self.head + text

    return text

class EpubHandler:
  def __init__(self, translate: Translate):
    self.translate: Translate = translate
    self._parser: Any = HTMLParser(recover=True)

  def translate_page(self, page_content: str, report_progress: ReportProgress):
    xml = _XML(page_content, self._parser)
    picker = TextPicker(xml.root, "text")
    source_texts = [self._unformat_text(text) for text in picker.pick_texts()]
    target_texts = self.translate(source_texts, report_progress)
    picker.append_texts(target_texts)

    return xml.encode()

  def _unformat_text(self, text: str) -> str:
    text = self._clean_p_tag(text)
    if self._is_not_empty(text):
      text = f"<p>{text}</p>"
      dom = create_node(text, parser=self._parser)
      text = tostring(
        dom, 
        method="text", 
        encoding="utf-8", 
        pretty_print=False,
      ).decode("utf-8")
    return text

  def _clean_p_tag(self, text: str) -> str:
    text = re.sub(r"^[\s\n]*<p[^>]*>", "", text)
    text = re.sub(r"</\s*p>[\s\n]*$", "", text)
    text = re.sub(r"[\s\n]+", " ", text)
    return text

  def _is_not_empty(self, text: str) -> bool:
    return not re.match(r"^[\s\n]*$", text)