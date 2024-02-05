import re

from lxml import etree
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
  ):
    self.client = translate.TranslationServiceClient()
    self.project_id = project_id
    self.source_language_code = source_language_code
    self.target_language_code = target_language_code
    self.max_paragraph_characters = max_paragraph_characters

  def translate(self, text):
    location = "global"
    parent = f"projects/{self.project_id}/locations/{location}"
    response = self.client.translate_text(
      request={
        "parent": parent,
        "contents": [text],
        "mime_type": "text/plain",
        "source_language_code": self.source_language_code,
        "target_language_code": self.target_language_code,
      }
    )
    for translation in response.translations:
      return translation.translated_text
    
    return title

  def translate_page(self, page_content):
    parser = etree.HTMLParser(recover=True)
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

    root = etree.fromstring(xml, parser=parser)
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
        source_dom = etree.fromstring(source, parser=parser)
        target_dom = etree.fromstring(target, parser=parser)
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
      if not re.match(r"^[\s\n]*<p.*>", text):
        text = "<p>" + text
      if not re.match(r"</\s*p>[\s\n]*$", text):
        text = text + "</p>"
      if text != "" and not re.match(r"[\s\n]+", text):
        target_list.append(text)
    return target_list

  def _translate_html(self, contents) -> list[str]:
    location = "global"
    parent = f"projects/{self.project_id}/locations/{location}"
    response = self.client.translate_text(
      request={
        "parent": parent,
        "contents": contents,
        "mime_type": "text/html",
        "source_language_code": self.source_language_code,
        "target_language_code": self.target_language_code,
      }
    )
    target_list = []
    for translation in response.translations:
      target_list.append(translation.translated_text)
    
    return target_list