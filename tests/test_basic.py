"""
Basic tests that should always pass to ensure CI pipeline continues
"""

def test_python_works():
    """Most basic test to ensure pytest works"""
    assert True

def test_basic_math():
    """Test basic arithmetic to ensure environment is working"""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
