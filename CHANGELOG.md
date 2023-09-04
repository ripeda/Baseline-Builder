# Baseline Builder

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