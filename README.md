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

Example of this is shown below:

```xml
<dict>
	<key>Packages</key>
	<array>
		<dict>
			<key>DisplayName</key>
			<string>RIPEDA Observer</string>
			<key>PackagePath</key>
			<string>/usr/local/Baseline/Packages/MonitoringClient.pkg</string>
			<key>Icon</key>
			<string>/usr/local/Baseline/Icons/MonitoringClient.icns</string>
		</dict>
	</array>
  ...
```

The project will attempt to resolve the `PackagePath` and `Icon` keys through scanning the local directory:
```
Baseline Builder Directory:
- client.plist
- Packages:
  - MonitoringClient.pkg
- Icons:
  - MonitoringClient.icns
```


## Installation

```
pip3 install baseline
```


## Usage


```py
import baseline

baseline_obj = baseline.BaselineBuilder("client.plist", "com.ripeda.baseline.client", "1.0.0")
baseline_obj.build()
```