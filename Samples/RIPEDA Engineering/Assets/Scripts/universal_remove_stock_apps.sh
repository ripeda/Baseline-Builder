#!/bin/zsh --no-rcs

# Remove stock applications from OS if available from VPP
# Primarily iLife apps, as clients can associate their own Apple ID to these apps
# Note: Implements exemption for Pro App Bundles (since this is more difficult to restore)

# Source of logic:
# https://github.com/ripeda/VPP-Detection

logFile="/var/log/ripeda_setup.log"
verificationURL="https://buy.itunes.apple.com/verifyReceipt"

echo "##############################" >> "$logFile"
echo "Initializing Stock App Cleaner" >> "$logFile"
echo "##############################" >> "$logFile"


# MARK: - Functions
# -----------------

# Call server to determine receipt type
# Takes applicationReceipt as an argument
__checkServer() {

    local receiptJSON
    local receiptData
    local receiptResponse

    receiptJSON="{\"receipt-data\":\"$(base64 -i "$1")\"}"
    receiptResponse=$(curl -s -X POST --data "$receiptJSON" "$verificationURL")

    # Check if receipt key is missing
    if [[ ! "$receiptResponse" =~ "receipt" ]]; then
        echo 2
        return
    fi

    # Check if receipt_type key is missing
    if [[ ! "$receiptResponse" =~ "receipt_type" ]]; then
        echo 2
        return
    fi

    # Check for 'receipt_type' value
    if [[ "$receiptResponse" =~ "ProductionVPPSandbox" ]]; then
        echo 0
        return
    elif [[ "$receiptResponse" =~ "ProductionVPP" ]]; then
        echo 0
        return
    elif [[ "$receiptResponse" =~ "ProductionSandbox" ]]; then
        echo 1
        return
    elif [[ "$receiptResponse" =~ "Production" ]]; then
        echo 1
        return
    fi

    echo 4
}


# MARK: - Main
# ------------

excludeProApps=("Final Cut Pro" "Logic Pro" "Motion" "Compressor" "MainStage")

for application in /Applications/*.app; do

    applicationReceipt="$application/Contents/_MASReceipt/receipt"
    if [[ ! -f "$applicationReceipt" ]]; then
        continue
    fi

    # Check if application is from VPP
    result=$(__checkServer "$applicationReceipt")
    echo "Application: $application (Result: $result)" >> "$logFile"

    # Remove stock applications
    if [[ "$result" == 2 ]]; then
        # Check if application is excluded
        for excludeProApp in "${excludeProApps[@]}"; do
            if [[ "$application" =~ "$excludeProApp" ]]; then
                echo "  Skipping due to exemption" >> "$logFile"
                continue 2
            fi
        done

        echo "  Removing application: $application" >> "$logFile"
        rm -rf "$application"
    fi

done