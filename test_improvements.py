#!/usr/bin/env python3
"""
Test script for the improved Word Counter application.
This script tests the key improvements made to the application.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the current directory to the path so we can import the word counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_class():
    """Test the improved Config class."""
    print("Testing Config class...")
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_config = f.name
    
    try:
        # Import the Config class
        from wordcounter_06_28_25 import Config
        
        # Test config creation
        config = Config(temp_config)
        
        # Test default values
        assert config.get("daily_goal") == 1000
        assert config.get("auto_save_interval") == 300
        assert config.get("min_word_length") == 2
        
        # Test setting values
        config.set("daily_goal", 2000)
        assert config.get("daily_goal") == 2000
        
        # Test validation
        config.set("auto_save_interval", 10)  # Should be reset to default
        assert config.get("auto_save_interval") == 300
        
        print("✓ Config class tests passed")
        
    except Exception as e:
        print(f"✗ Config class test failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_config):
            os.unlink(temp_config)
    
    return True

def test_word_detector():
    """Test the improved WordDetector class."""
    print("Testing WordDetector class...")
    
    try:
        from wordcounter_06_28_25 import WordDetector
        from pynput.keyboard import Key, KeyCode
        
        detector = WordDetector(min_word_length=2)
        
        # Test word detection
        # Simulate typing "hello world"
        keys = [
            KeyCode.from_char('h'), KeyCode.from_char('e'), KeyCode.from_char('l'),
            KeyCode.from_char('l'), KeyCode.from_char('o'), Key.space,
            KeyCode.from_char('w'), KeyCode.from_char('o'), KeyCode.from_char('r'),
            KeyCode.from_char('l'), KeyCode.from_char('d'), Key.space
        ]
        
        word_count = 0
        for key in keys:
            count = detector.process_key(key)
            if count:
                word_count += count
        
        assert word_count == 2, f"Expected 2 words, got {word_count}"
        
        # Test reset
        detector.reset()
        assert detector.current_word == ""
        assert len(detector.word_count_cache) == 0
        
        print("✓ WordDetector class tests passed")
        
    except Exception as e:
        print(f"✗ WordDetector class test failed: {e}")
        return False
    
    return True

def test_statistics():
    """Test the improved Statistics class."""
    print("Testing Statistics class...")
    
    try:
        from wordcounter_06_28_25 import Statistics
        
        stats = Statistics(wpm_history_size=5)
        
        # Test session start
        stats.start_session()
        assert stats.get_session_duration() >= 0
        
        # Test adding words
        for _ in range(10):
            stats.add_word()
        
        session_data = stats.get_session_data()
        assert session_data.word_count == 10
        
        # Test WPM calculation
        wpm = stats.get_overall_wpm()
        assert wpm >= 0
        
        # Test productivity score
        score = stats.get_productivity_score()
        assert score >= 0
        
        # Test reset
        stats.reset()
        session_data = stats.get_session_data()
        assert session_data.word_count == 0
        
        print("✓ Statistics class tests passed")
        
    except Exception as e:
        print(f"✗ Statistics class test failed: {e}")
        return False
    
    return True

def test_data_manager():
    """Test the new DataManager class."""
    print("Testing DataManager class...")
    
    try:
        from wordcounter_06_28_25 import DataManager, SessionData
        from datetime import datetime
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_data_file = os.path.join(temp_dir, "test_data.xlsx")
        
        try:
            data_manager = DataManager(temp_data_file)
            
            # Test saving session
            session_data = SessionData(
                word_count=100,
                start_time=datetime.now(),
                duration=300,
                wpm=20.0
            )
            
            success = data_manager.save_session(session_data)
            assert success == True
            
            # Test loading today's data
            today_total = data_manager.load_today_data()
            assert today_total == 100
            
            # Test getting statistics
            stats = data_manager.get_statistics()
            assert stats['total_words'] == 100
            assert stats['total_sessions'] == 1
            
            # Test export
            export_file = data_manager.export_data('csv')
            assert export_file is not None
            assert os.path.exists(export_file)
            
            # Clean up export file
            os.unlink(export_file)
            
            print("✓ DataManager class tests passed")
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        print(f"✗ DataManager class test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Running tests for improved Word Counter application...\n")
    
    tests = [
        test_config_class,
        test_word_detector,
        test_statistics,
        test_data_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The improvements are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 