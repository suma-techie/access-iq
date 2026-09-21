
import io
import logging
from abc import ABC, abstractmethod

from pypdf import PdfReader

from app.services.llm import LLMError, chat_completion

logger = logging.getLogger(__name__)

STRUCTURING_PROMPT = (
    "You clean up raw text extracted from a PDF so it can be used as a grounding "
    "source for access-permission lookups. Preserve every concrete fact (permission "
    "names, role names, system names, instructions) verbatim. Remove page-header/footer "
    "noise and fix obvious line-wrap artifacts. Do not summarize or omit content. "
    "Output plain text only."
)


class ParserInterface(ABC):
    @abstractmethod
    def parse(self, content: bytes) -> str:
        ...


class PdfParser(ParserInterface):
    def parse(self, content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        raw_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        raw_text = raw_text.strip()
        if not raw_text:
            return ""
        return self._structure(raw_text)

    def _structure(self, raw_text: str) -> str:
        try:
            message = chat_completion(
                messages=[
                    {"role": "system", "content": STRUCTURING_PROMPT},
                    {"role": "user", "content": raw_text[:60000]},
                ],
            )
            return message.get("content") or raw_text
        except LLMError:
            logger.exception("Document structuring LLM call failed; falling back to raw extracted text")
            return raw_text


PARSERS: dict[str, ParserInterface] = {
    "pdf": PdfParser(),
}


def get_parser(file_type: str) -> ParserInterface | None:
    return PARSERS.get(file_type)
