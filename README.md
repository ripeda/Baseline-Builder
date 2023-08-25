# Baseline Builder


Python-based tooling for generating [Baseline packages](https://github.com/SecondSonConsulting/Baseline), with the goal of streamlining package deployment for multiple clients. Designed for easier CI/CD integration with Python 3.6+.

------------

Features implemented:
- Resolves local files such as scripts, packages and images to Baseline packaging
  - Scans in same directory as invocation script
- Calculates MD5 for scripts and packages
- Determines Team ID for local packages

## Logic

Baseline Builder works by taking config files for Baseline, and generating a package for deployment. If scripts, packages or images are declared in the file, Baseline Builder will attempt to resolve them and embed inside the package.

* See Baseline's documentation on how to configure: [Baseline Wiki](https://github.com/SecondSonConsulting/Baseline/wiki)

Example configuration can be found in the [Samples](Samples) directory. Below is pulled from RIPEDA Engineering configuration:

```xml
<key>Packages</key>
<array>
  <dict>
    <key>DisplayName</key>
    <string>Printer</string>
    <key>PackagePath</key>
    <string>Assets/Packages/Printer.pkg</string>
    <key>Icon</key>
    <string>Assets/Icons/Printer.png</string>
  </dict>
</array>
```

The project will attempt to resolve the `PackagePath` and `Icon` keys through scanning the local directory:
```
Baseline Builder Directory:
- client.plist
- Assets:
  - Packages:
    - Printer.pkg
  - Icons:
    - Printer.png
```


## Installation

```
pip3 install baseline-builder
```

## Usage


```py
import baseline

baseline_obj = baseline.BaselineBuilder(
                  configuration_file="ripeda.plist",
                  identifier="com.ripeda.baseline.engineering",
                  version="1.0.0",
                  output="RIPEDA Baseline.pkg"
                )
if baseline_obj.build() is False:
  print("Failed to build package")
  return

print("Package built successfully")
```