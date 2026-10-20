#!/usr/bin/env bash
# Build dependency only. End users do not run this or install MSYS2.
set -euo pipefail
pf_root="$(cd "$(dirname "$0")/.." && pwd)"
pf_work="$pf_root/build/icarus-work"
mkdir -p "$pf_work"
cd "$pf_root/vendor/sources"
printf '%s  %s\n' 'a68cb1ef7c017ef090ebedb2bc3e39ef90ecc70a3400afb4aa94303bc3beaa7d' 'iverilog-12.0.tar.gz' | sha256sum -c -
cd "$pf_work"
tar -xzf "$pf_root/vendor/sources/iverilog-12.0.tar.gz"
cd iverilog-12_0
sh autoconf.sh
# Deliberately disable optional readline/history: no interactive runtime required.
export ac_cv_lib_readline_readline=no
export ac_cv_lib_readline_add_history=no
export ac_cv_lib_history_add_history=no
export ac_cv_header_readline_readline_h=no
export ac_cv_header_readline_history_h=no
./configure --host=x86_64-w64-mingw32 --prefix=/PhoenixForge \
  CC=gcc CXX=g++ CFLAGS="-O2 -ffile-prefix-map=$pf_work=." \
  CXXFLAGS="-O2 -ffile-prefix-map=$pf_work=." LDFLAGS="-static-libgcc -static-libstdc++"
make -j2
make install DESTDIR="$pf_work/stage"
pacman -Q > "$pf_root/build/msys2-packages.txt"
cygpath -w "$pf_work/stage/PhoenixForge" > "$pf_root/build/icarus-prefix.txt"
cygpath -w /mingw64/bin > "$pf_root/build/mingw-bin.txt"
cygpath -w /mingw64/share/licenses > "$pf_root/build/mingw-licenses.txt"
printf 'Built Icarus under %s\n' "$pf_work/stage/PhoenixForge"
