import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('GROQ_API_KEY', 'dummy-key-for-ci')
os.environ.setdefault('GROQ_MODEL', 'llama-3.1-8b-instant')

from unittest.mock import patch, MagicMock
import backend

def test_generate_label_filters_no_label():
    with patch.object(backend.llm, 'invoke') as mock_invoke:
        mock_invoke.return_value = MagicMock(content='[_NO_LABEL_]')
        assert backend.generate_label('hi') == ''

def test_generate_label_returns_text():
    with patch.object(backend.llm, 'invoke') as mock_invoke:
        mock_invoke.return_value = MagicMock(content='Trip Planning Discussion')
        assert backend.generate_label('plan my Uttarakhand trip') == 'Trip Planning Discussion'

def test_workflow_compiles():
    assert backend.workflow is not None