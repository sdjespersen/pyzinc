import datetime
import hszinc
import io
import logging
import pandas as pd
import re

from collections import OrderedDict
from pandas.api.types import CategoricalDtype
from typing import Any, Dict, Union


DEFAULT_TZ = 'Los_Angeles'

NEWLINE_PATTERN = re.compile(r'\r?\n')

ID_COLTAG = "id"
UNIT_COLTAG = "unit"
KIND_COLTAG = "kind"
ENUM_COLTAG = "enum"

NUMBER_KIND = "Number"
STRING_KIND = "Str"

NUMERIC_UNIT_SUFFIXES = ("°F", "°C", "%", "cfm", "kW")


class ZincParseException(Exception):
    pass


class MarkerType:
    """Type of the ZINC Marker."""

    def __repr__(self):
        return 'MARKER'


MARKER = MarkerType()


class ZincDataFrame(pd.DataFrame):
    """A tabular data frame for ZINC.

    This is effectively just a pandas.DataFrame, but with added ZINC support,
    namely, `column_info` metadata containing the tags, units, etc. associated
    with each Haystack Point in the frame.

    Constructor: Same as pd.DataFrame, but accepts a 'column_info' kwarg.
    """

    column_info = OrderedDict()

    def __init__(self, *args, **kwargs):
        if 'column_info' in kwargs:
            self.column_info = kwargs.pop('column_info')
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return (f"ZincDataFrame<\n"
                + "column_info: {self.column_info}\n"
                + super().__repr__()
                + ">")


class ZincSeries(pd.Series):
    """A single column of tabular ZINC data.

    This is effectively just a pandas.Series, but with added ZINC support,
    namely, `column_info` metadata containing the tags, units, etc. associated
    with the Haystack Point.

    Constructor: Same as pd.Series, but accepts a 'column_info' kwarg.
    """

    column_info = OrderedDict()

    def __init__(self, *args, **kwargs):
        if 'column_info' in kwargs:
            self.column_info = kwargs.pop('column_info')
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return (f"ZincSeries<\n"
                + "column_info: {self.column_info}\n"
                + super().__repr__()
                + ">")


def zinc_to_frame(zinc: str) -> ZincDataFrame:
    """Converts raw ZINC string to a single ZincDataFrame."""
    splits = re.split(NEWLINE_PATTERN, zinc, maxsplit=2)
    if len(splits) < 2:
        raise ZincParseException("Malformed input")
    column_info = _parse_zinc_header("\n".join(splits[:2]))
    data = None
    if len(splits) == 3:
        # zinc can indicate "null" with "N"; in pandas-land, this
        # is not distinct from "NaN", so we convert
        data = pd.read_csv(
            io.StringIO(splits[2]),
            header=None,
            na_values='N')
        renaming = {}
        for i, (k, v) in enumerate(column_info.items()):
            if i > 0:
                if ID_COLTAG in v:
                    renaming[i] = v[ID_COLTAG][1]
                else:
                    renaming[i] = k
        data.rename(columns=renaming, inplace=True)
        print(f"{data=}")
        for i, col in enumerate(column_info):
            colinfo = column_info[col]
            cname = data.columns[i]
            # i == 0 corresponds to the index; leave until end
            if i > 0:
                data[cname] = _sanitize_zinc_series(data[cname], colinfo)
        _set_datetime_index(data, column_info['ts'])
    return ZincDataFrame(data=data, column_info=column_info)


def zinc_to_series(zinc: str) -> ZincSeries:
    """Converts raw ZINC string to a single ZincSeries."""
    zdf = zinc_to_frame(zinc)
    return ZincSeries(zdf[zdf.columns[0]], column_info=zdf.column_info)


def _parse_zinc_header(header: str) -> Dict[str, Dict[str, Any]]:
    # TODO: Don't use hszinc; write something in-house that's maybe faster
    parsed = hszinc.parse(header)[0]
    colinfo = OrderedDict()  # type: OrderedDict[str, Dict[str, Any]]
    for c, v in parsed.column.items():
        colinfo[c] = {}
        for k, val in v.items():
            colinfo[c][k] = _untype_hszinc_scalar(val)
    return colinfo


def _untype_hszinc_scalar(val: Any) -> Union[str, float]:
    if val is hszinc.MARKER:
        return MARKER
    elif isinstance(val, hszinc.datatypes.Ref):
        return ('@' + val.name, val.value)
    elif isinstance(val, hszinc.datatypes.Quantity):
        return val.value
    elif isinstance(val, datetime.datetime):
        return val.isoformat()
    elif isinstance(val, str) or isinstance(val, float):
        return val
    else:
        raise ValueError(f"{type(val)} with value {val} not understood")


def _sanitize_zinc_series(
        series: pd.Series, colinfo: Dict[str, Any]) -> pd.Series:
    if colinfo:
        kind = colinfo[KIND_COLTAG]
        if kind == NUMBER_KIND:
            # Now we should be able to safely strip units
            unitless = series.str.rstrip(colinfo[UNIT_COLTAG])
            # Parse as numeric type
            return pd.to_numeric(unitless)
        elif ENUM_COLTAG in colinfo:
            cat_type = CategoricalDtype(
                categories=colinfo[ENUM_COLTAG].split(","))
            return series.astype(cat_type)
        elif kind != STRING_KIND:
            raise ZincParseException(f"Unrecognized kind {kind}")
    else:
        logging.debug("No column headers, heuristically inferring type")
        for suffix in NUMERIC_UNIT_SUFFIXES:
            if series[0].endswith(suffix):
                return pd.to_numeric(series.str.rstrip(suffix))


def _set_datetime_index(data, colinfo):
    tz = colinfo.get('tz', DEFAULT_TZ)
    data.index = pd.DatetimeIndex(data[0].str.rstrip(tz).str.rstrip())
    data.index.name = 'ts'
    data.drop([0], axis=1, inplace=True)
