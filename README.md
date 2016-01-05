# clementine-stats
This is a collection of scripts to get statistics from your [Clementine](https://clementine-player.org/) database.

## Requirements
* python3

The location of the database is set in the variable `DB_FILE`. Currently, it is set to the default database location on linux systems. Change it if needed.

### monthlystatistics.py
This script prints a summary of the number of songs played together and the total play time grouped by month.

### clstatistics.py
This script allows you to query the database for songs played in a given date range. It will also print a summary of the number of songs in the database.
