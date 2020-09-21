# Seattle ACS KMZ Creator

## Introduction

This package is meant to do two things:

1. Process CSV files generated from spreadsheets in the Seattle ACS shared Google drive and generate KML/KMZ files from those data points.
1. (Not implemented yet) Take other KML/KMZ files and combine them into one combined file.

For some folks, creating a KML/KMZ is easier than updating the spreadsheet, and for other folks vice versa. This tool is intended to support both use cases.

## Minimum Python version

I know this needs at least 3.6 to run, but I've only personally tested 3.8.5.

## Usage

The help is still a work in progress, but this package includes everything you should need to get setup.

1. Clone this repository
1. `cd acs_kmz_processor`
1. Create a venv: `virtualenv venv`
1. Activate it: `. venv/bin/activate`
1. pip install this package: `pip install --editable .`
1. Then you should be able to run the script: `kmz_processor --help`

## Example command:
`kmz_processor -m members.csv -r repeaters.csv -w Winlink.csv -a Assembly\ points.csv -d "Seattle ACS NW Map" -i seattle_acs_nw_map -o seattle_acs_nw.kmz`