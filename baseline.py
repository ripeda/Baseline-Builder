#!/usr/bin/env python3

import argparse
import plistlib
import tempfile
import subprocess
import macos_pkg_builder

from pathlib import Path

BASELINE_VERSION:        str = "1.2"
BASELINE_REPOSITORY_URL: str = f"https://github.com/SecondSonConsulting/Baseline/archive/refs/tags/v{BASELINE_VERSION}.zip"


class BaselineBuilder:

    def __init__(self, configuration_file: str, identifier: str = "", version: str = "1.0.0") -> None:
        self.configuration_file = configuration_file
        self.configuration = plistlib.load(open(self.configuration_file, "rb"))

        self.identifier = identifier if identifier != "" else "com.example.baseline"
        self.version = version

        self._build_directory = tempfile.TemporaryDirectory()
        self._build_directory_path = Path(self._build_directory.name)

        self._build_pkg_path             = Path(self._build_directory_path / "Packages")
        self._build_scripts_path         = Path(self._build_directory_path / "Scripts")
        self._build_icons_path           = Path(self._build_directory_path / "Icons")

        self._baseline_core_script        = None
        self._baseline_preinstall_script  = None
        self._baseline_postinstall_script = None
        self._baseline_launch_daemon      = None


    def _fetch_baseline(self) -> None:
        """
        """

        print(f"Fetching Baseline v{BASELINE_VERSION}...")

        if not Path("Baseline.zip").exists():
            # Download the baseline repository.
            print(f"  Downloading...")
            subprocess.run(["curl", "-s", "-L", "-o", "Baseline.zip", BASELINE_REPOSITORY_URL], cwd=self._build_directory_path)
        else:
            print(f"  Using existing Baseline.zip")
            subprocess.run(["cp", "Baseline.zip", self._build_directory_path])

        # Unzip the baseline zip into Baseline folder.
        print(f"  Unzipping...")
        subprocess.run(["unzip", "-q", "Baseline.zip"], cwd=self._build_directory_path)

        # Rename the Baseline folder to Baseline
        for item in self._build_directory_path.iterdir():
            if item.name.startswith("Baseline-"):
                item.rename(self._build_directory_path / "Baseline")


        # Remove the Baseline.zip file.
        (self._build_directory_path / "Baseline.zip").unlink()

        # Set Baseline properties
        self._baseline_core_script        = self._build_directory_path / "Baseline" / "Baseline.sh"
        self._baseline_preinstall_script  = self._build_directory_path / "Baseline" / "Build" / "Baseline_daemon-preinstall.sh"
        self._baseline_postinstall_script = self._build_directory_path / "Baseline" / "Build" / "Baseline_daemon-postinstall.sh"
        self._baseline_launch_daemon      = self._build_directory_path / "Baseline" / "Build" / "com.secondsonconsulting.baseline.plist"
        self._baseline_configuration      = self._build_directory_path / "Baseline" / "BaselineConfig.plist"


    def _resolve_file(self, file: str, variant: str) -> str:
        """
        Attempt to resolve the icon path and copy it to the build directory.
        Returns resolved icon path.
        """

        local_destination      = ""
        production_destination = ""

        print(f"    Resolving file: {Path(file).name}...")

        if  variant == "Scripts":
            local_destination = self._build_scripts_path
        elif variant == "Packages":
            local_destination = self._build_pkg_path
        elif variant == "Icon":
            local_destination = self._build_icons_path
        else:
            raise Exception(f"Unknown variant: {variant}")

        production_destination = str(local_destination).replace(str(self._build_directory_path), "/usr/local/Baseline")

        if Path(local_destination).exists() is False:
            Path(local_destination).mkdir()

        if file.startswith("/usr/local/Baseline/"):
            file = file.replace("/usr/local/Baseline/", "")

        # Check if we already have the icon.
        if (local_destination / Path(file).name).exists():
            return str(production_destination + "/" + Path(file).name)

        # Check if a copy exists next to us
        if (Path(file)).exists():
            subprocess.run(["cp", "-a", file, local_destination])
            return str(production_destination + "/" + Path(file).name)

        raise Exception(f"Unable to resolve icon: {file}")


    def _calculate_md5(self, file: str) -> str:
        """
        """
        if file.startswith("/usr/local/Baseline/"):
            file = file.replace("/usr/local/Baseline", f"{self._build_directory_path}")
        print(f"    Calculating MD5 for: {file}...")
        return subprocess.run(["md5", "-q", file], capture_output=True).stdout.decode("utf-8").strip()


    def _resolve_team_id(self, file) -> str:
        """
        """
        if file.startswith("/usr/local/Baseline/"):
            file = file.replace("/usr/local/Baseline", f"{self._build_directory_path}")

        if file.endswith(".pkg"):
            result = subprocess.run(["pkgutil", "--check-signature", file], capture_output=True).stdout.decode("utf-8").strip()
            for line in result.split("\n"):
                if "Developer ID Installer: " not in line:
                    continue
                return line.split("(")[1].split(")")[0]
        return ""


    def _parse_baseline_configuration(self) -> None:
        """
        """

        for variant in ["InitialScripts", "Installomator", "Packages", "Scripts"]:
            if variant not in self.configuration:
                continue
            if len(self.configuration[variant]) <= 0:
                continue

            print(f"Processing key: {variant}...")

            for item in self.configuration[variant]:
                if "DisplayName" not in item:
                    raise Exception(f"Missing DisplayName in {variant} item.")

                print(f"  Processing item: {item['DisplayName']}")

                if "Icon" in item:
                    item["Icon"] = self._resolve_file(item["Icon"], "Icon")
                if "ScriptPath" in item:
                    item["ScriptPath"] = self._resolve_file(item["ScriptPath"], "Scripts")
                    item["MD5"] = self._calculate_md5(item["ScriptPath"])
                if "PackagePath" in item:
                    item["PackagePath"] = self._resolve_file(item["PackagePath"], "Packages")
                    team_id = self._resolve_team_id(item["PackagePath"])
                    if team_id != "":
                        item["TeamID"] = team_id
                    item["MD5"] = self._calculate_md5(item["PackagePath"])


        # Check if any files are passed in the dialog options.
        for variant in ["DialogListOptions", "DialogSuccessOptions", "DialogFailureOptions"]:
            if variant not in self.configuration:
                continue
            arguments_string = self.configuration[variant]
            # Resolve into a list of arguments.
            # Note we can't split if the user has escaped the space character.
            arguments = []
            argument = ""
            for character in arguments_string:
                if character == "\\":
                    continue
                if character == " ":
                    arguments.append(argument)
                    argument = ""
                    continue
                argument += character
            if argument != "":
                arguments.append(argument)

            print(f"Processing key: {variant}...")

            # Resolve any files in the arguments.
            for index, argument in enumerate(arguments):
                if argument.startswith("-"):
                    continue
                if argument.startswith('"') or argument.startswith("'"):
                    argument = argument[1:]
                if argument.endswith('"') or argument.endswith("'"):
                    argument = argument[:-1]
                arguments[index] = self._resolve_file(argument, "Icon")

            # Rebuild the arguments string.
            arguments_string = ""
            for argument in arguments:
                arguments_string += f" {argument}"

            self.configuration[variant] = arguments_string

        # Write the configuration file.
        plistlib.dump(self.configuration, open(self._baseline_configuration, "wb"), sort_keys=False)


    def _set_file_permissions(self) -> None:
        """
        """
        if Path(self._baseline_core_script).exists():
            subprocess.run(["chmod", "+x", self._baseline_core_script])

        if Path(self._build_scripts_path).exists():
            for file in self._build_scripts_path.iterdir():
                subprocess.run(["chmod", "+x", file])


    def _generate_pkg(self) -> bool:
        """
        """
        pkg_obj = macos_pkg_builder.Packages(
            pkg_output="Sample-Baseline.pkg",
            pkg_bundle_id=self.identifier,
            pkg_version=self.version,
            pkg_preinstall_script=self._baseline_preinstall_script,
            pkg_postinstall_script=self._baseline_postinstall_script,
            pkg_file_structure={
                f"{self._baseline_launch_daemon}" :         "/Library/LaunchDaemons/com.secondsonconsulting.baseline.plist",
                f"{self._baseline_core_script}" :           "/usr/local/Baseline/Baseline.sh",
                f"{self._baseline_configuration}" :         "/usr/local/Baseline/BaselineConfig.plist",

                # Optional if user requested
                **({ f"{self._build_pkg_path}":             "/usr/local/Baseline/Packages" }       if self._build_pkg_path.exists()     else {}),
                **({ f"{self._build_scripts_path}":         "/usr/local/Baseline/Scripts"  }       if self._build_scripts_path.exists() else {}),
                **({ f"{self._build_icons_path}":           "/usr/local/Baseline/Icons"    }       if self._build_icons_path.exists()   else {}),
            }
        )

        return pkg_obj.build()


    def build(self) -> None:
        """
        """
        self._fetch_baseline()
        self._parse_baseline_configuration()
        self._set_file_permissions()
        if self._generate_pkg() is False:
            raise Exception("Failed to generate pkg.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a baseline from a configuration file.')
    parser.add_argument('configuration_file', help='The configuration file to use to build the baseline.')
    args = parser.parse_args()

    builder = BaselineBuilder(args.configuration_file)
    builder.build()