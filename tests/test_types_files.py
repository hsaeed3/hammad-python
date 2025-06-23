import pytest
from hammad.types.files.file import File, FileSource
from hammad.types.files.configuration import Configuration
from hammad.types.files.document import Document
from hammad.types.files.image import Image
from hammad.types.files.audio import Audio

import json
from pathlib import Path
import tempfile
import os


class TestFileSource:
    """Test the FileSource class."""

    def test_default_values(self):
        """Test FileSource with default values."""
        source = FileSource()
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
        source = FileSource(is_file=True, path=path, size=100, encoding="utf-8")
        assert source.is_file is True
        assert source.is_dir is False
        assert source.is_url is False
        assert source.path == path
        assert source.size == 100
        assert source.encoding == "utf-8"

    def test_url_source(self):
        """Test DataSource for URL data."""
        url = "https://example.com/file.txt"
        source = FileSource(is_url=True, url=url, size=200)
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
        data = File.from_path(test_file)

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
        data = File.from_path(test_file, lazy=True)

        # Data should not be loaded yet
        assert data.data is None

        # Reading should load the data
        content = data.read()
        assert isinstance(content, bytes)
        assert b"Lorem ipsum" in content

    def test_from_path_with_encoding(self):
        """Test creating Data with specific encoding."""
        test_file = Path("tests/assets/example.txt")
        data = File.from_path(test_file, encoding="utf-8", lazy=False)

        assert data.source.encoding == "utf-8"
        assert isinstance(data.data, str)
        assert "Lorem ipsum" in data.data

    def test_from_bytes(self):
        """Test creating Data from bytes."""
        test_bytes = b"Hello, world!"
        data = File.from_bytes(test_bytes, name="test.txt")

        assert data.data == test_bytes
        assert data.source.is_file is True
        assert data.source.size == len(test_bytes)
        assert data.name == "test.txt"

    def test_from_bytes_with_png_signature(self):
        """Test creating Data from bytes with PNG signature."""
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"fake png data"
        data = File.from_bytes(png_bytes)

        assert data.type == "image/png"
        assert data.data == png_bytes

    def test_name_property(self):
        """Test the name property."""
        # Test with file path
        test_file = Path("tests/assets/example.txt")
        data = File.from_path(test_file)
        assert data.name == "example.txt"

        # Test with URL
        data_url = File(
            source=FileSource(is_url=True, url="https://example.com/file.txt")
        )
        assert data_url.name == "file.txt"

    def test_extension_property(self):
        """Test the extension property."""
        test_file = Path("tests/assets/example.txt")
        data = File.from_path(test_file)
        assert data.extension == ".txt"

    def test_exists_property(self):
        """Test the exists property."""
        # Existing file
        test_file = Path("tests/assets/example.txt")
        data = File.from_path(test_file)
        assert data.exists is True

        # Non-existing file
        fake_file = Path("non_existent_file.txt")
        data_fake = File.from_path(fake_file)
        assert data_fake.exists is False

        # Data with content
        data_with_content = File(data="test content")
        assert data_with_content.exists is True

    def test_to_file(self):
        """Test saving data to file."""
        test_data = "Hello, world!"
        data = File(data=test_data)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.txt"
            result_path = data.to_file(output_path)

            assert result_path == output_path
            assert output_path.exists()
            assert output_path.read_text() == test_data

    def test_to_file_overwrite_protection(self):
        """Test overwrite protection in to_file."""
        data = File(data="test content")

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
        data = File.from_path(test_file)
        repr_str = repr(data)

        assert "path=" in repr_str
        assert "example.txt" in repr_str
        assert "is_file=True" in repr_str

    def test_equality(self):
        """Test equality comparison."""
        data1 = File(data="test")
        data2 = File(data="test")
        data3 = File(data="different")

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
        txt_doc = Document(source=FileSource(path=Path("test.txt")))
        assert txt_doc.is_markdown is False

        # Test with .md file
        md_doc = Document(source=FileSource(path=Path("test.md")))
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
        data = File.from_path(txt_file)
        assert data.type == "text/plain"

        # Test image file (if exists)
        jpg_file = Path("tests/assets/example.jpg")
        if jpg_file.exists():
            img_data = File.from_path(jpg_file)
            assert img_data.type == "image/jpeg"

        # Test audio file (if exists)
        mp3_file = Path("tests/assets/example.mp3")
        if mp3_file.exists():
            audio_data = File.from_path(mp3_file)
            assert audio_data.type in ["audio/mpeg", "audio/mp3"]

    def test_polymorphic_behavior(self):
        """Test that subclasses work as Data objects."""
        test_file = Path("tests/assets/example.txt")

        # Create as Document
        doc = Document.from_path(test_file)
        assert isinstance(doc, File)
        assert isinstance(doc, Document)

        # Should have all Data methods
        assert doc.exists is True
        assert doc.name == "example.txt"

        # Should have Document-specific methods
        assert hasattr(doc, "content")
        assert hasattr(doc, "lines")
        assert hasattr(doc, "word_count")

    def test_caching_behavior(self):
        """Test that properties are cached properly."""
        test_file = Path("tests/assets/example.txt")
        data = File.from_path(test_file)

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



class TestConfiguration:
    """Test the Configuration class."""

    def test_default_initialization(self):
        """Test Configuration with default values."""
        config = Configuration()
        assert config.config_data == {}
        assert config.format_type is None

    def test_from_dict(self):
        """Test creating Configuration from dictionary data."""
        data = {"key1": "value1", "key2": 42, "nested": {"key": "value"}}
        config = Configuration(config_data=data, format_type="json")
        
        assert config.config_data == data
        assert config.format_type == "json"
        assert config.get("key1") == "value1"
        assert config.get("key2") == 42
        assert config.get("nested") == {"key": "value"}

    def test_json_parsing(self):
        """Test parsing JSON configuration data."""
        json_data = '{"name": "test", "count": 5, "enabled": true}'
        config = Configuration(data=json_data)
        config._parse_data()
        
        assert config.config_data["name"] == "test"
        assert config.config_data["count"] == 5
        assert config.config_data["enabled"] is True
        assert config.format_type == "json"

    def test_env_parsing(self):
        """Test parsing environment file format."""
        env_data = """
# This is a comment
DATABASE_URL=postgresql://localhost/mydb
DEBUG=true
PORT=5432
NAME="My App"
        """.strip()
        
        config = Configuration(data=env_data, format_type="env")
        config._parse_data()
        
        assert config.config_data["DATABASE_URL"] == "postgresql://localhost/mydb"
        assert config.config_data["DEBUG"] == "true"
        assert config.config_data["PORT"] == "5432"
        assert config.config_data["NAME"] == "My App"

    def test_from_file_json(self):
        """Test loading JSON configuration from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"app_name": "test_app", "version": "1.0"}, f)
            temp_path = f.name

        try:
            config = Configuration.from_file(temp_path)
            assert config.config_data["app_name"] == "test_app"
            assert config.config_data["version"] == "1.0"
            assert config.format_type == "json"
        finally:
            os.unlink(temp_path)

    def test_from_dotenv(self):
        """Test loading from .env file."""
        env_content = """
# Environment configuration
DATABASE_URL=sqlite:///test.db
SECRET_KEY=super-secret-key
DEBUG=true
        """.strip()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            temp_path = f.name

        try:
            config = Configuration.from_dotenv(temp_path)
            assert config.config_data["DATABASE_URL"] == "sqlite:///test.db"
            assert config.config_data["SECRET_KEY"] == "super-secret-key"
            assert config.config_data["DEBUG"] == "true"
            assert config.format_type == "env"
        finally:
            os.unlink(temp_path)

    def test_from_os_prefix(self):
        """Test creating configuration from environment variables with prefix."""
        # Set some test environment variables
        test_vars = {
            "MYAPP_DATABASE_URL": "postgresql://localhost/test",
            "MYAPP_DEBUG": "true",
            "MYAPP_PORT": "8080",
            "OTHER_VAR": "should_be_ignored"
        }
        
        # Save original environment
        original_env = {k: os.environ.get(k) for k in test_vars.keys()}
        
        try:
            # Set test variables
            for k, v in test_vars.items():
                os.environ[k] = v
            
            config = Configuration.from_os_prefix("MYAPP")
            
            assert config.config_data["database_url"] == "postgresql://localhost/test"
            assert config.config_data["debug"] == "true"
            assert config.config_data["port"] == "8080"
            assert "other_var" not in config.config_data
            assert config.format_type == "env"
            
        finally:
            # Restore original environment
            for k, v in original_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_from_os_vars(self):
        """Test creating configuration from specific environment variables."""
        test_vars = {
            "TEST_VAR1": "value1",
            "TEST_VAR2": "value2", 
            "TEST_VAR3": "value3"
        }
        
        # Save and set test variables
        original_env = {k: os.environ.get(k) for k in test_vars.keys()}
        
        try:
            for k, v in test_vars.items():
                os.environ[k] = v
            
            config = Configuration.from_os_vars(["TEST_VAR1", "TEST_VAR2", "NONEXISTENT"])
            
            assert config.config_data["TEST_VAR1"] == "value1"
            assert config.config_data["TEST_VAR2"] == "value2"
            assert "TEST_VAR3" not in config.config_data
            assert "NONEXISTENT" not in config.config_data
            
        finally:
            # Restore environment
            for k, v in original_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_to_file_json(self):
        """Test saving configuration to JSON file."""
        config = Configuration(
            config_data={"name": "test", "value": 42},
            format_type="json"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "config.json"
            config.to_file(output_path)
            
            assert output_path.exists()
            
            # Verify content
            with open(output_path) as f:
                loaded_data = json.load(f)
            assert loaded_data["name"] == "test"
            assert loaded_data["value"] == 42

    def test_to_file_env(self):
        """Test saving configuration to .env file."""
        config = Configuration(
            config_data={"DATABASE_URL": "sqlite:///test.db", "DEBUG": "true"},
            format_type="env"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "config.env"
            config.to_file(output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            assert "DATABASE_URL=sqlite:///test.db" in content
            assert "DEBUG=true" in content

    def test_update_file(self):
        """Test updating an existing configuration file."""
        # Create initial config file
        initial_data = {"name": "original", "version": "1.0", "debug": False}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(initial_data, f)
            temp_path = f.name

        try:
            # Create config with updates
            update_config = Configuration(
                config_data={"name": "updated", "new_key": "new_value"}
            )
            
            # Update the file
            update_config.update_file(temp_path)
            
            # Verify the update
            updated_config = Configuration.from_file(temp_path)
            assert updated_config.config_data["name"] == "updated"  # Updated
            assert updated_config.config_data["version"] == "1.0"   # Preserved
            assert updated_config.config_data["debug"] is False     # Preserved
            assert updated_config.config_data["new_key"] == "new_value"  # Added
            
        finally:
            os.unlink(temp_path)

    def test_to_os(self):
        """Test pushing configuration to environment variables."""
        config = Configuration(
            config_data={"database_url": "test://localhost", "port": "5432"}
        )
        
        # Save original environment
        original_env = {
            "TEST_DATABASE_URL": os.environ.get("TEST_DATABASE_URL"),
            "TEST_PORT": os.environ.get("TEST_PORT")
        }
        
        try:
            config.to_os(prefix="TEST")
            
            assert os.environ["TEST_DATABASE_URL"] == "test://localhost"
            assert os.environ["TEST_PORT"] == "5432"
            
        finally:
            # Restore environment
            for k, v in original_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_dict_like_access(self):
        """Test dictionary-like access methods."""
        config = Configuration(
            config_data={"key1": "value1", "key2": "value2"}
        )
        
        # Test __getitem__ and __setitem__
        assert config["key1"] == "value1"
        config["key3"] = "value3"
        assert config["key3"] == "value3"
        
        # Test __contains__
        assert "key1" in config
        assert "key3" in config
        assert "nonexistent" not in config
        
        # Test get method
        assert config.get("key1") == "value1"
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"
        
        # Test keys, values, items
        keys = list(config.keys())
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
        
        values = list(config.values())
        assert "value1" in values
        assert "value2" in values
        assert "value3" in values
        
        items = list(config.items())
        assert ("key1", "value1") in items

    def test_serialization_formats(self):
        """Test serialization to different formats."""
        config_data = {"name": "test", "count": 42, "enabled": True}
        config = Configuration(config_data=config_data)
        
        # Test JSON serialization
        json_output = config._serialize_data("json")
        parsed_json = json.loads(json_output)
        assert parsed_json == config_data
        
        # Test ENV serialization
        env_output = config._serialize_data("env")
        assert "name=test" in env_output
        assert "count=42" in env_output
        assert "enabled=True" in env_output

    def test_format_detection(self):
        """Test automatic format detection."""
        # Test with different extensions
        config = Configuration()
        config.source = FileSource(path=Path("test.json"))
        assert config._detect_format() == "json"
        
        config.source = FileSource(path=Path("test.yaml"))
        assert config._detect_format() == "yaml"
        
        config.source = FileSource(path=Path("test.env"))
        assert config._detect_format() == "env"
        
        # Test with MIME type
        config = Configuration(type="application/json")
        config.source = FileSource()
        assert config._detect_format() == "json"

    def test_error_handling(self):
        """Test error handling for invalid data."""
        # Test invalid JSON
        with pytest.raises(ValueError, match="Failed to parse configuration data"):
            config = Configuration(data="{ invalid json", format_type="json")
            config._parse_data()
        
        # Test file not found for dotenv
        with pytest.raises(FileNotFoundError):
            Configuration.from_dotenv("nonexistent.env")
        
        # Test file not found for update
        config = Configuration(config_data={"test": "value"})
        with pytest.raises(FileNotFoundError):
            config.update_file("nonexistent.json")
        
        # Test overwrite protection
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(b'{"existing": "data"}')
            temp_path = f.name

        try:
            config = Configuration(config_data={"new": "data"})
            with pytest.raises(FileExistsError):
                config.to_file(temp_path, overwrite=False)
        finally:
            os.unlink(temp_path)




if __name__ == "__main__":
    pytest.main(["-v", __file__])
