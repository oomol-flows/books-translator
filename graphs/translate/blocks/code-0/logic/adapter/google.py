from google.cloud import translate

# https://cloud.google.com/translate/docs/advanced/translate-text-advance?hl=zh-cn
class GoogleTranslator:
  def __init__(self, 
    project_id: str,
    source_language_code: str, 
    target_language_code: str,
  ):
    self.project_id = project_id
    self.source_language_code = source_language_code
    self.target_language_code = target_language_code
    self._client = translate.TranslationServiceClient()

  def translate(self, text_list: list[str], mime_type: str):
    location = "global"
    parent = f"projects/{self.project_id}/locations/{location}"
    response = self._client.translate_text(
      request={
        "parent": parent,
        "contents": text_list,
        "mime_type": mime_type,
        "source_language_code": self.source_language_code,
        "target_language_code": self.target_language_code,
      }
    )
    return list(map(
      lambda x: x.translated_text,
      response.translations,
    ))
