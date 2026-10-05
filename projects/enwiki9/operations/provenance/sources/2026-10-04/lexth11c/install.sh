#!/bin/bash
# install.sh -- HPJA dependency phase for the lexth11c (cmix-lex transformer) entry.
#
# Contract (HutterPrizeJudgingAssistant ENTRANT_INSTRUCTIONS.md section 4): this is the
# only entrant-controlled root + network phase. It is COPYed alone into a `docker build`
# context (the orchestrator writes `.dockerignore` = "*\n!install.sh"), so no source tree
# is visible here and nothing of the entry may be built here. It starts from the
# QUALIFICATION_OS userspace (ubuntu:22.04 = jammy, digest-pinned by the harness; noble also works, see REPORT.md) and must be
# noninteractive and repeatable. The judging base image runs it as root, so plain
# apt-get (no sudo) is correct here.
#
# What build.sh needs (see ../makefile and ../build_and_construct_comp.sh):
#   clang++-17, lld-17 (-fuse-ld=lld), llvm-profdata-17 (PGO merge), llvm-strip-17,
#   GNU make, binutils (objdump/objcopy: portability gates + section stripping),
#   python3 (the AVX-512 confinement gate in build_and_construct_comp.sh),
#   coreutils/mawk (md5sum, wc, awk), and UPX 5.1.1 (exact version, checked by the build).
# The compressor is dynamically linked against libc, libm, libstdc++ and libgcc_s only;
# all of those are loader-visible in /lib and /usr/lib after this phase, which is what the
# harness copies into its sanitized runtime image.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
# The judging base image replaces /tmp with a symlink into /work, which the dependency
# Dockerfile tears down again; anchor temporary files somewhere that exists throughout.
export TMPDIR=/var/tmp
mkdir -p "$TMPDIR"

. /etc/os-release
case "${ID:-}-${VERSION_CODENAME:-}" in
  ubuntu-noble|ubuntu-jammy) CODENAME="$VERSION_CODENAME" ;;   # QUALIFICATION_OS ubuntu-24.04 / ubuntu-22.04
  *) echo "install.sh: expected Ubuntu 24.04 (noble) or 22.04 (jammy), got ${PRETTY_NAME:-unknown}" >&2; exit 1 ;;
esac

apt-get update -o Acquire::Retries=3
apt-get install --yes --no-install-recommends -o Acquire::Retries=3 \
  ca-certificates curl xz-utils make binutils python3 coreutils mawk

# LLVM 17 from apt.llvm.org (the same repository/commit the reference build used):
# clang-17 1:17.0.6~++20240501091250+6009708b4367 for noble and jammy at the time of writing.
# This is what https://apt.llvm.org/llvm.sh does for "17", without its lsb-release /
# software-properties-common / gnupg detour (apt >= 2.4 accepts an armored signed-by key).
install -d -m 0755 /etc/apt/keyrings
curl -fsSL --retry 3 -o /etc/apt/keyrings/apt.llvm.org.asc https://apt.llvm.org/llvm-snapshot.gpg.key
chmod 0644 /etc/apt/keyrings/apt.llvm.org.asc
echo "deb [signed-by=/etc/apt/keyrings/apt.llvm.org.asc] http://apt.llvm.org/$CODENAME/ llvm-toolchain-$CODENAME-17 main" \
  > /etc/apt/sources.list.d/llvm-toolchain-$CODENAME-17.list
# Ubuntu noble also ships its own clang-17 (1:17.0.6-9ubuntu1) and apt would prefer it, because
# apt.llvm.org's "1:17.0.6~++2024..." sorts below it ("~"). Pin apt.llvm.org so the toolchain is the
# upstream LLVM 17.0.6 build (commit 6009708b4367) the artifact of record was compiled with.
printf 'Package: *\nPin: origin "apt.llvm.org"\nPin-Priority: 1001\n' > /etc/apt/preferences.d/99-apt-llvm-org
apt-get update -o Acquire::Retries=3
# The C++ standard library headers are part of the code generation: the artifact of record was
# compiled against GCC 12's libstdc++ (Debian bookworm). noble's clang-17 pulls libstdc++-13-dev;
# on jammy (default GCC 11) install libstdc++-12-dev as well -- clang selects the newest GCC
# installation it finds, so this makes it build against the GCC 12 headers.
EXTRA_PKGS=""
[[ "$CODENAME" == "jammy" ]] && EXTRA_PKGS="libstdc++-12-dev"
apt-get install --yes --no-install-recommends -o Acquire::Retries=3 \
  clang-17 lld-17 llvm-17 llvm-17-linker-tools libclang-rt-17-dev $EXTRA_PKGS
rm -rf /var/lib/apt/lists/*

# UPX 5.1.1 (the exact packer the shipped comp9/archive9 prefixes were made with; the
# harness validates upx-overlay artifacts with the same pinned release, whose tarball
# sha256 is 1ff660454227861e00772f743f66b900072116b9dc24f6ee28b97cce88a7828a).
UPX_TXZ_SHA=1ff660454227861e00772f743f66b900072116b9dc24f6ee28b97cce88a7828a
UPX_BIN_SHA=6cf3932e8d94a81b705ca7714731dff7a25d4745feee15ef532c20fe52ec8474
if ! curl -fsSL --retry 3 -o "$TMPDIR/upx.txz" \
     https://github.com/upx/upx/releases/download/v5.1.1/upx-5.1.1-amd64_linux.tar.xz; then
  echo "install.sh: could not download UPX 5.1.1 from GitHub" >&2
  if [[ -x /opt/upx/upx-5.1.1-amd64_linux/upx ]]; then
    echo "install.sh: falling back to the judging image's pinned /opt/upx copy" >&2
    install -m 0755 /opt/upx/upx-5.1.1-amd64_linux/upx /usr/local/bin/upx
  else
    exit 1
  fi
else
  echo "$UPX_TXZ_SHA  $TMPDIR/upx.txz" | sha256sum -c -
  tar -xJf "$TMPDIR/upx.txz" -C "$TMPDIR"
  install -m 0755 "$TMPDIR/upx-5.1.1-amd64_linux/upx" /usr/local/bin/upx
  rm -rf "$TMPDIR/upx.txz" "$TMPDIR/upx-5.1.1-amd64_linux"
fi
echo "$UPX_BIN_SHA  /usr/local/bin/upx" | sha256sum -c -

# Record what was installed (the harness keeps install.log; this is the toolchain of record).
echo "install.sh complete:"
clang++-17 --version | head -1
clang++-17 -v -x c++ -E /dev/null 2>&1 | grep -E "Selected GCC installation|libstdc\+\+" | head -2 || true
ld.lld-17 --version | head -1
llvm-profdata-17 --version | head -1
/usr/local/bin/upx --version | head -1
make --version | head -1
objdump --version | head -1
python3 --version
dpkg-query -W -f='${Package} ${Version}\n' clang-17 lld-17 llvm-17 libclang-common-17-dev libstdc++-13-dev libstdc++-12-dev libstdc++-11-dev libc6 binutils 2>/dev/null || true
case "$(dpkg-query -W -f='${Version}' clang-17)" in
  *'~++'*) ;;
  *) echo "install.sh: clang-17 is not the apt.llvm.org build (pin failed)" >&2; exit 1 ;;
esac
