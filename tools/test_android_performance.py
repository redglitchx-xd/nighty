#!/usr/bin/env python3
"""Test the real Android recorder/timers in a host harness, without player data."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    harness = ROOT / '.local/android/performance-tests'
    (harness / 'src').mkdir(parents=True, exist_ok=True)
    (harness / 'Cargo.toml').write_text('''[package]
name = "android-performance-tests"
version = "0.0.0"
edition = "2024"
[workspace]
[dependencies]
serde_json = "1"
log = "0.4"
rustix = { version = "1", features = ["time"] }
apex-threads = { path = "../../../crates/apex-threads" }
''', encoding='utf-8')
    (harness / 'src/lib.rs').write_text('''#![allow(dead_code)]
extern crate self as apex_client;
pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;
#[path = "../../../../crates/apex-client/src/control.rs"] pub mod control;
#[path = "../../../../crates/apex-client-render/src/spans.rs"] pub mod spans;
mod backend { pub const VERSION: &str = "0.7.2-test"; }
mod platform {
    pub fn open_documents(_: &str) -> bool { true }
}
#[path = "../../../../crates/apex-client/src/android/performance.rs"] mod performance;
#[path = "../../../../crates/apex-client/src/android/device_math.rs"] mod device_math;
''', encoding='utf-8')
    subprocess.run(['cargo', 'test', '--manifest-path', str(harness / 'Cargo.toml'),
                    '--', '--test-threads=1'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
