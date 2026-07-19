import urllib.request
import tomllib
from pathlib import Path
from typing import Any
import sys
import subprocess
import shutil

ROOT = Path(__file__).parent
RUST = ROOT / "rust"
STAGE1_RUSTLIB = RUST / "build/host/stage1/lib/rustlib/"


def run(
    args: list[str | Path], check: bool = True, **kwargs: Any
) -> subprocess.CompletedProcess[Any]:
    print(">", " ".join(str(x) for x in args))
    result = subprocess.run(args, check=False, text=True, **kwargs)
    if check and result.returncode:
        sys.exit(result.returncode)
    return result


def apply_patch(name: str) -> None:
    run(["patch", "-p1", "-i", ROOT / name], cwd=RUST)


def apply_patches() -> None:
    # The wasm base target must force the new (non-legacy) exception-handling
    # instructions via `-wasm-use-legacy-eh=false`.
    base = RUST / "compiler/rustc_target/src/spec/base/wasm.rs"
    if "-wasm-use-legacy-eh=false" not in base.read_text():
        apply_patch("turn-on-new-wasm-eh-base.patch")

    apply_patch("turn-on-new-wasm-eh.patch")


def main(emcc_version, date):
    print(
        "> Requesting",
        f"http://static.rust-lang.org/dist/{date}/channel-rust-nightly.toml",
    )
    with urllib.request.urlopen(
        f"http://static.rust-lang.org/dist/{date}/channel-rust-nightly.toml"
    ) as response:
        manifest = response.read().decode()

    rust = tomllib.loads(manifest)["pkg"]["rust"]
    commit_hash = rust["git_commit_hash"]

    if not RUST.exists():
        run(
            [
                "git",
                "clone",
                "https://github.com/rust-lang/rust.git",
                "--shallow-since=2025-01-01",
            ],
            cwd=ROOT,
        )
    run(["git", "reset", "--hard"], cwd=RUST)
    run(["git", "checkout", commit_hash], cwd=RUST)
    apply_patches()
    print("> cp config.toml rust")
    shutil.copy("config.toml", RUST)
    run(["./x.py", "build", "library", "--stage", "1"], cwd=RUST)

    shutil.make_archive(
        f"emcc-{emcc_version}_nightly-{date}",
        "bztar",
        root_dir=STAGE1_RUSTLIB,
        base_dir="wasm32-unknown-emscripten",
    )


if __name__ == "__main__":
    main(*sys.argv[-2:])
