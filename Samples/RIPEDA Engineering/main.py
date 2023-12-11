import os
import logging
import baseline

os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(filename)-22s] [%(levelname)-8s] [%(lineno)-3d]: %(message)s",
    handlers=[logging.StreamHandler()]
)

for variant in ["plist", "mobileconfig"]:
    baseline_obj = baseline.BaselineBuilder(
        configuration_file=f"Configuration/ripeda.{variant}",
        identifier="com.ripeda.baseline.engineering",
        version="1.0.0",
        output="RIPEDA Engineering Baseline.pkg",
    )

    baseline_obj.build()
    baseline_obj.validate_pkg()