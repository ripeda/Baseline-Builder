# Baseline Builder

## 1.0.2
- Add embedding swiftDialog pkg (creates more stable build if repo moves/is not available)
  - New optional parameter `cache_swift_dialog` (defaults to `False`, Baseline will pull during install)
  - Uses local `swiftDialog.pkg` if present, otherwise pulls from GitHub
- Allow forcing Baseline and swiftDialog versions
  - New optional parameters:
    - `baseline_version` (defaults to `latest`)
    - `swift_dialog_version` (defaults to `latest`, requires `cache_swift_dialog` to be `True`)
- Implement Copy on Write (CoW) during `/bin/cp` calls for reduced disk usage during build

## 1.0.1
- Create output directory if missing

## 1.0.0
- Initial release