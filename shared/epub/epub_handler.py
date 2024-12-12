import re
import json

from typing import Any
from lxml.etree import tostring, fromstring, HTMLParser
from shared.transalter import Translate
from shared.language import Language
from .group import Paragraph, ParagraphsGroup, CountUnit
from .text_picker import TextPicker
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
  def __init__(
      self,
      translate: Translate,
      source_lan: Language,
      max_paragraph_chars: int,
      max_translating_group: int,
      max_translating_group_unit: CountUnit,
    ):
    self._translate: Translate = translate
    self._parser: Any = HTMLParser(recover=True)
    self._group: ParagraphsGroup = ParagraphsGroup(
      source_lan=source_lan,
      max_paragraph_chars=max_paragraph_chars,
      max_translating_group=max_translating_group,
      max_translating_group_unit=max_translating_group_unit,
    )

  def translate_page(self, file_path: str, page_content: str):
    xml = _XML(page_content, self._parser)
    picker = TextPicker(xml.root, "text")
    source_texts = picker.pick_texts()
    target_texts: list[str] = self.translate(source_texts)
    picker.append_texts(target_texts)

    return xml.encode()

  def translate(self, text_list: list[str]) -> list[str]:
    paragraph_groups = self._group.split(text_list)
    target_texts_in_group: dict[int, list[str]] = {}

    for index, paragraphs in enumerate(paragraph_groups):
      source_text_list = list(map(lambda x: self._clean_p_tag(x.text), paragraphs))
      target_paragraphs: list[Paragraph] = []
      for i, text in enumerate(self._translate_text_list(source_text_list)):
        target_paragraphs.append(Paragraph(
          text=text, 
          index=paragraphs[i].index,
          count=paragraphs[i].count,
        ))

      # 长度为 2 的数组来源于裁剪，不得已，此时它的后继的首位不会与它重复，故不必裁剪
      if index > 0 and len(paragraph_groups[index - 1]) > 2:
        target_paragraphs.pop(0)
      if index < len(paragraph_groups) - 1 and len(paragraphs) > 2:
        target_paragraphs.pop()

      for target in target_paragraphs:
        if target.index in target_texts_in_group:
          target_texts_in_group[target.index].append(target.text)
        else:
          target_texts_in_group[target.index] = [target.text]

    target_texts: list[str] = ["" for _ in range(len(text_list))]

    for index in range(len(text_list)):
      if index in target_texts_in_group:
        texts = target_texts_in_group[index]
        text = "".join(texts).strip()
        target_texts[index] = text

    return target_texts

  def _translate_text_list(self, source_text_list: list[str]):
    target_text_list: list[str] = [""] * len(source_text_list)
    to_translated_text_list: list[str] = []
    index_list: list[int] = []

    for index, text in enumerate(source_text_list):
      if self._is_not_empty(text):
        text = f"<p>{text}</p>"
        dom = create_node(text, parser=self._parser)
        unformat_text = self._unformat(dom)

        if self._is_not_empty(unformat_text):
          to_translated_text_list.append(unformat_text)
          index_list.append(index)

    for i, text in enumerate(self._translate(to_translated_text_list)):
      index = index_list[i]
      target_text_list[index] = text

    return target_text_list

  def _unformat(self, dom) -> str:
    return tostring(dom, method="text", encoding="utf-8", pretty_print=False).decode("utf-8")

  def _is_not_empty(self, text: str) -> bool:
    return not re.match(r"^[\s\n]*$", text)

  def _wrap_with_p(self, p_dom, text: str) -> str:
    attributes_list = []
    for key, value in p_dom.attrib.items():
      json_value = json.dumps(value)
      attributes_list.append(f"{key}={json_value}")
    if len(attributes_list) > 1:
      attributes = " ".join(attributes_list)
      return f"<p {attributes}>{text}</p>"
    else:
      return f"<p>{text}</p>"

  def _clean_p_tag(self, text: str) -> str:
    text = re.sub(r"^[\s\n]*<p[^>]*>", "", text)
    text = re.sub(r"</\s*p>[\s\n]*$", "", text)
    text = re.sub(r"[\s\n]+", " ", text)
    return text