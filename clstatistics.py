#!/usr/bin/python3

# This program print statistics of the Clementine music collection.

import argparse
import datetime
import dateutil.parser
import os
import sqlite3

# This is the default location of the database file on linux
# systems. Change it if needed.
DB_FILE = os.path.join(os.environ['HOME'], '.config/Clementine/clementine.db')

class ClementineDb():
    """This class opens and closes the clementine database and implements
    and executes selected queries.
    """

    def __init__(self, filename):
        """Connects to the database specified by the parameter 'filename'.
        """

        # Create the connection
        self.connection = sqlite3.connect(filename)
        self.connection.row_factory = sqlite3.Row

        # This dictionary will hold the number of songs and artists
        # and total play time.
        self.statistics_dict = {}

        # This dictionary will contain the elements 'date', 'before',
        # 'after'. The values are a unix timestamp and the number of
        # songs played before and after this time respectively.
        self.time_partition_dict = {}

        # This list will contain a list of sqlite3 rows
        # of the songs played in a certain time period.
        self.songs_played = []

        # This will contain a tuple of strings representing dates.
        self.date = None

    def __enter__(self):
        """ This function returns the object.
        """
        return self

    def __exit__(self,exception_type, exception_val, trace):
        """ Closes the database connection.
        """
        if self.connection:
            self.connection.close()


    def get_statistics(self):
        """Queries the database for the number of songs,
        number of albums, total play time and last played song.
        """
        cur = self.connection.cursor()

        # Get the number of (available) songs.
        cur.execute("SELECT COUNT(*) FROM songs WHERE unavailable=0")
        self.statistics_dict['number_of_songs'] = cur.fetchone()[0]

        # Get the number of albums.
        cur.execute("SELECT COUNT(DISTINCT album) FROM songs "
                    "WHERE unavailable=0")
        self.statistics_dict['number_of_albums'] = cur.fetchone()[0]

        # Get the number of artists.
        cur.execute("SELECT COUNT(DISTINCT artist) FROM songs "
                    "WHERE unavailable=0")
        self.statistics_dict['number_of_artists'] = cur.fetchone()[0]

        # Get the number of genres.
        cur.execute("SELECT Count(DISTINCT genre) FROM songs "
                    "WHERE unavailable=0")
        self.statistics_dict['number_of_genres'] = cur.fetchone()[0]

        # Get the total play time.
        cur.execute("SELECT Total(length) FROM songs WHERE unavailable=0")
        total_time_in_nsecs = cur.fetchone()[0]
        # Convert the result to microseconds and turn it into a
        # human-readable string.
        total_time_in_usecs = total_time_in_nsecs / 1000
        self.statistics_dict['total_play_time_str'] = \
                str(datetime.timedelta(
                microseconds=total_time_in_usecs))

        # Get the title, artist and timestamp of the last played song.
        cur.execute("SELECT artist, title, lastplayed "
                    "FROM songs "
                    " WHERE unavailable = 0 "
                    "ORDER BY lastplayed DESC "
                    "LIMIT 1")
        last_played_song = cur.fetchone()
        self.statistics_dict['last_played_title'] = \
            last_played_song['title']
        self.statistics_dict['last_played_artist'] = \
            last_played_song['artist']
        self.statistics_dict['last_played_time'] = \
            datetime.datetime.fromtimestamp(
                last_played_song['lastplayed']).strftime("%Y-%m-%d %H:%M")

    def print_statistics(self):
        """ This function prints the statistics gathered to the shell.
        """
        print(("%d songs on %d albums by %d different artists "
            "spread on %d genres." %
            (self.statistics_dict['number_of_songs'],
             self.statistics_dict['number_of_albums'],
             self.statistics_dict['number_of_artists'],
             self.statistics_dict['number_of_genres']
            )))
        print("The total play time of the collection is %s." % \
            (self.statistics_dict['total_play_time_str']))
        print("The last song played was %s by %s at %s." % \
            (self.statistics_dict['last_played_title'],
             self.statistics_dict['last_played_artist'],
             self.statistics_dict['last_played_time']))

    def partition_songs(self, split_date):
        """Splits the number of songs played into two partions: The
        variable 'before' holds the number of songs played before
        the given time. The variable 'after' holds the number of
        songs played after the given time.

        Parameter: split_date (integer) is a unix timestamp.

        """
        cur = self.connection.cursor()
        if split_date != None:
            # Put the parameter into a 1-tuple so that it can be used in
            # the sql query.
            when = (split_date,)

            # Get the number of songs played before the date.
            cur.execute('SELECT Count(*) FROM songs '
                        'WHERE lastplayed < ? AND unavailable=0',
                        when
                    )
            number_of_songs_played_before_date = cur.fetchone()[0]

            # Get the number of songs played after the date.
            cur.execute('SELECT Count(*) FROM songs '
                        'WHERE lastplayed >= ? AND unavailable=0',
                        when
                    )
            number_of_songs_played_after_date = cur.fetchone()[0]

            # Populate self.time_partition_dict with these values.
            self.time_partition_dict['date'] = split_date
            self.time_partition_dict['before'] = (
                number_of_songs_played_before_date
            )
            self.time_partition_dict['after'] = (
                number_of_songs_played_after_date
            )

    def print_partitions(self):
        """
        Print the number of songs played before and after the
        date 'date' in self.time_partition_dict.

        """

        if not self.time_partition_dict:
            return

        split_date_str = datetime.datetime.fromtimestamp(
            self.time_partition_dict['date']).strftime(
                "%Y-%m-%d %H:%M")
        print("There are %d songs played before %s." % \
            (self.time_partition_dict['before'], split_date_str))
        print("There are %d songs played after %s." % \
            (self.time_partition_dict['after'], split_date_str))

    def get_songs_played_on_interval(self, when):
        """Queries for a list of all songs that were played on the
        date interval given in the tuple when in a unix timestamp
        format. The list is stored in the list self.song_list.

        """

        # Query the database.
        cur = self.connection.cursor()
        cur.execute(
            "SELECT artist, title, "
            "datetime(lastplayed, 'unixepoch', 'localtime') "
            "AS 'last played', "
            "length "
            "FROM songs "
            "WHERE lastplayed BETWEEN ? "
            "AND ? "
            "AND unavailable = 0 "
            "ORDER BY lastplayed",
            when
        )
        self.songs_played = cur.fetchall()

        # Store the dates as a string.
        self.date = (
            datetime.datetime.fromtimestamp(
                when[0]).strftime("%Y-%m-%d %H:%M"),
            datetime.datetime.fromtimestamp(
                when[1]).strftime("%Y-%m-%d %H:%M")
        )

    def compute_total_play_time_of_songs_played(self):
        """Queries the database and computes the total play time for all songs
        that has been read into self.songs_played. The result is
        returned as a human readable string.

        """

        # Sum the length of all tracks, convert it into microseconds
        # and turn it into a human readable format.
        play_time_nsec = sum(row["length"] for row in self.songs_played)
        play_time_usec = play_time_nsec / 1000
        play_time_str = str(datetime.timedelta(microseconds=play_time_usec))

        return play_time_str

    def print_song_list(self):
        """ Prints the list of songs in self.songs_played."""

        # Print headers
        print()
        print("{:<30} {:<30} {:<20}".format(
            "artist", "title", "last played"
        ))
        print("{0:-<30} {0:-<30} {0:-<20}".format(""))
        # Print list
        for row in self.songs_played:
            print("{:<30} {:<30} {:<20}".format(
                row["artist"][:30], row["title"][:30], row["last played"]
            ))
        # Print total number of songs.
        number_of_songs = len(self.songs_played)
        play_time_str = self.compute_total_play_time_of_songs_played()
        print()
        print("{} songs played between {} and {}."\
            .format(number_of_songs, self.date[0], self.date[1]))
        print("The total play time is {}.".format(play_time_str))

def get_timestamp(args):
    '''Reads the argument list and converts the first argument that can be
    interperted as a date or time into the unix timestamp format. This
    is then returned. If no valid argument is found, None is returned
    instead.

    TODO: The command line switches are changed so that they now only
    support one argument. We can probably enable fuzzy matching now.
    '''
    for argument in args:
        try:
            dt_obj = dateutil.parser.parse(argument)
        except (TypeError, ValueError):
            pass
        else:
            time_posix = dt_obj.strftime('%s')
            return int(time_posix) # Return as an integer.


def main():
    # Usage: No arguments give basic statistics. A datetime as an
    # argument gives basic statistics and the number of songs played
    # before and after the given date. The switches -f (--from) and -t
    # (--to) DATE gives a list of the songs played on the date
    # interval given.

    # Parse the commandline.
    parser = argparse.ArgumentParser(
        description = "Print statistics of the clementine database.")
    parser.add_argument(
        '-s', '--split',
        nargs = 1,
        help = ('List how many songs that has been played before '
                'and after the given date.'),
        metavar = 'DATE',
        action = 'store'
    )
    list_group = parser.add_argument_group(
        'List songs',
        'Print the songs played between the --from date and the --to date. '
        'If only one of the arguments is given, print either the interval '
        '[--from, --from + 1 day] or [--to - 1 day, --to].'
        )
    list_group.add_argument(
        '-f', '--from',
        nargs = 1,
        help = 'Start date',
        metavar = 'DATE',
        action = 'store',
        dest = 'from_' # This is needed because 'from' is a python keyword.
    )
    list_group.add_argument(
        '-t', '--to',
        nargs = 1,
        help = 'End date',
        metavar = 'DATE',
        action = 'store',
    )

    args = parser.parse_args()

    # Create the database connection.
    with ClementineDb(DB_FILE) as conn:

        # Load the statics from the database and print it.
        conn.get_statistics()
        conn.print_statistics()

        # If the command line options '--from' and/or '--to' is given,
        # print a list of songs that were played in the interval
        # --from - --to. If one of the arguments is missing, print the
        # interval --from - --from + 1 day och --to - 1 day - --to.
        if args.from_:
            start_date = get_timestamp(args.from_)
            if start_date != None: # Do nothing on an invalid date.
                if args.to:
                    end_date = get_timestamp(args.to)
                else:
                    end_date = start_date + 86400 # +1 day
                if end_date != None: # Do nothing on an invalid date.
                    when = (start_date, end_date)
                    conn.get_songs_played_on_interval(when)
                    conn.print_song_list()
        elif args.to:
            # Only the end date has been given. Print the interval
            # [end date - 1 day, end date].
            end_date = get_timestamp(args.to)
            if end_date != None: # Do nothing on an invalid date.
                start_date = end_date - 86400 # -1 day
                when = (start_date, end_date)
                conn.get_songs_played_on_interval(when)
                conn.print_song_list()

        # If the command line option '--split' was given, print the
        # number of songs that were played before and after the
        # supplied date.
        if args.split:
            date = get_timestamp(args.split)
            if date != None: # Do nothing on an invalid date.
                conn.partition_songs(date)
                conn.print_partitions()

# Run the program. (Use C-u C-c C-c to run main from within emacs.)
if __name__ == '__main__':
    main()
