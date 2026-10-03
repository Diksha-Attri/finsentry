from dataclasses import dataclass
from typing import Literal
from bs4 import BeautifulSoup, Tag
import re


@dataclass
class DocumentChunk:
    chunk_type: Literal["prose", "table"]
    content: str
    section_context: str
    table_index: int | None = None


class LayoutAwareParser:
    """Parses raw SEC HTML filings into distinct prose and structured table chunks."""

    def __init__(self) -> None:
        self.item_regex = re.compile(
            r"(Item\s+(?:1A|1B|1|7A|7|8|9A|9)[\.:\s\-]+[^\n\r<]{3,80})",
            re.IGNORECASE,
        )

    def _html_table_to_markdown(self, table_tag: Tag) -> str | None:
        """Converts an HTML table element to clean Markdown syntax."""
        rows = table_tag.find_all("tr")
        if not rows:
            return None

        matrix: list[list[str]] = []
        for tr in rows:
            cells = tr.find_all(["td", "th"])
            row_data = [
                re.sub(r"\s+", " ", cell.get_text(strip=True).replace("|", "/"))
                for cell in cells
            ]
            if any(row_data):
                matrix.append(row_data)

        if not matrix or len(matrix) < 2:
            return None

        max_cols = max(len(r) for r in matrix)
        if max_cols < 2:
            return None

        padded_matrix = [r + [""] * (max_cols - len(r)) for r in matrix]

        header = padded_matrix[0]
        separator = ["---"] * max_cols
        data_rows = padded_matrix[1:]

        md_lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(separator) + " |",
        ]
        for row in data_rows:
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    def parse(self, raw_html: str) -> list[DocumentChunk]:
        """Decomposes the raw document into typed document chunks."""
        soup = BeautifulSoup(raw_html, "lxml")

        # Strip unneeded scripts and styling
        for element in soup(["script", "style", "meta", "noscript"]):
            element.decompose()

        chunks: list[DocumentChunk] = []
        current_section = "General Disclosures"
        table_counter = 0

        # Process document elements in DOM order
        for element in soup.find_all(["h1", "h2", "h3", "h4", "table", "p", "div"]):
            # Check if this element defines a new SEC section header
            text_preview = element.get_text(strip=True)
            match = self.item_regex.search(text_preview)
            if match:
                current_section = match.group(1).strip()

            # Process Tables
            if element.name == "table":
                md_table = self._html_table_to_markdown(element)
                if md_table:
                    table_counter += 1
                    chunks.append(
                        DocumentChunk(
                            chunk_type="table",
                            content=md_table,
                            section_context=current_section,
                            table_index=table_counter,
                        )
                    )
            # Process Prose
            elif element.name in ["p", "div"]:
                # If this div/p contains nested content blocks, let children be processed individually
                if element.find(["p", "table", "div", "ul", "ol"]):
                    continue

                cleaned_text = re.sub(r"\s+", " ", text_preview)
                # Filter out pure headers or short noise
                if len(cleaned_text) > 80 and not self.item_regex.fullmatch(cleaned_text):
                    chunks.append(
                        DocumentChunk(
                            chunk_type="prose",
                            content=cleaned_text,
                            section_context=current_section,
                        )
                    )

        return chunks
