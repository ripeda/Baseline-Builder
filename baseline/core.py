"""
core.py: Core module for Baseline Builder.
"""

import os
import shlex
import logging
import plistlib
import tempfile
import requests
import subprocess
import macos_pkg_builder

from pathlib import Path

from . import __version__

BIN_CP:      str = "/bin/cp"
BIN_CHMOD:   str = "/bin/chmod"
BIN_MD5:     str = "/sbin/md5"
BIN_TAR:     str = "/usr/bin/tar"
BIN_CURL:    str = "/usr/bin/curl"
BIN_GREP:    str = "/usr/bin/grep"
BIN_UNZIP:   str = "/usr/bin/unzip"
BIN_XATTR:   str = "/usr/bin/xattr"
BIN_PKGUTIL: str = "/usr/sbin/pkgutil"

# Avoid API rate limits by Github.
BASELINE_ZIP_CACHE:              str = ""
SWIFTDIALOG_PKG_CACHE:           str = ""
INSTALLOMATOR_PKG_CACHE:         str = ""
INSTALLOMATOR_SUPPORTED_LABELS: list = []

DOWNLOAD_CACHE: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()

class BaselineBuilder:

    def __init__(
            self, configuration_file: str,

            identifier: str = "",
            version:    str = "1.0.0",
            output:     str = "Baseline.pkg",

            cache_swift_dialog:   bool = False,
            cache_installomator:  bool = False,

            baseline_version:      str = "latest",
            swiftdialog_version:   str = "latest",
            installomator_version: str = "latest",

            signing_identity:      str = "",

            pkg_as_distribution:  bool = False,

            github_token:          str = "",

            simple_mdm_icon:       str = None,

            embed_versioning:      bool = True,
        ) -> None:

        self.configuration_file = configuration_file
        self.configuration      = None

        self.identifier = identifier if identifier != "" else "com.example.baseline"
        self.version    = version
        self.output     = output

        self._build_directory      = tempfile.TemporaryDirectory()
        self._build_directory_path = Path(self._build_directory.name)

        self._build_pkg_path             = Path(self._build_directory_path / "Packages")
        self._build_scripts_path         = Path(self._build_directory_path / "Scripts")
        self._build_icons_path           = Path(self._build_directory_path / "Icons")

        self._baseline_core_script        = None
        self._baseline_preinstall_script  = None
        self._baseline_postinstall_script = None
        self._baseline_launch_daemon      = None
        self._baseline_configuration      = None

        self._build_cache_swift_dialog  = cache_swift_dialog
        self._build_cache_installomator = cache_installomator

        self._baseline_version      = baseline_version
        self._swiftdialog_version   = swiftdialog_version
        self._installomator_version = installomator_version

        self._signing_identity = signing_identity

        self._pkg_as_distribution = pkg_as_distribution

        self._github_token = github_token

        self._simple_mdm_icon = simple_mdm_icon

        self._embed_versioning = embed_versioning

        self._baseline_resolved_version      = None
        self._swiftdialog_resolved_version   = None
        self._installomator_resolved_version = None

        if baseline_version != "latest":
            self._baseline_resolved_version = baseline_version
        if swiftdialog_version != "latest":
            self._swiftdialog_resolved_version = swiftdialog_version
        if installomator_version != "latest":
            self._installomator_resolved_version = installomator_version


    def _fetch_api_content(self, url: str) -> requests.Response:
        """
        Fetch content, if GitHub link and token available, use them.
        """
        if "api.github.com" not in url:
            return requests.get(url)
        if self._github_token != "":
            return requests.get(url, headers={"Authorization": f"token {self._github_token}"})
        if "GITHUB_TOKEN" not in os.environ:
            return requests.get(url)

        return requests.get(url, headers={"Authorization": f"token {os.environ['GITHUB_TOKEN']}"})


    def _resolve_baseline_download_url(self, version: str) -> str:
        """
        Resolve what URL to download Baseline from.
        """

        if version.startswith("branch: "):
            return f"https://github.com/secondsonconsulting/Baseline/archive/refs/heads/{version.replace('branch: ', '')}.zip"

        if version == "latest":
            api_url = f"https://api.github.com/repos/secondsonconsulting/Baseline/releases/latest"
        else:
            api_url = f"https://api.github.com/repos/secondsonconsulting/Baseline/releases/tags/{version}"

        result = self._fetch_api_content(api_url)
        if result.status_code != 200:
            raise Exception(f"Unable to fetch Baseline from GitHub: {result.status_code}")

        result = result.json()
        if "zipball_url" not in result:
            raise Exception(f"No zipball_url in GitHub response: {result}")

        self._baseline_resolved_version = result["tag_name"]

        return result["zipball_url"]


    def _fetch_baseline(self, version: str) -> None:
        """
        Fetch Baseline from GitHub.
        Use local copy if available.
        """

        logging.info(f"Fetching Baseline: {version}...")

        search_paths = [
            DOWNLOAD_CACHE.name + "/Baseline.zip",
            "Baseline.zip"
        ]

        for path in search_paths:
            if Path(path).exists():
                logging.info(f"  Using existing Baseline.zip: {path}")
                subprocess.run([BIN_CP, "-c", path, self._build_directory_path])
                break

        asset_url = ""
        if Path(f"{self._build_directory_path}/Baseline.zip").exists() is False:
            logging.info("  No cached pkg for Baseline, fetching from GitHub...")

            asset_url = self._resolve_baseline_download_url(version)

            subprocess.run([BIN_CURL, "-s", "-L", "-o", "Baseline.zip", asset_url], cwd=DOWNLOAD_CACHE.name)
            subprocess.run([BIN_CP, "-c", "Baseline.zip", self._build_directory_path], cwd=DOWNLOAD_CACHE.name)

        # Unzip the baseline zip into Baseline folder.
        logging.info(f"  Unzipping...")
        result = subprocess.run([BIN_UNZIP, "-q", "Baseline.zip"], cwd=self._build_directory_path)
        if result.returncode != 0:
            error_message = "Unable to unzip Baseline.zip"
            if asset_url != "":
                error_message += f", verify that the asset URL is valid: {asset_url}"

            raise Exception(error_message)

        # Rename first folder to Baseline
        for item in self._build_directory_path.iterdir():
            if not item.is_dir():
                continue
            if "Baseline" not in item.name:
                continue
            item.rename(self._build_directory_path / "Baseline")
            break

        # Remove the Baseline.zip file.
        (self._build_directory_path / "Baseline.zip").unlink()

        # Set Baseline properties
        self._baseline_core_script        = self._build_directory_path / "Baseline" / "Baseline.sh"
        self._baseline_preinstall_script  = self._build_directory_path / "Baseline" / "Build" / "Baseline_daemon-preinstall.sh"
        self._baseline_postinstall_script = self._build_directory_path / "Baseline" / "Build" / "Baseline_daemon-postinstall.sh"
        self._baseline_launch_daemon      = self._build_directory_path / "Baseline" / "Build" / "com.secondsonconsulting.baseline.plist"

        if self.configuration_file.endswith(".plist"):
            self._baseline_configuration = self._build_directory_path / "Baseline" / "BaselineConfig.plist"
        else:
            # Write mobileconfig to the pkg output directory.
            self._baseline_configuration = Path(self.output).parent / Path(Path(self.configuration_file).stem + "-resolved.mobileconfig")


    def _fetch_swift_dialog(self, version: str) -> None:
        """
        Fetch swiftDialog from GitHub.
        Use local copy if available.
        """

        if version == "latest":
            api_url = f"https://api.github.com/repos/swiftDialog/swiftDialog/releases/latest"
        else:
            api_url = f"https://api.github.com/repos/swiftDialog/swiftDialog/releases/tags/{version}"

        logging.info(f"Fetching swiftDialog: {version}...")

        if not self._build_pkg_path.exists():
            self._build_pkg_path.mkdir()

        for path in [DOWNLOAD_CACHE.name + "/swiftDialog.pkg", "swiftDialog.pkg"]:
            if Path(path).exists():
                logging.info(f"  Using existing swiftDialog.pkg: {path}")
                subprocess.run([BIN_CP, "-c", path, self._build_pkg_path])
                break

        if Path(f"{self._build_pkg_path}/swiftDialog.pkg").exists() is False:
            logging.info("  No cached pkg for swiftDialog, fetching from GitHub...")
            result = self._fetch_api_content(api_url)
            if result.status_code != 200:
                raise Exception(f"Unable to fetch swiftDialog from GitHub: {result.status_code}")
            result = result.json()
            if "assets" not in result:
                raise Exception(f"No assets in GitHub response: {result}")
            if len(result["assets"]) <= 0:
                raise Exception(f"No assets in GitHub response: {result}")
            if "browser_download_url" not in result["assets"][0]:
                raise Exception(f"No browser_download_url in GitHub response: {result}")
            subprocess.run([BIN_CURL, "-s", "-L", "-o", "swiftDialog.pkg", result["assets"][0]["browser_download_url"]], cwd=DOWNLOAD_CACHE.name)
            subprocess.run([BIN_CP, "-c", "swiftDialog.pkg", self._build_pkg_path], cwd=DOWNLOAD_CACHE.name)

            self._swiftdialog_version = result["tag_name"]


    def _fetch_installomator(self, version: str) -> None:
        """
        Fetch Installomator from GitHub.
        Use local copy if available.
        """

        if version == "latest":
            api_url = f"https://api.github.com/repos/Installomator/Installomator/releases/latest"
        else:
            api_url = f"https://api.github.com/repos/Installomator/Installomator/releases/tags/{version}"

        logging.info(f"Fetching Installomator: {version}...")

        for path in [DOWNLOAD_CACHE.name + "/Installomator.pkg", "Installomator.pkg"]:
            if Path(path).exists():
                logging.info(f"  Using existing Installomator.pkg: {path}")
                subprocess.run([BIN_CP, "-c", path, self._build_pkg_path])
                break

        if Path(f"{self._build_pkg_path}/Installomator.pkg").exists() is False:
            logging.info("  No cached pkg for Installomator, fetching from GitHub...")
            result = self._fetch_api_content(api_url)
            if result.status_code != 200:
                raise Exception(f"Unable to fetch Installomator from GitHub: {result.status_code}")
            result = result.json()
            if "assets" not in result:
                raise Exception(f"No assets in GitHub response: {result}")
            if len(result["assets"]) <= 0:
                raise Exception(f"No assets in GitHub response: {result}")
            if "browser_download_url" not in result["assets"][0]:
                raise Exception(f"No browser_download_url in GitHub response: {result}")
            subprocess.run([BIN_CURL, "-s", "-L", "-o", "Installomator.pkg", result["assets"][0]["browser_download_url"]], cwd=DOWNLOAD_CACHE.name)
            subprocess.run([BIN_CP, "-c", "Installomator.pkg", self._build_pkg_path], cwd=DOWNLOAD_CACHE.name)

            self._installomator_version = result["tag_name"]


    def _resolve_file(self, file: str, variant: str, ignore_if_missing: bool = False) -> str:
        """
        Attempt to resolve the icon path and copy it to the build directory.
        Returns resolved icon path.
        """

        if ignore_if_missing is False:
            logging.info(f"    Resolving file: {Path(file).name}...")

        local_destination      = ""
        production_destination = ""

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
            subprocess.run([BIN_CP, "-ac", file, local_destination])
            return str(production_destination + "/" + Path(file).name)

        if ignore_if_missing is True:
            return file

        raise Exception(f"Unable to resolve file: {file}")


    def _calculate_md5(self, file: str) -> str:
        """
        Calculate the MD5 of a file.
        """
        logging.info(f"    Calculating MD5 for: {Path(file).name}...")
        if file.startswith("/usr/local/Baseline/"):
            file = file.replace("/usr/local/Baseline", f"{self._build_directory_path}")
        return subprocess.run([BIN_MD5, "-q", file], capture_output=True).stdout.decode("utf-8").strip()


    def _resolve_team_id(self, file: str) -> str:
        """
        Determine the team ID of a package.
        """
        logging.info(f"    Determining Team ID for: {Path(file).name}...")
        if file.startswith("/usr/local/Baseline/"):
            file = file.replace("/usr/local/Baseline", f"{self._build_directory_path}")

        if file.endswith(".pkg"):
            result = subprocess.run([BIN_PKGUTIL, "--check-signature", file], capture_output=True).stdout.decode("utf-8").strip()
            for line in result.split("\n"):
                if "Developer ID Installer: " not in line:
                    continue
                return line.split("(")[1].split(")")[0]
        return ""


    def _resolve_arguments(self, arguments: str) -> list:
        """
        Resolve arguments into a list.
        """
        return shlex.split(arguments)


    def _rebuild_arguments(self, arguments: list) -> str:
        """
        Rebuild arguments into a string.
        """
        arguments_string = ""
        for argument in arguments:
            if isinstance(argument, str):
                if " " in argument:
                    argument = f'"{argument}"'
            arguments_string += f" {argument}"
        return arguments_string


    def _parse_baseline_configuration(self) -> None:
        """
        Parse the baseline configuration file and resolve any files.
        """

        config_contents = self.configuration if self.configuration_file.endswith(".plist") else self.configuration["PayloadContent"][0]

        for variant in ["InitialScripts", "Installomator", "Packages", "Scripts"]:
            if variant not in config_contents:
                continue
            if len(config_contents[variant]) <= 0:
                continue

            logging.info(f"Processing key: {variant}...")

            for item in config_contents[variant]:
                if "DisplayName" not in item:
                    raise Exception(f"Missing DisplayName in {variant} item.")

                logging.info(f"  Processing item: {item['DisplayName']}")

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

                if "Arguments" in item and variant != "Installomator":
                    arguments = self._resolve_arguments(item["Arguments"])
                    for index, argument in enumerate(arguments):
                        if argument.startswith("-"):
                            continue
                        if argument.startswith('"') or argument.startswith("'"):
                            argument = argument[1:]
                        if argument.endswith('"') or argument.endswith("'"):
                            argument = argument[:-1]
                        arguments[index] = self._resolve_file(argument, "Icon", ignore_if_missing=True)
                    item["Arguments"] = self._rebuild_arguments(arguments)


        # Check if any files are passed in the dialog options.
        for variant in ["DialogListOptions", "DialogSuccessOptions", "DialogFailureOptions"]:
            if variant not in config_contents:
                continue
            arguments = self._resolve_arguments(config_contents[variant])

            logging.info(f"Processing key: {variant}...")

            # Resolve any files in the arguments.
            for index, argument in enumerate(arguments):
                if argument.startswith("-"):
                    continue
                if argument.startswith('"') or argument.startswith("'"):
                    argument = argument[1:]
                if argument.endswith('"') or argument.endswith("'"):
                    argument = argument[:-1]
                arguments[index] = self._resolve_file(argument, "Icon")

            config_contents[variant] = self._rebuild_arguments(arguments)

        if not self.configuration_file.endswith(".plist"):
            self.configuration["PayloadContent"][0] = config_contents


        # If embed versioning is requested, update the version in the configuration file.
        # Add 'Baseline-Builder' dictionary to top level of configuration file.
        if self._embed_versioning is True:
            if "Baseline-Builder" not in self.configuration:
                self.configuration["Baseline-Builder"] = {}
            self.configuration["Baseline-Builder"]["Project Version"] = self.version
            self.configuration["Baseline-Builder"]["Project Identifier"] = self.identifier
            self.configuration["Baseline-Builder"]["Baseline-Builder Version"] = __version__
            self.configuration["Baseline-Builder"]["Baseline Version"] = self._baseline_resolved_version or "N/A"
            self.configuration["Baseline-Builder"]["swiftDialog Version"] = self._swiftdialog_resolved_version or "N/A"
            self.configuration["Baseline-Builder"]["Installomator Version"] = self._installomator_resolved_version or "N/A"

        # Write the configuration file.
        plistlib.dump(self.configuration, open(self._baseline_configuration, "wb"), sort_keys=False)


    def _set_file_permissions(self) -> None:
        """
        Set file permissions to ensure that when Baseline is installed, the files are executable.
        """
        if Path(self._baseline_core_script).exists():
            subprocess.run([BIN_CHMOD, "+x", self._baseline_core_script])

        if Path(self._build_scripts_path).exists():
            for file in self._build_scripts_path.iterdir():
                subprocess.run([BIN_CHMOD, "+x", file])


    def _clear_problematic_xattr(self) -> None:
        """
        Clear problematic extended attributes from the build directory.
        """
        xattr_to_remove = [
            "com.apple.quarantine",
            "com.apple.metadata:kMDItemDownloadedDate",
            "com.apple.metadata:kMDItemWhereFroms",
        ]
        for xattr in xattr_to_remove:
            subprocess.run([BIN_XATTR, "-dr", xattr, self._build_directory_path])


    def _generate_fake_icon(self) -> None:
        """
        SimpleMDM's API doesn't support custom icons
        Thus create a fake Baseline app for it to pull the icon from.
        """
        app_path = self._build_directory_path / ".Baseline.app"
        Path(app_path, "Contents/Resources").mkdir(parents=True)
        result = subprocess.run([BIN_CP, "-c", self._simple_mdm_icon, app_path / "Contents/Resources/"])
        if result.returncode != 0:
            raise Exception(f"Unable to copy icon to fake app: {self._simple_mdm_icon}")
        plistlib.dump({"CFBundleIconFile": Path(self._simple_mdm_icon).name}, open(app_path / "Contents/Info.plist", "wb"), sort_keys=False)


    def _generate_pkg(self) -> bool:
        """
        Generate package using macos_pkg_builder library.
        """
        pkg_obj = macos_pkg_builder.Packages(
            pkg_output=self.output,
            pkg_bundle_id=self.identifier,
            pkg_version=self.version,
            pkg_preinstall_script=self._baseline_preinstall_script,
            pkg_postinstall_script=self._baseline_postinstall_script,
            pkg_file_structure={
                # Required
                f"{self._baseline_launch_daemon}" : "/Library/LaunchDaemons/com.secondsonconsulting.baseline.plist",
                f"{self._baseline_core_script}"   : "/usr/local/Baseline/Baseline.sh",

                # Dependant on configuration file.
                **({ f"{self._baseline_configuration}" : "/usr/local/Baseline/BaselineConfig.plist", } if self.configuration_file.endswith(".plist") else {}),

                # Optional if user requested
                **({ f"{self._build_pkg_path}"    : "/usr/local/Baseline/Packages" } if self._build_pkg_path.exists()     else {}),
                **({ f"{self._build_scripts_path}": "/usr/local/Baseline/Scripts"  } if self._build_scripts_path.exists() else {}),
                **({ f"{self._build_icons_path}"  : "/usr/local/Baseline/Icons"    } if self._build_icons_path.exists()   else {}),

                # SimpleMDM icon (if requested)
                **({ f"{self._build_directory_path}/.Baseline.app" : "/usr/local/Baseline/.Baseline.app" } if self._simple_mdm_icon is not None else {})
            },
            **({ "pkg_signing_identity": self._signing_identity } if self._signing_identity != "" else {}),
            **({ "pkg_as_distribution": self._pkg_as_distribution } if self._pkg_as_distribution is True else {})
        )

        return pkg_obj.build()


    def _validate(self, configuration: str = None, directory: str = None, localize: bool = True) -> None:
        """
        Validate the configuration file.
        """

        if configuration is None:
            configuration = self._baseline_configuration
        if directory is None:
            directory = self._build_directory_path

        config = plistlib.load(open(configuration, "rb"))

        config_contents = config if self.configuration_file.endswith(".plist") else config["PayloadContent"][0]

        logging.info("Validating configuration file...")
        for variant in ["InitialScripts", "Installomator", "Packages", "Scripts"]:
            if variant not in config_contents:
                continue
            for item in config_contents[variant]:
                if "DisplayName" not in item:
                    raise Exception(f"Missing DisplayName in {variant} item.")
                path = "ScriptPath" if variant == "Scripts" else "PackagePath"
                if path in item:
                    logging.info(f"    Validating {path}: {Path(item[path]).name}...")
                    file = Path(f"{directory}/{item[path]}".replace("/usr/local/Baseline" if localize is True else "", ""))
                    if Path(file).exists() is False:
                        raise Exception(f"Unable to find {path}: {file}")
                    if item["MD5"] != self._calculate_md5(str(file)):
                        raise Exception(f"MD5 mismatch for {path}: {item[path]}")
                    if "TeamID" in item:
                        if item["TeamID"] != self._resolve_team_id(str(file)):
                            raise Exception(f"TeamID mismatch for {path}: {item[path]}")
                if "Icon" in item:
                    logging.info(f"    Validating Icon: {Path(item['Icon']).name}...")
                    file = Path(f"{directory}/{item['Icon']}".replace("/usr/local/Baseline" if localize is True else "", ""))
                    if Path(file).exists() is False:
                        raise Exception(f"Unable to find Icon: {file}")
                if variant == "Installomator" and "Label" in item:
                    if self._is_installomator_label_valid(item["Label"]) is False:
                        raise Exception(f"Invalid Installomator label: {item['Label']}")

        logging.info("Configuration file is valid.")


    def _is_installomator_label_valid(self, label: str) -> bool:
        """
        Verify whether Installomator label is valid.
        """
        logging.info(f"    Validating Installomator label: {label}...")

        global INSTALLOMATOR_SUPPORTED_LABELS
        if INSTALLOMATOR_SUPPORTED_LABELS == []:
            if self._installomator_version == "latest":
                url = "https://raw.githubusercontent.com/Installomator/Installomator/main/Installomator.sh"
            else:
                url = f"https://raw.githubusercontent.com/Installomator/Installomator/blob/{self._installomator_version}/Installomator.sh"

            result = requests.get(url)
            if result.status_code != 200:
                raise Exception(f"Unable to fetch Installomator.sh: {result.status_code}")
            # Write to download cache.
            with open(f"{DOWNLOAD_CACHE.name}/Installomator.sh", "w") as file:
                file.write(result.text)

            # Replicate installomator's label validation.
            # https://github.com/Installomator/Installomator/blob/v10.5/Installomator.sh#L1413-L1418
            labels = subprocess.run([BIN_GREP, "--extended-regexp", "^[a-z0-9\_-]*(\)|\|\\\\)$", f"{DOWNLOAD_CACHE.name}/Installomator.sh"], capture_output=True).stdout.decode("utf-8").strip()
            labels = labels.replace(")", "").replace("|", "").replace("\\", "").split("\n")
            labels = [label for label in labels if label not in ["longversion", "version"]]
            labels = [label for label in labels if label.startswith("broken.") is False]

            INSTALLOMATOR_SUPPORTED_LABELS = labels

        if label in INSTALLOMATOR_SUPPORTED_LABELS:
            return True

        return False


    def _validate_pkg(self, pkg: str) -> None:
        """
        Extract pkg contents, and validate if it would install correctly.
        """

        logging

        temp_directory = tempfile.TemporaryDirectory()
        source = Path(temp_directory.name + "/pkg")

        subprocess.run([BIN_PKGUTIL, "--expand", pkg, source], capture_output=True)

        payload_path = f"{temp_directory.name}/pkg/Payload"

        if Path(f"{temp_directory.name}/pkg/Distribution").exists():
            # Grab first pkg in the directory.
            item = [item for item in Path(f"{temp_directory.name}/pkg").iterdir() if item.name.endswith(".pkg")][0]
            if item is None:
                raise Exception(f"Unable to find embedded pkg: {temp_directory.name}/pkg/*.pkg")

            payload_path = f"{temp_directory.name}/pkg/{Path(item).name}/Payload"

        if not Path(payload_path).exists():
            raise Exception(f"Unable to find Payload in pkg: {pkg}")

        subprocess.run([BIN_TAR, "--extract", "--file", payload_path, "--directory", source], capture_output=True)

        # Check core files.
        files = [
            "/Library/LaunchDaemons/com.secondsonconsulting.baseline.plist",
            "/usr/local/Baseline/Baseline.sh",
            "/usr/local/Baseline/BaselineConfig.plist" if self.configuration_file.endswith(".plist") else "",
        ]
        for file in files:
            if file == "":
                continue
            if not Path(f"{source}{file}").exists():
                logging.info(f"Unable to find file in pkg: {source}{file}")
                subprocess.run(["open", source])
                input("Press Enter to continue...")
                raise Exception(f"Unable to find file in pkg: {source}{file}")

            # Verify if plist is malformed, will raise if invalid.
            if file.endswith(".plist"):
                plistlib.load(open(f"{source}{file}", "rb"))

        # Load embedded config or exported mobileconfig.
        config = f"{source}/usr/local/Baseline/BaselineConfig.plist" if self.configuration_file.endswith(".plist") else self.configuration_file

        self._validate(configuration=config, directory=source, localize=False)


    def build(self) -> None:
        """
        Build Baseline

        Raises:
            Exception: Unable to generate pkg.
        """
        self.configuration = plistlib.load(open(self.configuration_file, "rb"))

        self._fetch_baseline(version=self._baseline_version)
        if self._build_cache_swift_dialog is True:
            self._fetch_swift_dialog(version=self._swiftdialog_version)
        if self._build_cache_installomator is True:
            self._fetch_installomator(version=self._installomator_version)
        self._parse_baseline_configuration()
        self._set_file_permissions()
        self._clear_problematic_xattr()
        self._validate()
        if self._simple_mdm_icon is not None:
            self._generate_fake_icon()
        if self._generate_pkg() is False:
            raise Exception("Failed to generate pkg.")

        # Very lazy hack, but set the configuration file to the resolved variant if it was a mobileconfig.
        if self.configuration_file.endswith(".mobileconfig"):
            self.configuration_file = str(self._baseline_configuration)
            logging.info(f"Configuration file set to: {self.configuration_file}")


    def validate_pkg(self, pkg: str = None) -> None:
        """
        Validate Baseline pkg (post-build)

        Raises:
            Exception: Unable to find pkg.
            Exception: Unable to validate pkg.
        """
        if pkg is None:
            pkg = self.output

        logging.info("Performing post-build validation...")
        if not Path(pkg).exists():
            logging.info(f"Unable to find pkg: {pkg}")
            logging.info("Please build the pkg first.")
            raise Exception("Unable to find pkg.")

        self._validate_pkg(pkg)
        logging.info("Post-build validation complete.")