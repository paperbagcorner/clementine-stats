import unittest

import monthlysummary as ms

class TestGetDataFromDb(unittest.TestCase):
    def setUp(self):
        self.result = ms.GetDataFromDb('testdata/test.db')

    def test_read_rows(self):
        self.assertTrue(len(self.result) > 0)

    def test_has_keys(self):
        keys = self.result[0].keys()
        self.assertTrue(len(keys) > 0)
        self.assertIn('month', keys)
        self.assertIn('num_songs', keys)
        self.assertIn('length_secs', keys)


class TestBuildResultList(unittest.TestCase):
    def setUp(self):
        self.stats = ms.GetDataFromDb('testdata/test.db')
        self.result = ms.BuildResultList(self.stats)

    def test_no_unplayed_songs_in_stats(self):
        # Check that we don't include non-played songs in the result
        # list. These have a lastplayed value of -1 in the database,
        # which is reported to us the month 1969-12.
        unplayed_songs = [x for x in self.result if x['month'] == '1969-12']
        self.assertEqual(len(unplayed_songs), 0)

    def test_result_should_be_at_least_as_long_as_stats(self):
        self.assertTrue(len(self.result) >= len(self.stats))
