# coding: utf-8
import numpy as np
import os
import pandas as pd
from ..pyzinc import pyzinc

from collections import OrderedDict
from pandas.api.types import CategoricalDtype


TEST_DATAFRAME_FILE = "test_dataframe.zinc"
TEST_SERIES_FILE = "test_series.zinc"
TEST_HISREAD_SERIES_FILE = "test_hisread_series.zinc"


def read_testfile(relpath):
    path = os.path.join(os.path.dirname(__file__), relpath)
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_zinc_to_frame():
    expected_colinfo = OrderedDict(
        ts={
            'disKey': 'ui::timestamp',
            'tz': 'Los_Angeles',
            'chartFormat': 'ka',
        },
        v0={
            'id': ('@p:q01b001:r:0197767d-c51944e4',
                   'Building One VAV1-01 Eff Heat SP'),
            'navName': 'Eff Heat SP',
            'point': pyzinc.MARKER,
            'his': pyzinc.MARKER,
            'siteRef': ('@p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            'equipRef': ('@p:q01b001:r:b78a8dcc-828caa1b',
                         'Building One VAV1-01'),
            'curVal': 65.972,
            'curStatus': 'ok',
            'kind': 'Number',
            'unit': '°F',
            'tz': 'Los_Angeles',
            'sp': pyzinc.MARKER,
            'temp': pyzinc.MARKER,
            'cur': pyzinc.MARKER,
            'haystackPoint': pyzinc.MARKER,
            'air': pyzinc.MARKER,
            'effective': pyzinc.MARKER,
            'heating': pyzinc.MARKER
        },
        v1={
            'id': ('@p:q01b001:r:e69a7401-f4b340ff',
                   'Building One VAV1-01 Eff Occupancy'),
            'navName': 'Eff Occupancy',
            'point': pyzinc.MARKER,
            'his': pyzinc.MARKER,
            'siteRef': ('@p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            'equipRef': ('@p:q01b001:r:b78a8dcc-828caa1b',
                         'Building One VAV1-01'),
            'curVal': 'Occupied',
            'curStatus': 'ok',
            'kind': 'Str',
            'tz': 'Los_Angeles',
            'sensor': pyzinc.MARKER,
            'cur': pyzinc.MARKER,
            'haystackPoint': pyzinc.MARKER,
            'hisCollectCov': pyzinc.MARKER,
            'enum': 'Nul,Occupied,Unoccupied,Bypass,Standby',
            'effective': pyzinc.MARKER,
            'occupied': pyzinc.MARKER},
        v2={
            'id': ('@p:q01b001:r:dcfe87d9-cd034388',
                   'Building One VAV1-01 Damper Pos'),
            'navName': 'Damper Pos',
            'point': pyzinc.MARKER,
            'his': pyzinc.MARKER,
            'siteRef': ('@p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            'equipRef': ('@p:q01b001:r:b78a8dcc-828caa1b',
                         'Building One VAV1-01'),
            'curVal': 41.5,
            'curStatus': 'ok',
            'kind': 'Number',
            'unit': '%',
            'tz': 'Los_Angeles',
            'sensor': pyzinc.MARKER,
            'cur': pyzinc.MARKER,
            'damper': pyzinc.MARKER,
            'precision': 1.0,
            'haystackPoint': pyzinc.MARKER,
            'air': pyzinc.MARKER
        },
        v3={
            'id': ('@p:q01b060:r:8fab195e-58ffca99',
                   'Building One VAV1-01 Occ Heat SP Offset'),
            'navName': 'Occ Heat SP Offset',
            'point': pyzinc.MARKER,
            'his': pyzinc.MARKER,
            'siteRef': ('@p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            'equipRef': ('@p:q01b001:r:b78a8dcc-828caa1b',
                         'Building One VAV1-01'),
            'curVal': -2.394,
            'curStatus': 'ok',
            'kind': 'Number',
            'unit': '°C',
            'tz': 'Los_Angeles',
            'sp': pyzinc.MARKER,
            'temp': pyzinc.MARKER,
            'cur': pyzinc.MARKER,
            'air': pyzinc.MARKER,
            'occ': pyzinc.MARKER,
            'writable': pyzinc.MARKER,
            'writeStatus': 'unknown',
            'zone': pyzinc.MARKER,
            'hisCollectInterval': 5.0,
            'heating': pyzinc.MARKER,
            'offset': pyzinc.MARKER,
            'writeLevel': 8.0,
            'haystackPoint': pyzinc.MARKER,
            'writeVal': -10.0,
            'actions': ('ver:"3.0"\ndis,expr\n"Override","pointOverride($self,'
                        ' $val, $duration)"\n"Auto","pointAuto($self)"\n')
        },
        v4={
            'id': ('@p:q01b060:r:260ce2bb-2ef5065f',
                   'Building One VAV1-01 Air Flow'),
            'navName': 'Air Flow',
            'point': pyzinc.MARKER,
            'his': pyzinc.MARKER,
            'siteRef': ('@p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            'equipRef': ('@p:q01b001:r:b78a8dcc-828caa1b',
                         'Building One VAV1-01'),
            'curVal': 117.6611,
            'curStatus': 'ok',
            'kind': 'Number',
            'unit': 'cfm',
            'tz': 'Los_Angeles',
            'sensor': pyzinc.MARKER,
            'cur': pyzinc.MARKER,
        }
    )

    expected_index = pd.DatetimeIndex(
        [
            pd.to_datetime('2020-05-17T23:47:08-07:00'),
            pd.to_datetime('2020-05-17T23:55:00-07:00'),
            pd.to_datetime('2020-05-18T00:00:00-07:00'),
            pd.to_datetime('2020-05-18T00:05:00-07:00'),
            pd.to_datetime('2020-05-18T01:13:09-07:00'),
        ],
        name='ts')
    expected_dataframe = pd.DataFrame(
        index=expected_index,
        data={
            'Building One VAV1-01 Eff Heat SP': [
                np.nan, 68.553, 68.554, 69.723, np.nan,
            ],
            'Building One VAV1-01 Eff Occupancy': pd.Series(
                ['Occupied', '', '', '', 'Unoccupied'],
                index=expected_index,
                dtype=CategoricalDtype(categories=[
                    'Nul', 'Occupied', 'Unoccupied', 'Bypass', 'Standby'])
            ),
            'Building One VAV1-01 Damper Pos': [np.nan, 3, 7, 18, np.nan],
            'Building One VAV1-01 Occ Heat SP Offset': [
                np.nan, -1.984, -2.203, 5.471, np.nan,
            ],
            'Building One VAV1-01 Air Flow': [
                np.nan, 118.65, 62.0, np.nan, np.nan,
            ],
        })
    actual = pyzinc.zinc_to_frame(read_testfile(TEST_DATAFRAME_FILE))
    expected = pyzinc.ZincDataFrame(
        expected_dataframe, column_info=expected_colinfo)
    assert actual.column_info == expected.column_info
    pd.testing.assert_frame_equal(actual, expected)


def test_zinc_to_series():
    expected_colinfo = OrderedDict(
        ts={
            'disKey': 'ui::timestamp',
            'tz': 'Los_Angeles',
            'chartFormat': 'ka',
        },
        v0={
            'id': ('@p:q01b001:r:0197767d-c51944e4',
                   'Building One VAV1-01 Eff Heat SP'),
            'navName': 'Eff Heat SP',
            'point': pyzinc.MARKER,
            'his': pyzinc.MARKER,
            'siteRef': ('@p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            'equipRef': ('@p:q01b001:r:b78a8dcc-828caa1b',
                         'Building One VAV1-01'),
            'curVal': 65.972,
            'curStatus': 'ok',
            'kind': 'Number',
            'unit': '°F',
            'tz': 'Los_Angeles',
            'sp': pyzinc.MARKER,
            'temp': pyzinc.MARKER,
            'cur': pyzinc.MARKER,
            'haystackPoint': pyzinc.MARKER,
            'air': pyzinc.MARKER,
            'effective': pyzinc.MARKER,
            'heating': pyzinc.MARKER
        },
    )
    expected_series = pd.Series(
        data=[np.nan, 68.553, 68.554, 69.723, np.nan],
        index=pd.DatetimeIndex(
            [
                pd.to_datetime('2020-05-17T23:47:08-07:00'),
                pd.to_datetime('2020-05-17T23:55:00-07:00'),
                pd.to_datetime('2020-05-18T00:00:00-07:00'),
                pd.to_datetime('2020-05-18T00:05:00-07:00'),
                pd.to_datetime('2020-05-18T01:13:09-07:00'),
            ],
            name='ts',
        ),
        name='Building One VAV1-01 Eff Heat SP',
    )
    expected = pyzinc.ZincSeries(expected_series, column_info=expected_colinfo)
    actual = pyzinc.zinc_to_series(read_testfile(TEST_SERIES_FILE))
    assert actual.column_info == expected.column_info
    pd.testing.assert_series_equal(actual, expected)


# WAIT A MINUTE. DOES hisRead REALLY NOT RETURN MORE EXTENSIVE METADATA? IS
# THIS TEST CASE VALID?
def test_hisread_zinc_to_series():
    expected_colinfo = OrderedDict(ts={}, val={})
    expected_series = pd.Series(
        data=[66.09200286865234, 66.00199890136719, 65.93000030517578],
        index=pd.DatetimeIndex(
            [
                pd.to_datetime('2020-04-01T00:00:00-07:00'),
                pd.to_datetime('2020-04-01T00:05:00-07:00'),
                pd.to_datetime('2020-04-01T00:10:00-07:00'),
            ],
            name='ts',
        ),
        name='val',
    )
    expected = pyzinc.ZincSeries(expected_series, column_info=expected_colinfo)
    actual = pyzinc.zinc_to_series(read_testfile(TEST_HISREAD_SERIES_FILE))
    assert actual.column_info == expected.column_info
    pd.testing.assert_series_equal(actual, expected)
