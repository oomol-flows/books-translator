import re

from lxml import etree
from html import escape
from google.cloud import translate
from .group import ParagraphsGroup

# https://cloud.google.com/translate/docs/advanced/translate-text-advance?hl=zh-cn
class Translator:
  def __init__(
    self, 
    project_id: str, 
    source_language_code: str, 
    target_language_code: str,
    max_paragraph_characters: int,
    clean_format: bool,
  ):
    self.client = translate.TranslationServiceClient()
    self.parser = etree.HTMLParser(recover=True)
    self.project_id = project_id
    self.source_language_code = source_language_code
    self.target_language_code = target_language_code
    self.max_paragraph_characters = max_paragraph_characters
    self.clean_format = clean_format

  def translate(self, text):
    translated_text_list = self._translate_by_google([text], "text/plain")
    if len(translated_text_list) > 0:
      return translated_text_list[0]
    else:
      return text

  def translate_page(self, page_content):
    group = ParagraphsGroup(
      max_paragraph_len=self.max_paragraph_characters,
      # https://support.google.com/translate/thread/18674882/how-many-words-is-maximum-in-google?hl=en
      max_group_len=5000,
    )
    # to remove <?xml version="1.0" encoding="utf-8"?> which lxml cannot parse
    xml = re.sub(r"^<\?xml.*\?>", "", page_content)
    # remove namespace of epub
    xml = re.sub(r"xmlns=\"http://www.w3.org/1999/xhtml\"", "", xml)
    xml = re.sub(r"xmlns:epub=\"http://www.idpf.org/2007/ops\"", "", xml)
    xml = re.sub(r"epub:", "", xml)

    root = etree.fromstring(xml, parser=self.parser)
    body_dom = root.find("body")

    merged_text_list = []
    source_text_list, child_doms = self._collect_child_text_list(body_dom)
    source_text_groups = group.split(source_text_list)

    for child_dom in child_doms:
      body_dom.remove(child_dom)

    for index, source_text_list in enumerate(source_text_groups):   
      source_text_list = self._standardize_paragraph_list(source_text_list)
      target_text_list = self._translate_html(source_text_list)

      if index > 0:
        source_text_list.pop(0)
        target_text_list.pop(0)

      # 长度为 2 的数组来源于裁剪，不得已，此时它的后继的首位不会与它重复，故不必裁剪
      if index < len(source_text_groups) and len(source_text_list) > 2:
        source_text_list.pop()
        target_text_list.pop()

      for source, target in zip(source_text_list, target_text_list):
        source_dom = etree.fromstring(source, parser=self.parser)
        target_dom = etree.fromstring(target, parser=self.parser)

        if source_dom is not None and target_dom is not None:
          body_dom.append(source_dom)
          body_dom.append(target_dom)

    return etree.tostring(root, method="html", encoding="utf-8").decode("utf-8")

  def _collect_child_text_list(self, dom):
    text_list = []
    child_doms = []

    for child_dom in dom.iterchildren():
      text = etree.tostring(child_dom, method="html", encoding="utf-8").decode("utf-8")
      text_list.append(text)
      child_doms.append(child_dom)
    
    return text_list, child_doms

  def _standardize_paragraph_list(self, text_list):
    target_list = []
    for text in text_list:
      text = re.sub(r"[\s\n]+", " ", text)
      if not re.match(r"^[\s\n]*<p.*>", text):
        text = "<p>" + text
      if not re.match(r"</\s*p>[\s\n]*$", text):
        text = text + "</p>"
      if text != "" and not re.match(r"[\s\n]+", text):
        target_list.append(text)
    return target_list

  def _translate_html(self, contents) -> list[str]:
    if self.clean_format:
      contents = contents.copy()
      for i, content in enumerate(contents):
        dom = etree.fromstring(content, parser=self.parser)
        contents[i] = etree.tostring(dom, method="text", encoding="utf-8", pretty_print=False).decode("utf-8")

    if self.clean_format:
      target_list = self._translate_by_google(contents, "text/plain")
      for i, target_content in enumerate(target_list):
        target_list[i] = "<p>" + escape(target_content) + "</p>"
    else:
      target_list = self._translate_by_google(contents, "text/html")

    return target_list

  def _translate_by_google(self, source_text_list, mime_type) -> list[str]:
    indexes = []
    contents = []

    for index, source_text in enumerate(source_text_list):
      if source_text != "" and not re.match(r"^[\s\n]+$", source_text):
        indexes.append(index)
        contents.append(source_text)
    
    target_text_list = [""] * len(source_text_list)

    if len(contents) > 0:
      location = "global"
      parent = f"projects/{self.project_id}/locations/{location}"
      
      try:
        response = self.client.translate_text(
          request={
            "parent": parent,
            "contents": contents,
            "mime_type": mime_type,
            "source_language_code": self.source_language_code,
            "target_language_code": self.target_language_code,
          }
        )
      except Exception as e:
        print("translate contents failed:")
        for content in contents:
          print(content)
        raise e

      for i, translation in enumerate(response.translations):
        index = indexes[i]
        target_text_list[index] = translation.translated_text
    
    return target_text_list