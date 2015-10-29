#!/usr/bin/python

# This script queries the clementine database and print how many songs
# which have been played each month. It's a more efficient alternative to
# for i in {0..32}; do month=$(playedinmonth $(date --date "2013-02-01 + $i month" +'%Y-%m')); printf "%64s\n" "$month"; done


import os
import sqlite3

from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta

# The location of the database file.
DB_FILE = os.path.join(os.environ['HOME'], '.config/Clementine/clementine.db')

# Create the database connection
conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row

# Get the data.
cur = conn.cursor()
cur.execute("SELECT strftime('%Y-%m', lastplayed, 'unixepoch') as month, "
            "Count(*) as num_songs "
            "FROM songs WHERE unavailable = 0 "
            "GROUP BY strftime('%Y-%m', lastplayed, 'unixepoch') "
            "ORDER BY lastplayed")

stats = cur.fetchall()
conn.close()

# Since we don't get any results from the database for the months
# where no songs were last played, we create an ordered dict which
# months as keys and the number of songs played as values. We
# initialise all values to zeros and then fill in the non-zero entries
# from the query result.
months = OrderedDict()
month = datetime.strptime(stats[0]['month'], '%Y-%m')
today = datetime.today()
while month <= today:
    months[datetime.strftime(month, '%Y-%m')] = 0
    month = month + relativedelta(months=+1)

for stat in stats:
    months[stat['month']] = stat['num_songs']

# Print the result
for month in months:
    print('{:>4} songs last played in {}.'.format(months[month], month))
