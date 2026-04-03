import json
from unittest.mock import patch, MagicMock

from batch_channel import (
    slugify,
    format_video_filename,
    get_next_prj_number,
    find_or_create_project_note,
    append_to_index,
    fetch_channel_videos,
    process_video,
)


def test_get_next_prj_number_empty_dir(tmp_path):
    assert get_next_prj_number(tmp_path) == 1


def test_get_next_prj_number_with_existing(tmp_path):
    (tmp_path / "PRJ-PERSONAL-003-foo.md").touch()
    (tmp_path / "PRJ-PERSONAL-007-bar.md").touch()
    assert get_next_prj_number(tmp_path) == 8


def test_get_next_prj_number_ignores_non_matching(tmp_path):
    (tmp_path / "some-other-file.md").touch()
    (tmp_path / "PRJ-PERSONAL-002-task.md").touch()
    assert get_next_prj_number(tmp_path) == 3


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


def test_creates_project_note_when_missing(tmp_path):
    note_path = find_or_create_project_note(tmp_path)
    assert note_path.exists()
    content = note_path.read_text()
    assert "vongoval Research" in content
    assert "## Videos" in content
    assert "PRJ-PERSONAL-001" in note_path.name


def test_finds_existing_project_note(tmp_path):
    projects_dir = tmp_path / "200 - Projects" / "Personal"
    projects_dir.mkdir(parents=True)
    existing = projects_dir / "PRJ-PERSONAL-004-vongoval-research.md"
    existing.write_text("# existing note", encoding="utf-8")

    note_path = find_or_create_project_note(tmp_path)
    assert note_path == existing


def test_creates_vongoval_subfolder(tmp_path):
    find_or_create_project_note(tmp_path)
    assert (tmp_path / "200 - Projects" / "Personal" / "vongoval").is_dir()


def test_append_to_index_adds_link(tmp_path):
    note = tmp_path / "index.md"
    note.write_text("# Test\n\n## Videos\n\n", encoding="utf-8")
    append_to_index(note, "My Video", "YT-2024-03-15-my-video.txt", "2024-03-15")
    content = note.read_text()
    assert "- [My Video](vongoval/YT-2024-03-15-my-video.txt) — 2024-03-15" in content


def test_append_to_index_skips_duplicate(tmp_path):
    note = tmp_path / "index.md"
    note.write_text(
        "# Test\n\n## Videos\n\n- [My Video](vongoval/YT-2024-03-15-my-video.txt) — 2024-03-15\n",
        encoding="utf-8",
    )
    append_to_index(note, "My Video", "YT-2024-03-15-my-video.txt", "2024-03-15")
    content = note.read_text()
    assert content.count("My Video") == 1


def test_append_to_index_multiple_entries(tmp_path):
    note = tmp_path / "index.md"
    note.write_text("# Test\n\n## Videos\n\n", encoding="utf-8")
    append_to_index(note, "Video One", "YT-2024-01-01-video-one.txt", "2024-01-01")
    append_to_index(note, "Video Two", "YT-2024-02-01-video-two.txt", "2024-02-01")
    content = note.read_text()
    assert "Video One" in content
    assert "Video Two" in content


def test_fetch_channel_videos_parses_output():
    mock_video = {
        "id": "abc123",
        "title": "Test Video",
        "upload_date": "20240315",
        "duration": 120,
        "webpage_url": "https://www.youtube.com/watch?v=abc123",
    }
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps(mock_video) + "\n"

    with patch("subprocess.run", return_value=mock_result):
        videos = fetch_channel_videos("https://youtube.com/@test/videos")

    assert len(videos) == 1
    assert videos[0]["title"] == "Test Video"
    assert videos[0]["upload_date"] == "20240315"


def test_fetch_channel_videos_handles_multiple():
    videos_data = [
        {"id": "v1", "title": "First", "upload_date": "20240101", "duration": 60, "webpage_url": "https://youtube.com/watch?v=v1"},
        {"id": "v2", "title": "Second", "upload_date": "20240201", "duration": 90, "webpage_url": "https://youtube.com/watch?v=v2"},
    ]
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "\n".join(json.dumps(v) for v in videos_data) + "\n"

    with patch("subprocess.run", return_value=mock_result):
        result = fetch_channel_videos("https://youtube.com/@test/videos")

    assert len(result) == 2
    assert result[1]["title"] == "Second"


def test_process_video_skips_existing(tmp_path):
    output_dir = tmp_path / "vongoval"
    output_dir.mkdir()
    note_path = tmp_path / "index.md"
    note_path.write_text("# Test\n\n## Videos\n\n", encoding="utf-8")

    video = {
        "title": "Test Video",
        "upload_date": "20240315",
        "webpage_url": "https://youtube.com/watch?v=abc",
        "duration": 120,
    }
    existing_file = output_dir / "YT-2024-03-15-test-video.txt"
    existing_file.write_text("already transcribed", encoding="utf-8")

    result = process_video(video, output_dir, note_path, "medium", True)
    assert result is False  # skipped


def test_process_video_writes_transcript(tmp_path):
    output_dir = tmp_path / "vongoval"
    output_dir.mkdir()
    note_path = tmp_path / "index.md"
    note_path.write_text("# Test\n\n## Videos\n\n", encoding="utf-8")

    video = {
        "title": "Test Video",
        "upload_date": "20240315",
        "webpage_url": "https://youtube.com/watch?v=abc",
        "duration": 120,
    }

    with patch("batch_channel.download_audio"), \
         patch("batch_channel.transcribe_audio", return_value="Hello world"):
        result = process_video(video, output_dir, note_path, "medium", True)

    assert result is True
    txt_file = output_dir / "YT-2024-03-15-test-video.txt"
    assert txt_file.exists()
    assert txt_file.read_text() == "Hello world"

    index_content = note_path.read_text()
    assert "Test Video" in index_content
