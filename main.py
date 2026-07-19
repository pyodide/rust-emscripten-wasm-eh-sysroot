import re
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

NIGHTLY_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


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

    if 'llvm_args: cvs![],' in base.read_text():
        apply_patch("turn-on-new-wasm-eh.patch")


def resolve_release(rust_version: str) -> tuple[str, str]:
    """Map a requested Rust version to a (channel, manifest_url).

    A ``YYYY-MM-DD`` argument selects that day's nightly, anything else is
    treated as a released stable version (e.g. ``1.85.0``).
    """
    if NIGHTLY_DATE.fullmatch(rust_version):
        channel = "nightly"
        url = (
            f"http://static.rust-lang.org/dist/{rust_version}"
            "/channel-rust-nightly.toml"
        )
    else:
        channel = "stable"
        url = f"http://static.rust-lang.org/dist/channel-rust-{rust_version}.toml"
    return channel, url


def set_channel(channel: str) -> None:
    """Point the copied ``config.toml`` at the channel we're building."""
    config = RUST / "config.toml"
    text = re.sub(
        r'channel = ".*"', f'channel = "{channel}"', config.read_text()
    )
    config.write_text(text)


def main(emcc_version, rust_version):
    channel, url = resolve_release(rust_version)
    print("> Requesting", url)
    with urllib.request.urlopen(url) as response:
        manifest = response.read().decode()

    rust = tomllib.loads(manifest)["pkg"]["rust"]
    commit_hash = rust["git_commit_hash"]

    if not RUST.exists():
        run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--no-checkout",
                "https://github.com/rust-lang/rust.git",
            ],
            cwd=ROOT,
        )
    # Nightly commits live on `master` while stable release commits live on the
    # `stable` branch, so fetch the exact commit rather than relying on any
    # single branch's history being present.
    run(["git", "fetch", "--depth", "1", "origin", commit_hash], cwd=RUST)
    run(["git", "reset", "--hard"], cwd=RUST)
    run(["git", "checkout", commit_hash], cwd=RUST)
    apply_patches()
    print("> cp config.toml rust")
    shutil.copy("config.toml", RUST)
    set_channel(channel)
    run(["./x.py", "build", "library", "--stage", "1"], cwd=RUST)

    shutil.make_archive(
        f"emcc-{emcc_version}_{channel}-{rust_version}",
        "bztar",
        root_dir=STAGE1_RUSTLIB,
        base_dir="wasm32-unknown-emscripten",
    )


if __name__ == "__main__":
    main(*sys.argv[-2:])
