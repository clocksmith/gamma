"""
Test Difficulty System

Tests the progressive difficulty levels, achievements, and session management.
"""

import sys
import os

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game.difficulty_levels import (
    DifficultyLevel,
    GameSession,
    RoundStats,
    DifficultyManager
)


def test_level_up():
    """Test that level-up triggers after 20 correct rounds with 75%+ accuracy."""
    session = GameSession("test_levelup")

    # Simulate 20 correct rounds with high accuracy
    for i in range(20):
        stats = RoundStats(
            round_number=i + 1,
            correct=True,
            probability_of_correct=0.8,
            time_taken_seconds=2.0,
            difficulty_level=session.current_level,
            temperature=0.7,
            top_k=8
        )
        session.add_round(stats)

    assert session.should_level_up() == True, "Should level up after 20 correct rounds"
    print("✓ Level up detection works")


def test_level_down():
    """Test that level-down triggers after 10 rounds with < 30% accuracy."""
    session = GameSession("test_leveldown", current_level=DifficultyLevel.EXPLORER)

    # Simulate 10 incorrect rounds
    for i in range(10):
        stats = RoundStats(
            round_number=i + 1,
            correct=False,
            probability_of_correct=0.2,
            time_taken_seconds=3.0,
            difficulty_level=session.current_level,
            temperature=0.9,
            top_k=20
        )
        session.add_round(stats)

    assert session.should_level_down() == True, "Should level down after struggling"
    print("✓ Level down detection works")


def test_achievements():
    """Test that achievements are correctly awarded."""
    session = GameSession("test_achievements")

    # Trigger first_10 achievement
    for i in range(10):
        stats = RoundStats(
            round_number=i + 1,
            correct=True,
            probability_of_correct=0.9,
            time_taken_seconds=1.0,
            difficulty_level=DifficultyLevel.SIMPLE,
            temperature=0.7,
            top_k=8
        )
        session.add_round(stats)

    assert "first_10" in session.achievements, "Should have first_10 achievement"
    print(f"✓ Achievements work (earned: {session.achievements})")


def test_perfect_5_streak():
    """Test the perfect 5-streak achievement."""
    session = GameSession("test_streak")

    # Simulate 5 correct rounds with very high probability
    for i in range(5):
        stats = RoundStats(
            round_number=i + 1,
            correct=True,
            probability_of_correct=0.95,
            time_taken_seconds=1.0,
            difficulty_level=DifficultyLevel.SIMPLE,
            temperature=0.7,
            top_k=8
        )
        session.add_round(stats)

    assert "perfect_5_streak" in session.achievements, "Should have perfect_5_streak achievement"
    print("✓ Perfect 5-streak achievement works")


def test_accuracy_calculation():
    """Test that accuracy is calculated correctly."""
    session = GameSession("test_accuracy")

    # Add 7 correct and 3 incorrect rounds
    for i in range(10):
        correct = i < 7  # First 7 are correct
        stats = RoundStats(
            round_number=i + 1,
            correct=correct,
            probability_of_correct=0.8 if correct else 0.3,
            time_taken_seconds=2.0,
            difficulty_level=DifficultyLevel.SIMPLE,
            temperature=0.7,
            top_k=8
        )
        session.add_round(stats)

    # Calculate overall accuracy from rounds
    total_correct = sum(1 for r in session.rounds if r.correct)
    overall_accuracy = total_correct / len(session.rounds)

    assert overall_accuracy == 0.7, f"Expected 0.7 accuracy, got {overall_accuracy}"

    # Test level-specific accuracy
    level_accuracy = session.get_accuracy_at_level(DifficultyLevel.SIMPLE)
    assert level_accuracy == 0.7, f"Expected 0.7 level accuracy, got {level_accuracy}"

    print(f"✓ Accuracy calculation works (70% = {overall_accuracy})")


def test_difficulty_manager():
    """Test the difficulty manager recommendations."""
    session = GameSession("test_manager")

    # Add rounds to trigger level-up
    for i in range(20):
        stats = RoundStats(
            round_number=i + 1,
            correct=True,
            probability_of_correct=0.8,
            time_taken_seconds=2.0,
            difficulty_level=DifficultyLevel.SIMPLE,
            temperature=0.7,
            top_k=8
        )
        session.add_round(stats)

    recommended = DifficultyManager.recommend_level(session)
    assert recommended == DifficultyLevel.LEARNER, f"Expected LEARNER, got {recommended}"
    print(f"✓ Difficulty manager recommends correct level: {recommended.get_display_name()}")


def test_personalized_tips():
    """Test that personalized tips are generated."""
    session = GameSession("test_tips")

    # Add some rounds with low probability
    for i in range(5):
        stats = RoundStats(
            round_number=i + 1,
            correct=False,
            probability_of_correct=0.3,
            time_taken_seconds=5.0,
            difficulty_level=DifficultyLevel.SIMPLE,
            temperature=0.9,
            top_k=20
        )
        session.add_round(stats)

    tip = session.get_personalized_tip()
    assert tip is not None, "Should provide a tip after struggling"
    print(f"✓ Personalized tip generated: {tip[:50]}...")


def test_session_save_load():
    """Test that sessions can be saved and loaded."""
    import os
    import json

    session = GameSession("test_save", current_level=DifficultyLevel.LEARNER)

    # Add some rounds
    for i in range(5):
        stats = RoundStats(
            round_number=i + 1,
            correct=True,
            probability_of_correct=0.8,
            time_taken_seconds=2.0,
            difficulty_level=session.current_level,
            temperature=0.7,
            top_k=8
        )
        session.add_round(stats)

    # Save session
    os.makedirs("sessions", exist_ok=True)
    filepath = "sessions/test_save.json"
    session.save_to_file(filepath)

    # Verify file exists and can be loaded
    assert os.path.exists(filepath), "Session file should exist"

    with open(filepath, 'r') as f:
        data = json.load(f)

    assert data["session_id"] == "test_save", "Session ID should match"
    assert data["total_rounds"] == 5, "Should have 5 rounds"
    assert data["current_level"] == "LEARNER", "Level should be LEARNER"

    # Clean up
    os.remove(filepath)
    print("✓ Session save/load works")


def test_achievement_descriptions():
    """Test that all achievements have descriptions."""
    session = GameSession("test_descriptions")

    # Force all achievements
    session.achievements = [
        "first_10",
        "correct_50",
        "perfect_5_streak",
        "temperature_expert",
        "explorer_unlocked"
    ]

    for achievement in session.achievements:
        desc = session.get_achievement_description(achievement)
        assert desc is not None, f"Achievement {achievement} should have a description"
        assert len(desc) > 0, f"Description for {achievement} should not be empty"

    print(f"✓ All {len(session.achievements)} achievements have descriptions")


def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("Testing GAMMA Difficulty System")
    print("=" * 80)
    print()

    tests = [
        ("Level Up Detection", test_level_up),
        ("Level Down Detection", test_level_down),
        ("Achievement System", test_achievements),
        ("Perfect 5-Streak", test_perfect_5_streak),
        ("Accuracy Calculation", test_accuracy_calculation),
        ("Difficulty Manager", test_difficulty_manager),
        ("Personalized Tips", test_personalized_tips),
        ("Session Save/Load", test_session_save_load),
        ("Achievement Descriptions", test_achievement_descriptions),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\nTest: {test_name}")
        print("-" * 40)
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    print()
    print("=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 80)

    if failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
