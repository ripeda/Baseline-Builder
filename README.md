# Baseline Builder


Python-based tooling for generating [Baseline packages](https://github.com/SecondSonConsulting/Baseline), for streamlining package building of multiple clients. Designed for easier CI/CD integration with Python 3.

------------

Features implemented:
- Resolves local files such as scripts, packages and images to Baseline packaging
  - Scans in same directory as invocation script
- Calculates MD5 for scripts and packages
- Determines Team ID for local packages
- Easy imports for chaining into larger CI/CD workflows
- Validates existing packages:
  - Checks 

## Logic

Baseline Builder works by taking configuration files for Baseline, and generating a package for deployment. If scripts, packages or images are declared in the file, Baseline Builder will attempt to resolve them and embed inside the package.

* See Baseline's documentation on how to configure: [Baseline Wiki](https://github.com/SecondSonConsulting/Baseline/wiki)
* If an mobileconfig is provided as input, a resolved version will be written next to the package.
  * As the mobileconfig method is meant to be used, no BaselineConfig.plist is embedded in the package.

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


### Building
```py
import baseline

baseline_obj = baseline.BaselineBuilder(
                    configuration_file="ripeda.plist",
                    identifier="com.ripeda.baseline.engineering",
                    version="1.0.0",
                    output="RIPEDA Baseline.pkg"
                )

baseline_obj.build()

print("Package built successfully")
```

After a build is complete, optional `.validate_pkg()` can be invoked to decompress and validate the package contents automatically.

### Validating existing packages via command line

For quick validation of existing packages, the `-v/--validate` flag can be used to decompress and validate the package contents automatically.
If the package lacks a BaselineConfig.plist, a mobileconfig can be provided to validate against.

```bash
# Validate package with mobileconfig
python3 baseline.py --validate "RIPEDA.pkg" ripeda.mobileconfig

# Validate package without config (embedded in pkg)
python3 baseline.py --validate "RIPEDA.pkg"
```

```bash
# Example Output
$ python3 baseline.py --validate RIPEDA.pkg

Performing post-build validation...
Validating configuration file...
    Validating Icon: Zoom.icns...
    Validating Installomator label: zoom...
    Validating Icon: Chrome.icns...
    Validating Installomator label: googlechromepkg...
    Validating PackagePath: Printer.pkg...
    Calculating MD5 for: Printer.pkg...
    Determining Team ID for: Printer.pkg...
    Validating Icon: Scripts-Printer.png...
    Validating ScriptPath: universal_remove_stock_apps.sh...
    Calculating MD5 for: universal_remove_stock_apps.sh...
    Validating Icon: Scripts-Stock-Apps.png...
    Validating ScriptPath: universal_dock.sh...
    Calculating MD5 for: universal_dock.sh...
    Validating Icon: Scripts-Dock.png...
Configuration file is valid.
Post-build validation complete.
```