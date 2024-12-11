import re
import base64

from typing import Any
from oocana import Context
from tasks.translater.transalter.llm import AITranslator

def main(inputs: dict[str, Any], context: Context):
  timestamps: list[str] = []
  texts: list[str] = []

  with open(inputs["srt_file"], "r", encoding="utf-8") as file:

    for chunk in file.read().split("\n\n"):
      lines = chunk.split("\n")
      if len(lines) < 3:
        continue
      timestamp = strip_text(lines[1])
      text = strip_text("\n".join(lines[2:]))
      timestamps.append(timestamp)
      texts.append(text)
  
  group_size = inputs["group_size"]
  translater = AITranslator(
    model="deepseek-chat",
    api_url="https://api.deepseek.com/chat/completions",
    auth_token=inputs["ai_token"],
    source_lan="English",
    target_lan="Chinese",
  )
  target_texts: list[str] = []

  for offset in range(0, len(texts), group_size):
    sub_texts = texts[offset:offset + group_size]
    sub_target_texts = translater.translate(sub_texts)
    target_texts.extend(sub_target_texts)
    context.report_progress(float(offset) / float(len(texts)) * 100.0)

  context.report_progress(100.0)
  files_lines: list[str] = []

  for i, text in enumerate(target_texts):
    timestamp = timestamps[i]
    files_lines.append(f"{i + 1}\n{timestamp}\n{text}")

  bin = "\n\n".join(files_lines).encode("utf-8")
  base64_str = base64.b64encode(bin)

  return { "bin": base64_str }

def strip_text(text: str) -> str:
  return re.sub(r"^[\s\n]+|[\s\n]+$", "", text)
