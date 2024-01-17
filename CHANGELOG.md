# Baseline Builder

## 1.4.0

## 1.3.0
- Add support for providing GitHub token via `github_token` parameter
  - Overrides OS environment variable `GITHUB_TOKEN`
- Enforce strict pathing for executables during build
  - Ensures non-Apple binaries are not used during build
- Add `validate_pkg()` function for validating built packages.
  - Will decompress and extract pkg files, mimicking Baseline's install process.
  - Primarily intended for validating baseline_builder changes in CI, but useful for local testing as well.
- Add support for stand alone validation of existing packages.
  - `baseline_builder.py --validate <path_to_pkg>`
  - `baseline_builder.py --validate <path_to_config> <path_to_pkg>`
- Publish project version in help menu.
- PyPI Wheel Changes:
  - Following properties added to class:
    - `__version__`
    - `__author__` (changes old setup.py author from `RIPEDA` to `RIPEDA Consulting`)
    - `__author_email__` (changed from employee to support)
- Add requirements.txt
  - Resolves missing requests module in CI

## 1.2.1
- Fix 1.1.0 regression where configuration file may be missing

## 1.1.0
- CI: Switch to `svenstaro/upload-release-action@v2`
- Validation: Ensure Installomator labels are valid
- Build: Add support for mobileconfig-based inputs
  - Generates a new mobileconfig next to pkg with suffix `-resolved.mobileconfig`
  - ex. `ripeda.mobileconfig` -> `ripeda-resolved.mobileconfig`

## 1.0.7
- Add support for distribution packages.
  - Allows for deployment through MDM without munki or other package management solutions.
  - Reference: [Mobile Device Management Protocol Reference: macOS App Installation](https://developer.apple.com/business/documentation/MDM-Protocol-Reference.pdf)
  - Requires macos-pkg-builder 1.0.8 or newer.

## 1.0.6
- Add support for fetching Baseline from branches instead of releases.
  - Allows for easy testing of Baseline changes before they are merged into `main` or have a release associated.
  - Pass `branch: <branch_name>` to `baseline_version` parameter.
    - ex. `baseline_version="branch: 2.0-beta1"`

## 1.0.5
- Switch to logging module for printing
  - To be configured by the calling script
- Add package signing support
  - New `signing_identity` parameter passed to `macos_pkg_builder`

## 1.0.4
- Add support for API token authentication for GitHub
  - Environment variable `GITHUB_TOKEN` will be used if present

## 1.0.3
- Resolve caching logic incorrectly pulling from GitHub when local file is present

## 1.0.2
- Add support for caching swiftDialog and Installomator pkg (creates more stable build if repo moves/is not available)
  - New optional parameters:
    - `cache_swift_dialog` (defaults to `False`, Baseline will pull during install)
    - `cache_installomator` (defaults to `False`, Baseline will pull during install)
      - Installomator caching requires Baseline 1.3 or newer
  - Uses local `swiftDialog.pkg` and `Installomator.pkg` if present, otherwise pulls from GitHub
- Allow forcing Baseline, swiftDialog and Installomator versions
  - New optional parameters:
    - `baseline_version` (defaults to `latest`)
    - `swift_dialog_version` (defaults to `latest`, requires `cache_swift_dialog` to be `True`)
    - `installomator_version` (defaults to `latest`, requires `cache_installomator` to be `True`)
- Implement Copy on Write (CoW) during `/bin/cp` calls for reduced disk usage during build
- Add final pass to configuration file to ensure sanity
  - Performed after config is written back to disk, to simulate Baseline loading the config
- Only add brackets to arguments if they have a space in them
  - Opt for double quotes instead of single quotes

## 1.0.1
- Create output directory if missing

## 1.0.0
- Initial release