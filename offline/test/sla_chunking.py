import unittest

import numpy as np
import pandas as pd

from offline.time.slagen import chunk_series_as_sla, discretize

now = pd.to_datetime('20000101', format='%Y%m%d')


def date_range(start, end):
    return pd.date_range(now + pd.Timedelta("%dH" % start), now + pd.Timedelta("%dH" % end), freq="1H")


class MyTestCase(unittest.TestCase):
    def test_something(self):

        s0 = pd.Series(np.array([1, 2, 3, 2]), index=date_range(1, 4))
        s1 = pd.Series(np.array([4, 3, 3, 2]), index=date_range(1, 4))
        s2 = pd.Series.add(s0, s1, fill_value=0)

        slas = chunk_series_as_sla({"1": s0, "2": s1})

        s3 = pd.Series()
        for sla in [item for sublist in slas.values() for item in sublist]:
            s3 = pd.Series.add(s3, sla, fill_value=0)

        for i in s0.index:
            self.assertEqual(s2[i], s3[i])

    def test_chunking(self):

        s = {key: pd.Series(np.arange(0, 100), index=date_range(0, 99)) for key in
             np.arange(0, 10)}


        for i in np.arange(1,10):
            tses = {key: discretize(1, i, ts=value, df=value[1], forecast_detector=lambda x: 0) for key, value in s.items()}
            chunked = chunk_series_as_sla(tses)
            self.assertEqual(len(chunked), 10)
            for chunky in chunked.values():
                self.assertEqual(len(chunky), i)


if __name__ == '__main__':
    unittest.main()
