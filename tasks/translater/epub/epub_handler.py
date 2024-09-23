import re
import json

from typing import Optional
from lxml.etree import tostring, fromstring, HTMLParser

from ..transalter import Translate
from .group import ParagraphsGroup
from .text_picker import TextPicker
from .utils import create_node, escape_ascii

class _XML:
  def __init__(self, page_content: str, parser: HTMLParser):
    regex = r"^<\?xml.*\?>"
    match = re.match(regex, page_content)
    xml = re.sub(regex, "", page_content)

    if match:
      self.head = match.group()
    else:
      self.head = ""

    self.root = fromstring(xml, parser=parser)
    self.nsmap: dict = self.root.nsmap.copy()
    self.root.nsmap.clear()

  def encode(self) -> str:
    for key, value in self.nsmap.items():
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
    max_paragraph_characters: int,
    clean_format: bool,
  ):
    self._translate: Translate = translate
    self.parser = HTMLParser(recover=True)
    self.clean_format = clean_format
    self.group = ParagraphsGroup(
      max_paragraph_len=max_paragraph_characters,
      # https://support.google.com/translate/thread/18674882/how-many-words-is-maximum-in-google?hl=en
      max_group_len=5000,
    )

  def translate(self, text_list: list[str]):
    to_text_list: list[str] = []
    for text_list in self.group.split_text_list(text_list):
      for text in self._emit_translation_task(text_list):
        to_text_list.append(text)
    return to_text_list

  def translate_page(self, file_path: str, page_content: str):
    xml = _XML(page_content, self.parser)
    picker = TextPicker(xml.root, "text")
    source_texts = picker.pick_texts()
    target_texts: list[str] = ["" for _ in range(len(source_texts))]
    translated_group_list = self._translate_group_by_group(file_path, source_texts)
    target_texts_in_group: dict[int, list[str]] = {}

    for _, target_text_list, index_list in translated_group_list:
      for i, text in enumerate(target_text_list):
        index = index_list[i]
        if text != "":
          if self.clean_format:
            text = escape_ascii(text)
          else:
            text = self._clean_p_tag(text)
        if index in target_texts_in_group:
          target_texts_in_group[index].append(text)
        else:
          target_texts_in_group[index] = [text]

    for index in range(len(source_texts)):
      if index in target_texts_in_group:
        texts = target_texts_in_group[index]
        text = "".join(texts).strip()
        target_texts[index] = text

    picker.append_texts(target_texts)

    return xml.encode()

  def _translate_group_by_group(self, file_path: str, source_text_list: list[str]):
    target_list = []
    paragraph_group_list = self.group.split_paragraphs(source_text_list)

    for index, paragraph_list in enumerate(paragraph_group_list):
      source_text_list = list(map(lambda x: self._clean_p_tag(x.text), paragraph_list))
      target_text_list = self._translate_text_list(source_text_list)
      index_list = list(map(lambda x: x.index, paragraph_list))

      # 长度为 2 的数组来源于裁剪，不得已，此时它的后继的首位不会与它重复，故不必裁剪
      if index > 0 and len(paragraph_group_list[index - 1]) > 2:
        source_text_list.pop(0)
        target_text_list.pop(0)
        index_list.pop(0)

      if index < len(paragraph_group_list) - 1 and len(paragraph_list) > 2:
        source_text_list.pop()
        target_text_list.pop()
        index_list.pop()

      target_list.append((source_text_list, target_text_list, index_list))
      print(f"Translate completed: {file_path} task {index + 1}/{len(paragraph_group_list)}")

    return target_list

  def _translate_text_list(self, source_text_list):
    target_text_list = [""] * len(source_text_list)
    to_translated_text_list = []
    index_list = []

    for index, text in enumerate(source_text_list):
      if self._is_not_empty(text):
        text = f"<p>{text}</p>"
        dom = create_node(text, parser=self.parser)

        if self.clean_format:
          unformat_text = self._unformat(dom)
          text = unformat_text
        else:
          # Some English books use <span> for indentation, which will affect translation and should be removed.
          changed = self._try_to_clean_space(dom)
          if changed:
            bin_text = tostring(dom, method="html", encoding="utf-8")
            text = bin_text.decode("utf-8")
          unformat_text = self._unformat(dom)

        if self._is_not_empty(unformat_text):
          to_translated_text_list.append(text)
          index_list.append(index)

    for i, text in enumerate(self._emit_translation_task(to_translated_text_list)):
      index = index_list[i]
      target_text_list[index] = text

    return target_text_list

  def _emit_translation_task(self, source_text_list) -> list[str]:
    indexes = []
    contents = []

    for index, source_text in enumerate(source_text_list):
      if source_text != "" and not re.match(r"^[\s\n]+$", source_text):
        indexes.append(index)
        contents.append(source_text)
    
    target_text_list = [""] * len(source_text_list)

    if len(contents) > 0:
      try:
        for i, text in enumerate(self._translate(contents)):
          index = indexes[i]
          target_text_list[index] = text

      except Exception as e:
        print("translate contents failed:")
        for content in contents:
          print(content)
        raise e

    return target_text_list

  def _try_to_clean_space(self, dom):
    span_list = []
    changed = False
    for dom in dom.xpath(".//span"):
      span_list.append(dom)
    for dom in span_list:
      text_bin = tostring(dom, method="text", encoding="utf-8", pretty_print=False)
      if self._is_not_empty(text_bin.decode("utf-8")):
        continue
      tail = dom.tail
      if tail is None:
        tail = " "
      else:
        tail = f" {tail}"
      dom.tail = tail
      dom.getparent().remove(dom)
      changed = True
    return changed

  def _unformat(self, dom):
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