# AlmaToBannerParser
This program takes an Alma XML invoice export file and parses the data into a csv
file that can be imported by Banner.  Variables are normally named after the xml
tag in the Alma export for convenient referencing.  All default  directory paths
are set to the current directory, so if this script is run in the same directory
as the Alma xml file, then all output (logs, backups and the csv file) will be
saved to that same directory. Variables are provided for setting different file
paths as you see fit.  This program may need to be modified to fit your
institution's needs.  It is advised that you work with your Banner analysts and
programmers to determine what the csv output should look like for importing into
Banner.  Logging functionality is built into the script for troubleshooting
purposes.
