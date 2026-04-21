"""Generate realistic demo writing data so the analytics dashboard has
something to render. Uses an isolated temp data dir via the
``WORDCOUNTER_DATA_DIR`` env var; your real ``WordCountData.xlsx`` and
``config.json`` are never touched.

Usage:

    python demo_data.py                 # generate 90 days + launch app
    python demo_data.py --days 180      # more history
    python demo_data.py --seed 7        # reproducible
    python demo_data.py --no-launch     # just write files, print path
    python demo_data.py --dir /tmp/wc   # write to a specific dir (will be
                                        # wiped + recreated)

The data follows a plausible pattern: ~70% of days are writing days,
weekends are lighter, WPM hovers around 35 with noise and occasional
flow sessions, and there are 0-2 multi-week dry spells so streaks are
non-trivial. One app from the platform allowlist is picked per day so
the 'writing apps' breakdown has something to show.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, time
from pathlib import Path

import pandas as pd


# Excel schema expected by DataManager (kept in sync with wordcounter.py).
COLUMNS = [
    'Session ID',
    'Date and Time',
    'Word Count',
    'Duration (seconds)',
    'WPM',
    'Productivity Score',
]


def _pick_session_slots(rng: random.Random) -> list[tuple[int, int, int]]:
    """Return a list of (hour, minute, duration_min) slots for one day.

    Most days are a single morning or evening session. ~25% of writing days
    get a second session. ~5% get three (heroic day).
    """
    roll = rng.random()
    base = [_morning_or_evening(rng)]
    if roll < 0.05:
        base.append(_morning_or_evening(rng, prefer='evening'))
        base.append(_morning_or_evening(rng, prefer='afternoon'))
    elif roll < 0.30:
        base.append(_morning_or_evening(rng, prefer='evening' if base[0][0] < 12 else 'morning'))
    return base


def _morning_or_evening(rng: random.Random, prefer: str | None = None) -> tuple[int, int, int]:
    """Pick a session (start_hour, start_minute, duration_min)."""
    if prefer is None:
        bucket = rng.choices(
            ['morning', 'afternoon', 'evening'],
            weights=[5, 2, 3],
        )[0]
    else:
        bucket = prefer

    if bucket == 'morning':
        hour = rng.randint(6, 10)
    elif bucket == 'afternoon':
        hour = rng.randint(12, 16)
    else:
        hour = rng.randint(19, 23)

    minute = rng.randint(0, 59)
    duration = rng.choices(
        [15, 25, 40, 60, 90, 120],
        weights=[2, 4, 5, 4, 2, 1],
    )[0]
    return hour, minute, duration


def _pick_wpm(rng: random.Random, is_flow_day: bool) -> float:
    """Pick a plausible WPM. Baseline ~33 with noise; flow days push higher."""
    base = rng.gauss(33, 6)
    if is_flow_day:
        base += rng.uniform(10, 20)
    return max(8.0, min(80.0, base))


def _generate_sessions(days: int, seed: int) -> list[dict]:
    """Build a list of session dicts matching DataManager's Excel schema."""
    rng = random.Random(seed)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_day = today - timedelta(days=days - 1)

    # Pick ~2 dry spells of 3-7 days so the streak graph has something to
    # recover from.
    dry_spells: set[int] = set()
    for _ in range(rng.randint(1, 2)):
        spell_start = rng.randint(0, days - 8)
        spell_len = rng.randint(3, 7)
        dry_spells.update(range(spell_start, spell_start + spell_len))

    rows: list[dict] = []
    for day_idx in range(days):
        day = start_day + timedelta(days=day_idx)
        weekend = day.weekday() >= 5

        if day_idx in dry_spells:
            continue

        # Writing probability
        p_write = 0.55 if weekend else 0.85
        if rng.random() > p_write:
            continue

        is_flow_day = rng.random() < 0.15
        for hour, minute, duration_min in _pick_session_slots(rng):
            wpm = _pick_wpm(rng, is_flow_day)
            duration_sec = int(duration_min * 60)
            word_count = int(wpm * duration_min * rng.uniform(0.85, 1.05))
            start_ts = day + timedelta(hours=hour, minutes=minute)
            if start_ts > datetime.now():
                continue
            effective_wpm = round(word_count * 60 / max(duration_sec, 1), 2)
            rows.append({
                'Session ID': uuid.uuid4().hex[:16],
                'Date and Time': start_ts,
                'Word Count': word_count,
                'Duration (seconds)': duration_sec,
                'WPM': effective_wpm,
                'Productivity Score': effective_wpm,
            })

    rows.sort(key=lambda r: r['Date and Time'])
    return rows


def _write_demo_data(target_dir: Path, rows: list[dict]) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=COLUMNS)
    xlsx_path = target_dir / 'WordCountData.xlsx'
    df.to_excel(xlsx_path, index=False)
    return xlsx_path


def _write_demo_config(target_dir: Path) -> Path:
    """Write a config that skips the first-run wizard so the dashboard is
    reachable in one click."""
    if sys.platform == 'darwin':
        allowed = ['obsidian', 'microsoft word', 'scrivener', 'ia writer',
                   'typora', 'bear', 'ulysses']
    else:
        allowed = ['obsidian.exe', 'winword.exe', 'scrivener.exe',
                   'typora.exe', 'notepad++.exe']
    config = {
        'auto_save_interval': 300,
        'data_flush_interval': 60,
        'daily_goal': 1200,
        'theme': 'vista',
        'theme_mode': 'light',
        'window_geometry': '900x640',
        'max_backup_files': 5,
        'backup_enabled': True,
        'min_word_length': 1,
        'allowed_apps': allowed,
        'onboarding_completed': True,
        'launch_on_startup': False,
    }
    config_path = target_dir / 'config.json'
    config_path.write_text(json.dumps(config, indent=4), encoding='utf-8')
    return config_path


def _print_summary(rows: list[dict], target_dir: Path) -> None:
    df = pd.DataFrame(rows, columns=COLUMNS)
    total_words = int(df['Word Count'].sum())
    total_sessions = len(df)
    days_written = df['Date and Time'].dt.date.nunique()
    best_day = (
        df.groupby(df['Date and Time'].dt.date)['Word Count'].sum().idxmax()
        if total_sessions else None
    )
    best_day_words = (
        int(df.groupby(df['Date and Time'].dt.date)['Word Count'].sum().max())
        if total_sessions else 0
    )
    avg_wpm = float(df['WPM'].mean()) if total_sessions else 0.0

    print()
    print("=" * 60)
    print(f"Demo data written to: {target_dir}")
    print("=" * 60)
    print(f"  Sessions generated:   {total_sessions}")
    print(f"  Days with writing:    {days_written}")
    print(f"  Total words:          {total_words:,}")
    print(f"  Best day:             {best_day} ({best_day_words:,} words)")
    print(f"  Average WPM:          {avg_wpm:.1f}")
    print("=" * 60)


def _launch_app(data_dir: Path) -> None:
    """Launch wordcounter.py with WORDCOUNTER_DATA_DIR set to the demo dir."""
    script = Path(__file__).resolve().parent / 'wordcounter.py'
    if not script.exists():
        print(f"ERROR: cannot find wordcounter.py next to {__file__}")
        sys.exit(1)
    env = os.environ.copy()
    env['WORDCOUNTER_DATA_DIR'] = str(data_dir)
    print(f"Launching: {sys.executable} {script}")
    print(f"  WORDCOUNTER_DATA_DIR={data_dir}")
    print("  (close the app window to return to this shell)")
    print()
    subprocess.call([sys.executable, str(script)], env=env)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed a temp data dir with realistic writing history "
                    "and launch Word Counter Pro against it."
    )
    parser.add_argument('--days', type=int, default=90,
                        help='Days of history to generate (default: 90)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducible data')
    parser.add_argument('--dir', type=Path, default=None,
                        help='Target data dir (will be wiped and recreated). '
                             'Default: a fresh temp dir.')
    parser.add_argument('--no-launch', action='store_true',
                        help='Just generate files; do not launch the app')
    args = parser.parse_args()

    if args.seed is None:
        args.seed = random.randint(0, 10_000)

    if args.dir is None:
        target = Path(tempfile.mkdtemp(prefix='wordcounter-demo-'))
    else:
        target = args.dir.expanduser().resolve()
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)

    print(f"[demo_data] seed={args.seed} days={args.days} dir={target}")
    rows = _generate_sessions(args.days, args.seed)
    _write_demo_data(target, rows)
    _write_demo_config(target)
    _print_summary(rows, target)

    if args.no_launch:
        print()
        print("To launch the app against this dataset, run:")
        print(f"  WORDCOUNTER_DATA_DIR='{target}' python wordcounter.py")
    else:
        _launch_app(target)


if __name__ == '__main__':
    main()
