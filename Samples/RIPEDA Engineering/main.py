import os
import baseline

os.chdir(os.path.dirname(os.path.abspath(__file__)))

baseline_obj = baseline.BaselineBuilder(
    configuration_file="Configuration/ripeda.plist",
    identifier="com.ripeda.baseline.engineering",
    version="1.0.0",
    output="RIPEDA Engineering Baseline.pkg",
)

if baseline_obj.build() is False:
    raise Exception("Build failed")