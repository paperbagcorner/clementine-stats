#!/usr/bin/python2

# This program print statistics of the Clementine music collection.
import argparse
import datetime
import dateutil.parser
import sqlite3

# The location of the database file.
DB_FILE = '/home/mattias/.config/Clementine/clementine.db'

class ClementineDb():
    """This class opens and closes the clementine database and implements
    and executes selected queries.
    """

    def __init__(self, filename):
        """Connects to the database specified by the parameter 'filename'.
        """
        #print 'ClementineDb::__init__'

        # Create the connection
        self.connection = sqlite3.connect(filename)
        self.connection.row_factory = sqlite3.Row

        # Create an empty dictionary. This dictionary will hold the
        # number of songs and artists and total play time.
        self.statistics_dict = {}

        # This dictionary will contain the elements 'date', 'before',
        # 'after'. The values are a unix timestamp and the number of
        # songs played before and after this time respectively.
        self.time_partition_dict = {}

        # This list will contain a list of sqlite3 rows
        # of the songs played in a certain time period.
        self.songs_played = []

        # This will contain a string representing a date.
        self.date = None

    def __enter__(self):
        """ This function returns the object.
        """
        #print 'ClementineDb::__enter__'
        return self

    def __exit__(self,exception_type, exception_val, trace):
        """ Closes the database connection.
        """
        #print 'ClementineDb::__exit__'
        # Close the connection if it was created.
        if self.connection:
            self.connection.close()


    def get_statistics(self):
        """This function queries the database for the number of songs,
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

        # Get the total play time
        cur.execute("SELECT Total(length) FROM songs WHERE unavailable=0")
        total_time_in_nanoseconds = cur.fetchone()[0]
        # Convert the result to microseconds and turn it into a
        # human-readable string.
        total_time_in_microseconds = total_time_in_nanoseconds / 1000
        self.statistics_dict['total_play_time_str'] = \
                str(datetime.timedelta(
                microseconds=total_time_in_microseconds))

        # Get the title, artist and timestamp of the last played song.
        cur.execute("SELECT title, artist, max(lastplayed) from songs "
                    "WHERE unavailable = 0")
        last_played_song = cur.fetchone()
        self.statistics_dict['last_played_title'] = last_played_song[0]
        self.statistics_dict['last_played_artist'] = last_played_song[1]
        self.statistics_dict['last_played_time'] = \
            datetime.datetime.fromtimestamp(
                last_played_song[2]).strftime("%Y-%m-%d %H:%M")

        # Debug row. It prints the dictionary.
        # print self.statistics_dict

    def print_statistics(self):
        """ This function prints the statistics gathered to the shell.
        """
        print "%d songs on %d albums by %d different artists." % \
            (self.statistics_dict['number_of_songs'],
             self.statistics_dict['number_of_albums'],
             self.statistics_dict['number_of_artists']
            )
        print "The total play time of the collection is %s." % \
            (self.statistics_dict['total_play_time_str'])
        print "The last song played was %s by %s at %s." % \
            (self.statistics_dict['last_played_title'],
             self.statistics_dict['last_played_artist'],
             self.statistics_dict['last_played_time'])

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
        # Do nothing if time_partition_dict is empty.
        if not self.time_partition_dict:
            return

        split_date_str = datetime.datetime.fromtimestamp(
            self.time_partition_dict['date']).strftime(
                "%Y-%m-%d %H:%M")
        print "There are %d songs played before %s." % \
            (self.time_partition_dict['before'], split_date_str)
        print "There are %d songs played after %s." % \
            (self.time_partition_dict['after'], split_date_str)

    def get_songs_played_on(self, date):
        """Queries for a list of all songs that were played on the date
        'date' and one day forward. The list is stored in the list
        self.song_list.

        """
        # Make a tuple of the date and one day forward.
        when = (date, date + 86400)

        # Query the database.
        cur = self.connection.cursor()
        cur.execute(
            "SELECT artist, title, "
            "datetime(lastplayed, 'unixepoch', 'localtime') "
            "AS 'last played' "
            "FROM songs "
            "WHERE lastplayed BETWEEN ? "
            "AND ? "
            "AND unavailable = 0 "
            " ORDER BY lastplayed",
            when
        )
        self.songs_played = cur.fetchall()

        # Store the date as a string.
        self.date = datetime.datetime.fromtimestamp(
            date).strftime("%Y-%m-%d %H:%M")

    def print_song_list(self):
        """ Prints the list of songs in self.songs_played."""

        # Print headers
        print
        print "{:<30} {:<30} {:<20}".format(
            "artist", "title", "last played"
        )
        print "{0:-<30} {0:-<30} {0:-<20}".format("")
        # Print list
        for row in self.songs_played:
            print u"{:<30} {:<30} {:<20}".format(
                row["artist"][:30], row["title"][:30], row["last played"]
            )
        # Print total number of songs.
        number_of_songs = len(self.songs_played)
        print
        print "The total number of songs last played on {} is {}.".format(
            self.date, number_of_songs
        )


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
    # before and after the given date. The switch -o (--on) and a date
    # gives a list of the songs played on that date.

    # Parse the commandline.
    parser = argparse.ArgumentParser(
        description = "Print statistics of the clementine database.")
    parser.add_argument(
        '-o', '--on',
        nargs = 1,
        help='List all songs that were last played on the given date.',
        action = 'store'
    )
    parser.add_argument(
        '-s', '--split',
        nargs = 1,
        help = ('List how many songs that has been played before '
                'and after the given date.'),
        action = 'store'
    )
    args = parser.parse_args()

    # Create the database connection.
    with ClementineDb(DB_FILE) as conn:

        # Load the statics from the database and print it.
        conn.get_statistics()
        conn.print_statistics()

        # If the command line option '--on' was given, print a list of
        # songs that were played on that day, if not print the number
        # of songs that were played before and after the given date
        # respectively.
        if args.on:
            date = get_timestamp(args.on)
            if date != None: # Do nothing on an invalid date.
                conn.get_songs_played_on(date)
                conn.print_song_list()

        # If the command line option '--split' was given, print the
        # number of songs that were played before and after the
        # supplied date.
        if args.split:
            date = get_timestamp(args.split)
            if date != None: # Do nothing on an invalid date.
                conn.partition_songs(date)
                conn.print_partitions()

main()
