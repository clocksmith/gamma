#!/usr/bin/env python3
"""
Session Viewer - View and analyze saved GAMMA game sessions

Usage:
  python tools/view_sessions.py                    # List all sessions
  python tools/view_sessions.py <session_id>       # View specific session
  python tools/view_sessions.py --stats           # Overall statistics
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.game.difficulty_levels import GameSession


def list_sessions():
    """List all available sessions."""
    sessions_dir = Path("sessions")
    if not sessions_dir.exists():
        print("No sessions directory found.")
        return

    sessions = list(sessions_dir.glob("session_*.json"))

    if not sessions:
        print("No sessions found.")
        return

    print("\n" + "="*80)
    print("Available Sessions")
    print("="*80 + "\n")

    for session_file in sorted(sessions, reverse=True):
        try:
            with open(session_file) as f:
                data = json.load(f)

            session_id = data['session_id']
            level = data.get('current_level', 'SIMPLE')
            rounds = data.get('total_rounds', 0)
            accuracy = data.get('overall_accuracy', 0) * 100

            # Parse timestamp from session_id
            timestamp_str = session_id.replace('session_', '').split('_')[0:2]
            if len(timestamp_str) >= 2:
                date_str = timestamp_str[0]
                time_str = timestamp_str[1]
                date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                time = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
                when = f"{date} {time}"
            else:
                when = "Unknown"

            print(f"  📁 {session_file.name}")
            print(f"     When: {when}")
            print(f"     Level: {level} | Rounds: {rounds} | Accuracy: {accuracy:.1f}%")
            print()

        except Exception as e:
            print(f"  ⚠️  {session_file.name} (corrupted: {e})")

def view_session(session_id):
    """View detailed information about a specific session."""
    session_file = Path(f"sessions/{session_id}.json")

    if not session_file.exists():
        # Try with .json extension if not provided
        if not session_id.endswith('.json'):
            session_file = Path(f"sessions/{session_id}")

    if not session_file.exists():
        print(f"Session not found: {session_id}")
        print("Run without arguments to list available sessions.")
        return

    try:
        session = GameSession.load_from_file(str(session_file))
    except Exception as e:
        print(f"Error loading session: {e}")
        return

    print("\n" + "="*80)
    print(f"Session: {session.session_id}")
    print("="*80 + "\n")

    stats = session.export_stats()

    print("Overview:")
    print(f"  Final Level: {stats['current_level']}")
    print(f"  Total Rounds: {stats['total_rounds']}")
    print(f"  Correct: {stats['total_correct']}")
    print(f"  Overall Accuracy: {stats['overall_accuracy']:.1%}")
    print(f"  Playtime: {stats['total_playtime_seconds']:.1f} seconds\n")

    print("Accuracy by Difficulty Level:")
    for level, accuracy in stats['accuracy_by_level'].items():
        if accuracy > 0:
            print(f"  {level}: {accuracy:.1%}")
    print()

    if session.achievements:
        print(f"🏆 Achievements ({len(session.achievements)}):")
        for achievement in session.achievements:
            desc = session.get_achievement_description(achievement)
            print(f"  {desc}")
        print()

    # Show round history (last 10)
    print("Recent Rounds (last 10):")
    print(f"  {'Round':<7} {'Result':<8} {'Prob':<8} {'Time':<8} {'Temp':<6}")
    print("  " + "-"*45)

    for round_stat in session.rounds[-10:]:
        result = "✓" if round_stat.correct else "✗"
        print(f"  {round_stat.round_number:<7} {result:<8} "
              f"{round_stat.probability_of_correct:<8.2f} "
              f"{round_stat.time_taken_seconds:<8.2f} "
              f"{round_stat.temperature:<6.2f}")

    print("\n" + "="*80 + "\n")


def show_overall_stats():
    """Show statistics across all sessions."""
    sessions_dir = Path("sessions")
    if not sessions_dir.exists():
        print("No sessions directory found.")
        return

    sessions = list(sessions_dir.glob("session_*.json"))

    if not sessions:
        print("No sessions found.")
        return

    total_rounds = 0
    total_correct = 0
    total_playtime = 0
    all_achievements = set()
    level_distribution = {}

    for session_file in sessions:
        try:
            with open(session_file) as f:
                data = json.load(f)

            total_rounds += data.get('total_rounds', 0)
            total_correct += data.get('total_correct', 0)
            total_playtime += data.get('total_playtime_seconds', 0)

            for achievement in data.get('achievements', []):
                all_achievements.add(achievement)

            level = data.get('current_level', 'SIMPLE')
            level_distribution[level] = level_distribution.get(level, 0) + 1

        except Exception:
            continue

    print("\n" + "="*80)
    print("Overall Statistics (All Sessions)")
    print("="*80 + "\n")

    print(f"Total Sessions: {len(sessions)}")
    print(f"Total Rounds Played: {total_rounds}")
    print(f"Total Correct: {total_correct}")
    print(f"Overall Accuracy: {(total_correct/total_rounds*100):.1f}%" if total_rounds > 0 else "N/A")
    print(f"Total Playtime: {total_playtime/60:.1f} minutes\n")

    print("Level Distribution:")
    for level, count in sorted(level_distribution.items()):
        print(f"  {level}: {count} sessions")
    print()

    print(f"Unique Achievements Unlocked: {len(all_achievements)}")
    print("\n" + "="*80 + "\n")


def main():
    if len(sys.argv) == 1:
        list_sessions()
    elif len(sys.argv) == 2:
        if sys.argv[1] in ['--stats', '-s']:
            show_overall_stats()
        elif sys.argv[1] in ['--help', '-h']:
            print(__doc__)
        else:
            view_session(sys.argv[1])
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
