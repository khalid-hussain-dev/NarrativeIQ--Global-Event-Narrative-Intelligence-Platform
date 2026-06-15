import sys
from pathlib import Path
# Add backend to path so we can import app.main
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import parse_import_rows, tokenize, text_score

def test_parse_import_rows_json_array():
    content = '[{"title": "Test 1", "source": "src1"}, {"title": "Test 2", "source": "src2"}]'
    rows = parse_import_rows(content)
    assert len(rows) == 2
    assert rows[0]["title"] == "Test 1"
    assert rows[1]["source"] == "src2"

def test_parse_import_rows_json_object():
    content = '{"rows": [{"title": "Test 1"}, {"title": "Test 2"}]}'
    rows = parse_import_rows(content)
    assert len(rows) == 2
    assert rows[0]["title"] == "Test 1"

def test_parse_import_rows_csv_lines():
    content = "Title One, Source One, http://url1.com\nTitle Two, Source Two"
    rows = parse_import_rows(content)
    assert len(rows) == 2
    assert rows[0]["title"] == "Title One"
    assert rows[0]["source"] == "Source One"
    assert rows[0]["url"] == "http://url1.com"
    assert rows[1]["title"] == "Title Two"
    assert rows[1]["source"] == "Source Two"

def test_parse_import_rows_empty():
    assert parse_import_rows("") == []
    assert parse_import_rows("   \n   ") == []

def test_tokenize():
    tokens = tokenize("Artificial Intelligence AI and the Machine Learning")
    assert "artificial" in tokens
    assert "intelligence" in tokens
    assert "ai" in tokens
    assert "machine" in tokens
    assert "learning" in tokens
    # Stopwords should not be present
    assert "and" not in tokens
    assert "the" not in tokens

def test_tokenize_empty():
    assert tokenize("") == set()
    assert tokenize("   ") == set()

def test_text_score():
    query = tokenize("AI machine")
    score = text_score(query, ["AI regulation", "machine learning"])
    assert score >= 0

def test_text_score_empty():
    assert text_score(set(), ["anything"]) == 0
    assert text_score(tokenize("ai"), []) == 0
