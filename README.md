# Baseline Builder


Python-based tooling for generating [Baseline packages](https://github.com/SecondSonConsulting/Baseline), with the goal of streamlining package building for multiple clients. Designed for CI/CD integration with Python 3.6+.

------------

Features implemented:
- Resolves local files such as scripts, packages and images to Baseline packaging
  - Scans in same directory as invocation script
- Calculates MD5 and Team ID for script and package integrity
- Creates unified Baseline package for easy deployment

## Installation

```
pip3 install baseline
```


## Usage

Baseline Builder works by taking config files for Baseline, and generating a package for deployment. If scripts, packages or images are declared in the file, Baseline Builder will attempt to resolve them and embed inside the package.

```py
import baseline

baseline_obj = baseline.BaselineBuilder("client.plist", "com.ripeda.baseline.client", "1.0.0")
baseline_obj.build()
```