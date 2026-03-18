import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock Streamlit and other dependencies before importing app
st_mock = MagicMock()

def mock_cache_data(ttl=None, **kwargs):
    def decorator(func):
        return func
    return decorator

st_mock.cache_data.side_effect = mock_cache_data
st_mock.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
st_mock.sidebar.__enter__.return_value = MagicMock()

def mock_get(key, default=None):
    if key == "last_script_execution":
        return 0
    if key == "messages":
        return []
    return default

st_mock.session_state.get.side_effect = mock_get

sys.modules['streamlit'] = st_mock
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['litellm'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Now we can import the function to test
from app import get_gemini_models

def test_get_gemini_models_success():
    """Test get_gemini_models correctly filters and formats model names."""
    mock_model1 = MagicMock()
    mock_model1.name = "models/gemini-1.5-flash"
    mock_model1.supported_generation_methods = ["generateContent"]

    mock_model2 = MagicMock()
    mock_model2.name = "models/gemini-pro"
    mock_model2.supported_generation_methods = ["generateContent", "otherMethod"]

    mock_model3 = MagicMock()
    mock_model3.name = "models/other-model"
    mock_model3.supported_generation_methods = ["otherMethod"]

    with patch('app.genai.list_models', return_value=[mock_model1, mock_model2, mock_model3]):
        models = get_gemini_models()

    assert models == ["gemini/gemini-1.5-flash", "gemini/gemini-pro"]

def test_get_gemini_models_empty():
    """Test get_gemini_models returns an empty list when no models are returned."""
    with patch('app.genai.list_models', return_value=[]):
        models = get_gemini_models()

    assert models == []

def test_get_gemini_models_no_generate_content():
    """Test get_gemini_models filters out models without 'generateContent' method."""
    mock_model = MagicMock()
    mock_model.name = "models/gemini-1.5-flash"
    mock_model.supported_generation_methods = ["embedContent"]

    with patch('app.genai.list_models', return_value=[mock_model]):
        models = get_gemini_models()

    assert models == []
