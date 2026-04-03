import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from batch_channel import slugify


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_special_chars():
    assert slugify("AI Agents & MCPs: A Guide!") == "ai-agents-mcps-a-guide"


def test_slugify_multiple_spaces():
    assert slugify("Hello  World") == "hello-world"


def test_slugify_leading_trailing_hyphens():
    assert slugify("  hello world  ") == "hello-world"


def test_slugify_truncates_long_titles():
    long_title = "a" * 80
    assert len(slugify(long_title)) <= 60
