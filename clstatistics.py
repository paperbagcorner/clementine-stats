#!/usr/bin/python2

# This program print statistics of the Clementine music collection.
import sys
import sqlite3
import datetime
import dateutil.parser


# The location of the database file.
db_file = '/home/mattias/.config/Clementine/clementine.db'

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

        # Create an empty dictionary. This dictionary will hold the
        # number of songs and artists and total play time.
        self.statistics_dict = {}

        # This dictionary will contain the elements 'date', 'before',
        # 'after'. The values are a unix timestamp and the number of
        # songs played before and after this time respectively.
        self.time_partition_dict = {}


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

            print self.time_partition_dict # Debug

    def print_partitions(self):
        """
        Print the number of songs played before and after the
        date vien in self.time_partition_dict.

        """
        # Do nothing if time_partition_dict is empty.
        if not self.time_partition_dict:
            return

        split_date_str = datetime.datetime.fromtimestamp(
            float(self.time_partition_dict['date'])).strftime(
                "%Y-%m-%d %H:%M")
        print "There are %d songs played before %s." % \
            (self.time_partition_dict['before'], split_date_str)
        print "There are %d songs played after %s." % \
            (self.time_partition_dict['after'], split_date_str)


def get_timestamp_from_command_line(argv):
    '''Reads the command line and converts the first argument that can be
    interperted as a date or time into the unix timestamp format. This
    is then returned. If no valid argument is found, None is returned
    instead. The function returns the timestamp as a 'str'.
    '''
    for argument in argv:
        try:
            dt_obj = dateutil.parser.parse(argument)
        except TypeError:
            pass
        else:
            time_posix = dt_obj.strftime('%s')
            return time_posix


def main():
    # Create the database connection.
    with ClementineDb(db_file) as conn:

        # Load the statics from the database.
        conn.get_statistics()

        # Print the statiscs.
        conn.print_statistics()

        # If there is a command line argument that can be interpreted as a
        # date, get the number of songs that has been played before (<)
        # this date and the number of songs that has been played after
        # (>=) this date.
        split_date = get_timestamp_from_command_line(sys.argv)
        # split_date = 1385167257 # Debug value, remove this later.

        # Split the number of songs in two, where the split point is
        # given by split_date.
        conn.partition_songs(split_date)

        # Print info on the number of songs played before and after
        # the cutoff-date.
        conn.print_partitions()

main()
