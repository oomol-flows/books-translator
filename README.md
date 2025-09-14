# Books Translator

Use LLM to translate EPUB e-books. The translated book will retain the original text and display the translation alongside the original text.

## Main Fields

In most cases, you only need to configure these three fields to run completely.

- `source_file`: The original EPUB file to be translated
- `translated_file`: Save location for the translated EPUB file. If not specified, it will be saved in `session_dir`.
- `language`: Target language for translation

## Custom Prompts

You can fill in prompts in the `prompt` field to provide necessary information for LLM book translation. For example, you can include glossaries and character name conventions. Just describe it to the LLM in natural language.

## Additional Fields

If you don't want to understand the following fields, just keep their original values.

- `max_chunk_tokens`: When segmenting for translation, limit the maximum number of tokens per segment. Due to the characteristics of LLM, it's impossible to input an entire book into a large language model for translation at once. Therefore, the book will be segmented and submitted to the LLM. This parameter is used to limit the maximum length of each segment (in tokens).
- `threads`: Concurrent translation requests. If you feel the translation is too slow, you can increase this value. However, it's recommended not to exceed 16 concurrent requests, as it will trigger rate limiting policies from LLM providers.
- `retry_times`: How many consecutive failures of the same segment before declaring failure.
- `retry_interval_seconds`: How many seconds to wait before retrying after a failed attempt.

## Output Fields

`translated_file` - The file path where the translated file is saved.

## Resume Translation

When translating the same book, if you actively interrupt or are interrupted due to network issues, the translated progress will not be lost. After continuing to run, you can resume translation from where you left off last time.