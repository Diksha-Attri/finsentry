import pytest
from app.ingestion.layout_parser import LayoutAwareParser


@pytest.fixture
def parser() -> LayoutAwareParser:
    return LayoutAwareParser()


def test_html_table_to_markdown(parser: LayoutAwareParser) -> None:
    html = """
    <div>
        <h3>Item 8. Financial Statements</h3>
        <table>
            <tr><th>Metric</th><th>2023</th><th>2024</th></tr>
            <tr><td>Total Revenue</td><td>$100,000</td><td>$145,000</td></tr>
            <tr><td>Net Income</td><td>$20,000</td><td>$32,000</td></tr>
        </table>
    </div>
    """
    chunks = parser.parse(html)
    table_chunks = [c for c in chunks if c.chunk_type == "table"]

    assert len(table_chunks) == 1
    assert "Item 8" in table_chunks[0].section_context
    assert "| Metric | 2023 | 2024 |" in table_chunks[0].content
    assert "| Total Revenue | $100,000 | $145,000 |" in table_chunks[0].content


def test_prose_chunking_with_context(parser: LayoutAwareParser) -> None:
    html = """
    <div>
        <h2>Item 1A. Risk Factors</h2>
        <p>Our operations are subject to severe macroeconomic fluctuations, specifically related to the availability of semiconductor fabrication components and rare-earth materials across the global supply chain.</p>
    </div>
    """
    chunks = parser.parse(html)
    prose_chunks = [c for c in chunks if c.chunk_type == "prose"]

    assert len(prose_chunks) == 1
    assert "Item 1A" in prose_chunks[0].section_context
    assert "semiconductor fabrication components" in prose_chunks[0].content
