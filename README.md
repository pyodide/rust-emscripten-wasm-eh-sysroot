To build the rust stdlib for Emscripten with emscripten-wasm-eh:
```sh
./main.sh <emscripten-version> <rust-nightly-date>
```

e.g.:
```sh
./main.sh 3.1.74 2025-02-01
```

## Why?

There are two other options that would seem better:
1. `-Zbuild-std`
2. Build a custom sysroot with https://github.com/RalfJung/rustc-build-sysroot/
   or https://github.com/DianaNites/cargo-sysroot/.

`-Zbuild-std` doesn't work with `panic=abort` (rust-lang/cargo#7359) or with
`cargo freeze`. Building a custom sysroot with `rustc-build-sysroot` or
`cargo-sysroot` works with `cargo freeze` but has the same problem with
`panic=abort`. Thus, I think the only reasonable way to go is to build the
sysroot from the rust source directory.
