#!/bin/zsh --no-rcs
# -----------------------------------------------
# macOS Dock Configuration Script
# -----------------------------------------------
#
# Takes an indefinte amount of arguments, and sets the dock to those apps
#
# Optional first argument is either "--overwrite" or "--append" to determine
# whether to clear the dock or append to it
#
# Supported argument formats for applications:
# - "Safari": Will resolve Safari's true path
# - "/Applications/Safari.app": Will use the provided path
#
# Script checks for .app ending on whether to resolve the path or not
#
# Current scan paths implemented:
# - /Applications
# - /Applications/Utilities
# - /System/Applications
# - /System/Applications/Utilities
# - /Users/$currentUser/Applications
#
# If script fails to resolve the path, it will default to /Applications
#
# -----------------------------------------------
#
# Sample invocations:
# - Overwrite:
#   ./universal_dock.sh "Safari" "Mail" "Calendar"
#   ./universal_dock.sh --overwrite "Safari" "Mail" "Calendar"
# - Append:
#   ./universal_dock.sh --append "Google Chrome" "Firefox"
#
# -----------------------------------------------

applications=("$@")

logFile="/var/log/ripeda_setup.log"
dock_mode="--overwrite"

echo "###############################" >> "$logFile"
echo "Initializing Dock Configuration" >> "$logFile"
echo "###############################" >> "$logFile"

# MARK: Populate base information on current user
# -----------------------------------------------
currentUser=$( echo "show State:/Users/ConsoleUser" | scutil | awk '/Name :/ { print $3 }' )
uid=$(id -u "${currentUser}")

echo "Current User: $currentUser (UID: $uid)" >> "$logFile"

# Check first argument for dock mode
if [[ "${applications[1]}" == "--overwrite" ]]; then
    dock_mode="--overwrite"
    applications=("${applications[@]:1}")
elif [[ "${applications[1]}" == "--append" ]]; then
    dock_mode="--append"
    applications=("${applications[@]:1}")
fi

echo "Dock Mode: $dock_mode" >> "$logFile"

# MARK: Internal Functions
# ------------------------

# Ensure regardless of parent ownership, this script is run as the intended user
_runAsUser() {
	if [[ "${currentUser}" != "loginwindow" ]]; then
		launchctl asuser "$uid" sudo -u "${currentUser}" "$@"
	else
		echo "No user logged in, exiting..." >> "$logFile"
		exit 1
	fi
}

# Locate provided application
_locate_application() {
    local searchPath

    searchPath=(
        "/Applications"
        "/Applications/Utilities"
        "/System/Applications"
        "/System/Applications/Utilities"
        "/Users/$currentUser/Applications"
    )

    for path in "${searchPath[@]}"; do
        if [[ -L "$path/$1.app" ]]; then
            local app="$(/usr/bin/readlink "$path/$1.app")"
            if [[ "$app" == ../* ]]; then
                printf "${app:2}"
            fi
            return
        elif [[ -d "$path/$1.app" ]]; then
            printf "$path/$1.app"
            return
        fi
    done

    printf "/Applications/$1.app"
}

# Check if item is already in the dock
_is_item_in_dock_already() {
    local result
    local item="$1"

    # If there's spaces in the path, replace them with %20
    item="${item// /%20}"

    result="$(_runAsUser defaults read com.apple.dock persistent-apps | grep -c "$item")"
    if [[ "$result" -gt 0 ]]; then
        printf "true"
        return
    fi

    printf "false"
}

# com.apple.dock formatting
_dock_item() {
    printf '%s%s%s%s%s' \
           '<dict><key>tile-data</key><dict><key>file-data</key><dict>' \
           '<key>_CFURLString</key><string>' \
           "$1" \
           '</string><key>_CFURLStringType</key><integer>0</integer>' \
           '</dict></dict></dict>'
}

# MARK: Main
# ----------

# Clear out the dock
if [[ "$dock_mode" == "--overwrite" ]]; then
    echo "Clearing out the dock" >> $logFile
    _runAsUser defaults write com.apple.dock persistent-apps -array
fi

# Iterate through the arguments and add them to the dock
for app in "${applications[@]}"; do
    app_path=$app
    if [[ ! "$app" =~ \.app$ ]]; then
        app_path="$(_locate_application "$app")"
    fi

    if [[ "$(_is_item_in_dock_already "$app_path")" == "true" ]]; then
        echo "$app_path is already in the dock, skipping" >> $logFile
        continue
    fi

    echo "Adding $app_path to the dock" >> $logFile

    _runAsUser defaults write com.apple.dock \
                persistent-apps -array-add \
                    "$(_dock_item $app_path)"
done

# Restart the dock
killall Dock