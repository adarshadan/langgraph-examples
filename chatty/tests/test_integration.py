import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import backend

def test_generate_label_real_call():
    result = backend.generate_label('What is the capital of France?')
    assert isinstance(result, str)
    assert result != ''
    assert len(result.split()) <= 6  # prompt asks for 4-5 words

def test_generate_label_real_greeting():
    result = backend.generate_label('hey there')
    assert result == '' or len(result.split()) <= 6