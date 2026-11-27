# Android release packaging

Apex Android preserves the upstream Git history, MIT copyright and license,
third-party notices and dependency licenses. See [upstream integration](android-upstream.json).
Nighty is an unofficial fork built on that history; its UI branch and release workflow
are maintained separately from upstream deployment workflows.

For automatic, separately installed development APKs for testers, see
[development builds in GitHub Actions](android-dev-builds.md).

## Nighty alpha.3 release

The current Nighty release is `v1.0.0-alpha.3` (`versionName 1.0.0-alpha.3`,
`versionCode 32`). The workflow in `.github/workflows/android.yml` builds the
ARM64-v8a public APK, attaches `nighty-arm64.apk` and `SHA256SUMS.txt` to the
GitHub release, and targets the exact source commit it built. It does not publish
the other ABIs listed below. Nighty is not affiliated with Mojang, Microsoft,
Starling or Zalith; see [security and privacy](security.md).

---

## Build distribution APKs

Build each required architecture with the optimized public mode:

```sh
python tools/android_build.py --abi arm64-v8a --public
python tools/android_build.py --abi armeabi-v7a --public
python tools/android_build.py --abi x86 --public
python tools/android_build.py --abi x86_64 --public
```

Outputs are `.local/android/apk/<abi>/apex-android-public.apk`.
The build signs and audits each APK. Default development APKs are not release
artifacts: they may contain private resource bundles and enable debugging.

### Payload

The public APK includes the Rust engine, licensed application dependencies and
allowlisted generated Apex tables. Original Minecraft resource files, JARs,
textures and sounds are not packaged as game resources. The installer downloads
them from Mojang, checks pinned hashes and reconstructs required world data on
the device. Touch textures and their license come from a pinned revision of
Mojang's official sample repository.

Public builds are non-debuggable, remap personal compiler paths, omit automatic
agent-control sockets and ignore `android-launch.json` development overrides.
The payload audit checks packaged paths, original-resource allowlists, recognized
credential patterns and the Android debuggable flag. Its scope is technical
packaging validation, not an exhaustive credential or licensing review.

### Signing and updates

Preserve the private signing key outside Git and release attachments. Android
requires a matching signing certificate and higher `versionCode` for an in-place
update. `versionName` is the visible application version. Update those values in
`packaging/android/build.gradle` and the launcher version together.

Public releases should attach:

- One clearly named APK per supported ABI.
- `SHA256SUMS.txt` covering the exact attached APKs; Nighty alpha releases also quote it in the release notes.
- `LICENSE.txt` and `THIRD_PARTY_NOTICES.md`.
- Release notes describing changes, requirements and known compatibility limits.

Include only APKs that passed their final payload/manifest audit. Confirm version,
minimum SDK, ELF architecture, signing certificate and the exact source commit.
Compilation results and device gameplay results should be reported separately.
Account integration remains a development configuration pending project-owned
Microsoft/Mojang registration; do not describe it as an approved integration.

## Versions and release branches

The Nighty line is at `1.0.0-alpha.3` (`versionCode 32`, ARM64-v8a), tagged
`v1.0.0-alpha.3`. The `0.7.5` material in the
[change list and validation scope](android-0.7.5.md) is upstream Apex history,
kept for reference. A Git push does not itself publish an APK; release attachments
must come from the exact tagged source (`--target "$GITHUB_SHA"` in the workflow).

Use `1.0.0-alpha.3-dev.<build>` for intermediate development APKs and
`1.0.0-alpha.3-rc.<build>` for explicitly prepared release candidates. Debug
builds use a separate `.dev` application ID by default, keeping their data separate
from the release app. Never replace an existing release asset with a different
binary of the same name.

Maintain changes as focused commits on working branches, integrate reviewed
upstream history into the Nighty branch, and record changes relative to the last
public release. Build and test the exact commit to be tagged. Only then create an
Android release tag such as `v1.0.0-alpha.3` and attach the audited APK and checksum
manifest.
Increment `versionCode` for every public Android update and preserve its signing
certificate. A source commit or development version is not a compatibility or
performance guarantee; list the architectures and device checks actually completed.

## Source checks

```sh
python -m unittest discover -s tests -p 'test_android*.py'
python tools/check_public_tree.py --history
```

`.githooks` guards public commits and pushes. Never publish `.local/`, prepared
resources, player data, signing keys or account/session files. Agent-authored
commits retain the attribution required by [AGENTS.md](../AGENTS.md).

An optional source export is available without publishing build inputs:

```sh
python tools/export_android_source.py
```

It writes a ZIP and hash manifest under `.local/android/public/`, excluding game
inputs, caches, saves, build products and signing material. Upstream workflows
remain under `.github/upstream-workflows/*.disabled`; the Android source workflow
runs source checks on pushes and pull requests to `android`, with read-only
permissions. A manual run with `native_checks` enabled also type-checks all four
Android ABIs, and one with `build_apk` enabled prepares the pinned engine tables,
builds that ABI's public APK and uploads it as a workflow artifact. The workflow
never publishes releases.

### Nighty alpha signing

The Nighty workflow restores `.local/android/debug.keystore` from the
`ANDROID_DEV_KEYSTORE_BASE64` repository secret when it is set; otherwise it
generates a fresh development keystore for that run.
`packaging/android/build.gradle` signs the release variant with that keystore.
No signing key is committed or attached to a release.

A changed keystore means a changed signing certificate: Android then requires
uninstalling the old app before installing the new APK. In-place updates need the
same keystore secret to be preserved and a higher `versionCode` for every public
release. Check the certificate in each build before describing an update as
in-place; an APK signed with a generated key is not a permanent signing identity.
The checksum manifest verifies the APK bytes, not the signing identity.

## Upstream maintenance

Fetch and review `upstream/main` before a release. Merge reviewed stable history
into the Nighty branch, resolve Android module paths and bridges, update
`docs/android-upstream.json`, and run Android checks before pushing. Keep
experimental feature clusters and upstream deployment changes separate from
routine Android fixes.
