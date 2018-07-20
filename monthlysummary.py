#!/usr/bin/python

# This script queries the clementine database and print how many songs
# which have been played each month.


import os
import sqlite3

from collections import namedtuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Default location of the database file.
DB_FILE = os.path.join(os.environ['HOME'], '.config/Clementine/clementine.db')

# This namedtuple stores the record for a given month.
MonthRecord = namedtuple('MonthRecord', 'month, num_songs, length_secs')


def GetDataFromDb(filename):
    '''
    Opens the database file filename and performs the query.

    Args:
      filename: a string with a valid filename to an existing
                Clementine database.'
    Returns:
      A list of MonthRecords.
    '''
    # Create the database connection
    conn = sqlite3.connect(filename)

    # Get the data.
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT "
                    "strftime('%Y-%m', lastplayed, 'unixepoch') as month, "
                    "Count(*) as num_songs, "
                    "Sum(length) / 1000000000 as length_secs "  # Nanoseconds
                                                                # in db.
                    "FROM songs "
                    "WHERE unavailable = 0 "
                    "AND playcount > 0 "
                    "GROUP BY strftime('%Y-%m', lastplayed, 'unixepoch') "
                    "ORDER BY lastplayed")

        stats = cur.fetchall()
    return [MonthRecord._make(stat) for stat in stats ]

def BuildResultList(stats):
    '''
    Constructs a list of dictionaries from the MonthRecords returned by
    GetDataFromDb and adds entries for those months for which there was no
    played songs.

    Args:
      stats: A list of MonthRecords.
    Returns:
      A list of MonthRecords where all months from the first
      month in the result from the db query until today is present event if
      no songs where last played during certain months.
    '''

    # Since we don't get any results from the database for the months
    # where no songs were last played, we need to insert these manually.
    month = datetime.strptime(stats[0].month, '%Y-%m')
    today = datetime.today()
    month_list = []
    i = 0
    while month <= today:
        month_str = datetime.strftime(month, '%Y-%m')
        if i < len(stats) and stats[i].month == month_str:
            month_list.append(stats[i])
            i += 1
        else:
            month_list.append(MonthRecord(month_str, 0, 0))

        month = month + relativedelta(months=+1)

    return month_list

def PrintResultList(a_list):
    '''
    Prints a nicely formatted list of the result.

    Args:
      a_list: A list of MonthRecords.
    Returns:
      None
    '''
    for row in a_list:
        print('{:>4} songs last played in {}. Total length: {}'.format(
            row.num_songs,
            row.month,
            timedelta(seconds=row.length_secs)))

def main():
    stats = GetDataFromDb(DB_FILE)
    months = BuildResultList(stats)
    PrintResultList(months)

if __name__ == '__main__':
    main()
