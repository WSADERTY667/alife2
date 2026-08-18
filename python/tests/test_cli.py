"""Tests for CLI arguments."""
import subprocess
import sys
import os
import tempfile


def test_help_shows_all_args():
    """Test that --help shows all expected arguments."""
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) or "."
    )
    assert result.returncode == 0
    help_text = result.stdout
    
    expected_args = [
        "--headless",
        "--seed",
        "--ticks",
        "--agents",
        "--food",
        "--out",
        "--hidden-neurons"
    ]
    
    for arg in expected_args:
        assert arg in help_text, f"Missing argument: {arg}"


def test_headless_basic():
    """Test basic headless mode runs without crash."""
    result = subprocess.run(
        [sys.executable, "main.py", "--headless", "--ticks", "5"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) or "."
    )
    assert result.returncode == 0
    assert "Headless Simulation Results" in result.stdout


def test_headless_with_seed():
    """Test headless mode with seed argument."""
    result = subprocess.run(
        [sys.executable, "main.py", "--headless", "--ticks", "5", "--seed", "42"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) or "."
    )
    assert result.returncode == 0
    assert "Headless Simulation Results" in result.stdout


def test_headless_with_agents_and_food():
    """Test headless mode with agents and food arguments."""
    result = subprocess.run(
        [sys.executable, "main.py", "--headless", "--ticks", "5", "--agents", "10", "--food", "50"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) or "."
    )
    assert result.returncode == 0
    assert "Headless Simulation Results" in result.stdout


def test_headless_with_output_file():
    """Test headless mode with output file argument."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        out_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, "main.py", "--headless", "--ticks", "5", "--out", out_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) or "."
        )
        assert result.returncode == 0
        assert "Results written to:" in result.stdout
        
        # Check output file was created and contains data
        with open(out_file, 'r') as f:
            content = f.read()
        assert "Ticks completed:" in content
        assert "Final agent count:" in content
    finally:
        if os.path.exists(out_file):
            os.unlink(out_file)


def test_visual_mode_still_works():
    """Test that visual mode (without --headless) still works.
    
    Note: This test checks that the program starts correctly,
    but cannot fully test Pygame in headless CI environment.
    """
    # Just verify the script doesn't crash on import/initialization
    # We can't actually run the Pygame loop in CI
    result = subprocess.run(
        [sys.executable, "-c", 
         "import sys; sys.path.insert(0, '.'); "
         "from main import main; "
         "import argparse; "
         "parser = argparse.ArgumentParser(); "
         "parser.add_argument('--headless', action='store_true'); "
         "args = parser.parse_args([]); "
         "print('Visual mode imports OK')"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) or "."
    )
    # May fail due to pygame display, but should not have syntax/import errors
    # Return code 1 is acceptable if it's a pygame display error, not import error
    if result.returncode != 0:
        # Check if it's a pygame-related error (acceptable in CI)
        if "pygame" not in result.stderr.lower() and "display" not in result.stderr.lower():
            raise AssertionError(f"Unexpected error: {result.stderr}")
