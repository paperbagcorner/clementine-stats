#!/usr/bin/python

# This script queries the clementine database and print how many songs
# which have been played each month. It's a more efficient alternative to
# for i in {0..32}; do month=$(playedinmonth $(date --date "2013-02-01 + $i month" +'%Y-%m')); printf "%64s\n" "$month"; done


import os
import sqlite3

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# The location of the database file.
DB_FILE = os.path.join(os.environ['HOME'], '.config/Clementine/clementine.db')


def GetDataFromDb(filename):
    '''
    Opens the database file filename and performs the query.

    Args:
      filename: a string with a valid filename to an existing
                Clementine database.'
    Returns:
      A list of sqlrows where the elements can be referenced by name.
    '''
    # Create the database connection
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    # Get the data.
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT "
                    "strftime('%Y-%m', lastplayed, 'unixepoch') as month, "
                    "Count(*) as num_songs, "
                    "Sum(length) / 1000000000 as length_secs "  # Nanoseconds
                                                                # in db.
                    "FROM songs WHERE unavailable = 0 "
                    "GROUP BY strftime('%Y-%m', lastplayed, 'unixepoch') "
                    "ORDER BY lastplayed")

        stats = cur.fetchall()
    # conn.close()

    return stats

def BuildResultList(stats):
    '''
    Constructs a list of dictionaries from the sqlrows returned by
    GetDataFromDb and adds entries for those months for which there was no
    last played songs.

    Args:
      stats: A list of sqlrows.
    Returns:
      A list of dictionaries where all months from the first
      month in the result from the db query until today is present event if
      no songs where last played during certain months.
    '''

    # Since we don't get any results from the database for the months
    # where no songs were last played, we need to create these manually.
    month = datetime.strptime(stats[0]['month'], '%Y-%m')
    today = datetime.today()
    month_list = []
    i = 0
    while month <= today:
        row = {}
        month_str = datetime.strftime(month, '%Y-%m')
        if stats[i]['month'] == month_str:
            row['month'] = stats[i]['month']
            row['num_songs'] = stats[i]['num_songs']
            row['length_sec'] = stats[i]['length_secs']
            i += 1
        else:
            row['month'] = month_str
            row['num_songs'] = 0
            row['length_sec'] = 0
        month_list.append(row)

        month = month + relativedelta(months=+1)

    return month_list

    # for stat in stats:
    #     months[stat['month']] = stat['num_songs']
    # return months

def PrintResultList(a_list):
    '''
    Prints a nicely formatted list of the result.

    Args:
      a_list: A list of dictionaries which has the keys month, num_songs
              and length_sec.
    Returns:
      None
    '''
    for row in a_list:
        print('{:>4} songs last played in {}. Total length: {}'.format(
            row['num_songs'],
            row['month'],
            timedelta(seconds=row['length_sec'])))

def main():
    stats = GetDataFromDb(DB_FILE)
    months = BuildResultList(stats)
    PrintResultList(months)

if __name__ == '__main__':
    main()
