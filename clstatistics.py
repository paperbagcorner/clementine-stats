#!/usr/bin/python2

# This program print statistics of the Clementine music collection.
import sys
import sqlite3 
import datetime
import dateutil.parser


# The location of the database file.
db_file = '/home/mattias/.config/Clementine/clementine.db'

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


# Connect to the database.
con = sqlite3.connect(db_file)

with con:
    cur = con.cursor()
    
    # Get the number of (available) songs.
    cur.execute("SELECT COUNT(*) FROM songs WHERE unavailable=0")
    number_of_songs = cur.fetchone()[0]

    # Get the number of albums.
    cur.execute("SELECT COUNT(DISTINCT album) FROM songs WHERE unavailable=0")
    number_of_albums = cur.fetchone()[0]
    # Get the number of artists.
    cur.execute("SELECT COUNT(DISTINCT artist) FROM songs WHERE unavailable=0")
    number_of_artists = cur.fetchone()[0]

    # Get the total play time
    cur.execute("SELECT Total(length) FROM songs WHERE unavailable=0")
    total_time_in_nanoseconds = cur.fetchone()[0]
    # Convert the result to microseconds and turn it into a
    # human-readable string.
    total_time_in_microseconds = total_time_in_nanoseconds / 1000
    total_play_time_str = str(datetime.timedelta(microseconds=total_time_in_microseconds))

    # Get the title, artist and timestamp of the last played song.
    cur.execute("SELECT title, artist, max(lastplayed) from songs WHERE unavailable = 0")
    last_played_song = cur.fetchone()
    last_played_title = last_played_song[0]
    last_played_artist = last_played_song[1]
    last_played_time = datetime.datetime.fromtimestamp(last_played_song[2]).strftime("%Y-%m-%d %H:%M")
    #type(last_played_time)

    # If there is a command line argument that can be interpreted as a
    # date, get the number of songs that has been played before (<)
    # this date and the number of songs that has been played after
    # (>=) this date.
    split_date = get_timestamp_from_command_line(sys.argv)
    if split_date != None:
        # Put the parameter into a 1-tuple so that it can be used in
        # the sql query.
        when = (split_date,)

        # Get the number of songs played before the date.
        cur.execute('SELECT Count(*) FROM songs WHERE lastplayed < ? AND unavailable=0', when)
        number_of_songs_played_before_date = cur.fetchone()[0]
      
        # Get the number of songs played after the date.
        cur.execute('SELECT Count(*) FROM songs WHERE lastplayed >= ? AND unavailable=0', when)
        number_of_songs_played_after_date = cur.fetchone()[0]
      
    # Print the results.
    print "%d songs on %d albums by %d different artists." % \
        (number_of_songs, number_of_albums, number_of_artists)
    print "The total play time of the collection is %s." % (total_play_time_str)
    print "The last song played was %s by %s at %s." % \
        (last_played_title, last_played_artist, last_played_time)

    
    # Print info on the number of songs played before and after the cutoff-date.
    try:
        number_of_songs_played_before_date
    except NameError:
        # If we reached this, no date was supplied on the command
        # line. We shall therefore do nothing.
        pass
    else:
        split_date_str = datetime.datetime.fromtimestamp(float(split_date)).strftime("%Y-%m-%d %H:%M")
        print "There are %d songs played before %s." % \
            (number_of_songs_played_before_date, split_date_str)
        print "There are %d songs played after %s." % \
            (number_of_songs_played_after_date, split_date_str)
