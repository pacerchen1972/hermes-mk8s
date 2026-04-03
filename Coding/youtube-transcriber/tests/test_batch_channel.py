from batch_channel import slugify, format_video_filename


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
    result = slugify(long_title)
    assert len(result) <= 60
    assert not result.endswith("-")


def test_slugify_no_trailing_hyphen_after_truncation():
    # 59 'a' chars + "-extra" → truncation should not leave a trailing hyphen
    title = "a" * 59 + "-extra-words"
    result = slugify(title)
    assert not result.startswith("-")
    assert not result.endswith("-")
    assert len(result) <= 60


def test_format_video_filename_basic():
    result = format_video_filename("20240315", "Hello World")
    assert result == "YT-2024-03-15-hello-world.txt"


def test_format_video_filename_special_chars():
    result = format_video_filename("20231201", "AI Agents & MCPs: A Guide!")
    assert result == "YT-2023-12-01-ai-agents-mcps-a-guide.txt"
