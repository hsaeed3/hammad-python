import pytest
from hammad.data.types import (
    Data,
    DataSource,
    Document,
    Image,
    Audio,
)

from pathlib import Path
import tempfile
import os


class TestDataSource:
    """Test the DataSource class."""

    def test_default_values(self):
        """Test DataSource with default values."""
        source = DataSource()
        assert source.is_file is False
        assert source.is_dir is False
        assert source.is_url is False
        assert source.path is None
        assert source.url is None
        assert source.size is None
        assert source.encoding is None

    def test_file_source(self):
        """Test DataSource for file data."""
        path = Path("test.txt")
        source = DataSource(is_file=True, path=path, size=100, encoding="utf-8")
        assert source.is_file is True
        assert source.is_dir is False
        assert source.is_url is False
        assert source.path == path
        assert source.size == 100
        assert source.encoding == "utf-8"

    def test_url_source(self):
        """Test DataSource for URL data."""
        url = "https://example.com/file.txt"
        source = DataSource(is_url=True, url=url, size=200)
        assert source.is_file is False
        assert source.is_dir is False
        assert source.is_url is True
        assert source.url == url
        assert source.size == 200


class TestData:
    """Test the base Data class."""

    def test_from_path_file(self):
        """Test creating Data from a file path."""
        test_file = Path("tests/assets/example.txt")
        data = Data.from_path(test_file)
        
        assert data.source.is_file is True
        assert data.source.is_dir is False
        assert data.source.path == test_file
        assert data.name == "example.txt"
        assert data.extension == ".txt"
        assert data.type == "text/plain"
        assert data.exists is True

    def test_from_path_lazy_loading(self):
        """Test lazy loading with from_path."""
        test_file = Path("tests/assets/example.txt")
        data = Data.from_path(test_file, lazy=True)
        
        # Data should not be loaded yet
        assert data.data is None
        
        # Reading should load the data
        content = data.read()
        assert isinstance(content, bytes)
        assert b"Lorem ipsum" in content

    def test_from_path_with_encoding(self):
        """Test creating Data with specific encoding."""
        test_file = Path("tests/assets/example.txt")
        data = Data.from_path(test_file, encoding="utf-8", lazy=False)
        
        assert data.source.encoding == "utf-8"
        assert isinstance(data.data, str)
        assert "Lorem ipsum" in data.data

    def test_from_bytes(self):
        """Test creating Data from bytes."""
        test_bytes = b"Hello, world!"
        data = Data.from_bytes(test_bytes, name="test.txt")
        
        assert data.data == test_bytes
        assert data.source.is_file is True
        assert data.source.size == len(test_bytes)
        assert data.name == "test.txt"

    def test_from_bytes_with_png_signature(self):
        """Test creating Data from bytes with PNG signature."""
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"fake png data"
        data = Data.from_bytes(png_bytes)
        
        assert data.type == "image/png"
        assert data.data == png_bytes

    def test_name_property(self):
        """Test the name property."""
        # Test with file path
        test_file = Path("tests/assets/example.txt")
        data = Data.from_path(test_file)
        assert data.name == "example.txt"
        
        # Test with URL
        data_url = Data(source=DataSource(is_url=True, url="https://example.com/file.txt"))
        assert data_url.name == "file.txt"

    def test_extension_property(self):
        """Test the extension property."""
        test_file = Path("tests/assets/example.txt")
        data = Data.from_path(test_file)
        assert data.extension == ".txt"

    def test_exists_property(self):
        """Test the exists property."""
        # Existing file
        test_file = Path("tests/assets/example.txt")
        data = Data.from_path(test_file)
        assert data.exists is True
        
        # Non-existing file
        fake_file = Path("non_existent_file.txt")
        data_fake = Data.from_path(fake_file)
        assert data_fake.exists is False
        
        # Data with content
        data_with_content = Data(data="test content")
        assert data_with_content.exists is True

    def test_to_file(self):
        """Test saving data to file."""
        test_data = "Hello, world!"
        data = Data(data=test_data)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.txt"
            result_path = data.to_file(output_path)
            
            assert result_path == output_path
            assert output_path.exists()
            assert output_path.read_text() == test_data

    def test_to_file_overwrite_protection(self):
        """Test overwrite protection in to_file."""
        data = Data(data="test content")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.txt"
            output_path.write_text("existing content")
            
            # Should raise error without overwrite=True
            with pytest.raises(FileExistsError):
                data.to_file(output_path)
            
            # Should work with overwrite=True
            data.to_file(output_path, overwrite=True)
            assert output_path.read_text() == "test content"

    def test_repr(self):
        """Test string representation."""
        test_file = Path("tests/assets/example.txt")
        data = Data.from_path(test_file)
        repr_str = repr(data)
        
        assert "path=" in repr_str
        assert "example.txt" in repr_str
        assert "is_file=True" in repr_str

    def test_equality(self):
        """Test equality comparison."""
        data1 = Data(data="test")
        data2 = Data(data="test")
        data3 = Data(data="different")
        
        assert data1 == data2
        assert data1 != data3


class TestDocument:
    """Test the Document class."""

    def test_from_path(self):
        """Test creating Document from file path."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file, lazy=False)
        
        assert isinstance(doc, Document)
        assert doc.source.is_file is True
        assert "Lorem ipsum" in doc.content

    def test_content_property(self):
        """Test the content property."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file)
        
        content = doc.content
        assert isinstance(content, str)
        assert "Lorem ipsum" in content

    def test_lines_property(self):
        """Test the lines property."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file)
        
        lines = doc.lines
        assert isinstance(lines, list)
        assert len(lines) > 0
        assert "Lorem ipsum" in lines[0]

    def test_line_count(self):
        """Test line count property."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file)
        
        assert doc.line_count > 0
        assert doc.line_count == len(doc.lines)

    def test_word_count(self):
        """Test word count property."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file)
        
        assert doc.word_count > 0

    def test_char_count(self):
        """Test character count property."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file)
        
        assert doc.char_count > 0
        assert doc.char_count == len(doc.content)

    def test_is_markdown(self):
        """Test markdown detection."""
        # Test with .txt file
        txt_doc = Document(source=DataSource(path=Path("test.txt")))
        assert txt_doc.is_markdown is False
        
        # Test with .md file
        md_doc = Document(source=DataSource(path=Path("test.md")))
        assert md_doc.is_markdown is True

    def test_iter_lines(self):
        """Test line iteration."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file)
        
        lines = list(doc.iter_lines())
        assert len(lines) > 0
        
        # Test with strip
        stripped_lines = list(doc.iter_lines(strip=True))
        assert len(stripped_lines) == len(lines)

    def test_iter_paragraphs(self):
        """Test paragraph iteration."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file)
        
        paragraphs = list(doc.iter_paragraphs())
        assert len(paragraphs) > 0

    def test_search(self):
        """Test search functionality."""
        test_file = Path("tests/assets/example.txt")
        doc = Document.from_path(test_file)
        
        # Case insensitive search (default)
        results = doc.search("lorem")
        assert len(results) > 0
        assert isinstance(results[0], tuple)
        assert len(results[0]) == 2  # (line_number, line_content)
        
        # Case sensitive search
        results_sensitive = doc.search("lorem", case_sensitive=True)
        results_insensitive = doc.search("Lorem", case_sensitive=True)
        assert len(results_insensitive) > 0


class TestImage:
    """Test the Image class."""

    def test_from_path(self):
        """Test creating Image from file path."""
        test_file = Path("tests/assets/example.jpg")
        if test_file.exists():
            img = Image.from_path(test_file)
            
            assert isinstance(img, Image)
            assert img.source.is_file is True
            assert img.type == "image/jpeg"
            assert img.is_valid_image is True

    def test_format_property(self):
        """Test format property."""
        img = Image(type="image/png")
        assert img.format == "PNG"
        
        img_jpg = Image(type="image/jpeg")
        assert img_jpg.format == "JPEG"

    def test_is_valid_image(self):
        """Test image validation."""
        valid_img = Image(type="image/png")
        assert valid_img.is_valid_image is True
        
        invalid_img = Image(type="text/plain")
        assert invalid_img.is_valid_image is False


class TestAudio:
    """Test the Audio class."""

    def test_from_path(self):
        """Test creating Audio from file path."""
        test_file = Path("tests/assets/example.mp3")
        if test_file.exists():
            audio = Audio.from_path(test_file)
            
            assert isinstance(audio, Audio)
            assert audio.source.is_file is True
            assert audio.type in ["audio/mpeg", "audio/mp3"]
            assert audio.is_valid_audio is True

    def test_format_property(self):
        """Test format property."""
        audio = Audio(type="audio/mp3")
        assert audio.format == "MP3"
        
        audio_wav = Audio(type="audio/wav")
        assert audio_wav.format == "WAV"

    def test_is_valid_audio(self):
        """Test audio validation."""
        valid_audio = Audio(type="audio/mp3")
        assert valid_audio.is_valid_audio is True
        
        invalid_audio = Audio(type="text/plain")
        assert invalid_audio.is_valid_audio is False


class TestIntegration:
    """Integration tests for the data types."""

    def test_file_type_detection(self):
        """Test automatic file type detection."""
        # Test text file
        txt_file = Path("tests/assets/example.txt")
        data = Data.from_path(txt_file)
        assert data.type == "text/plain"
        
        # Test image file (if exists)
        jpg_file = Path("tests/assets/example.jpg")
        if jpg_file.exists():
            img_data = Data.from_path(jpg_file)
            assert img_data.type == "image/jpeg"
        
        # Test audio file (if exists)
        mp3_file = Path("tests/assets/example.mp3")
        if mp3_file.exists():
            audio_data = Data.from_path(mp3_file)
            assert audio_data.type in ["audio/mpeg", "audio/mp3"]

    def test_polymorphic_behavior(self):
        """Test that subclasses work as Data objects."""
        test_file = Path("tests/assets/example.txt")
        
        # Create as Document
        doc = Document.from_path(test_file)
        assert isinstance(doc, Data)
        assert isinstance(doc, Document)
        
        # Should have all Data methods
        assert doc.exists is True
        assert doc.name == "example.txt"
        
        # Should have Document-specific methods
        assert hasattr(doc, 'content')
        assert hasattr(doc, 'lines')
        assert hasattr(doc, 'word_count')

    def test_caching_behavior(self):
        """Test that properties are cached properly."""
        test_file = Path("tests/assets/example.txt")
        data = Data.from_path(test_file)
        
        # First access should cache the value
        name1 = data.name
        name2 = data.name
        assert name1 == name2
        assert data._name is not None  # Should be cached
        
        # Same for extension
        ext1 = data.extension
        ext2 = data.extension
        assert ext1 == ext2
        assert data._extension is not None  # Should be cached


if __name__ == "__main__":
    pytest.main(["-v", __file__])