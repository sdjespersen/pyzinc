import io
import logging
import pandas as pd
import re

from collections import OrderedDict
from pandas.api.types import CategoricalDtype
from typing import Any, Dict


DEFAULT_TZ = 'Los_Angeles'

NEWLINE_PATTERN = re.compile(r'\r?\n')

ID_COLTAG = "id"
UNIT_COLTAG = "unit"
KIND_COLTAG = "kind"
ENUM_COLTAG = "enum"

NUMBER_KIND = "Number"
STRING_KIND = "Str"

# We don't want to be in the business of maintaining this list; it's solely for
# heuristically inferring the unit type of a series that didn't come along with
# some metadata.
NUMERIC_UNIT_SUFFIXES = ("°F", "°C", "%", "cfm", "kW")

NUMERIC_TAGS = ('curVal', 'precision', 'writeLevel', 'writeVal')


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
    column_info = _parse_zinc_header(splits[1])
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
    column_info = OrderedDict()  # type: OrderedDict[str, Dict[str, Any]]
    for col in _split_columns(header):
        toks = _tokenize_column(col)
        colname, v = next(toks)
        assert v == MARKER
        column_info[colname] = {}
        for k, v in toks:
            if v is MARKER:
                column_info[colname][k] = v
            else:
                v = v.strip('"')
                if v.startswith('@'):
                    # this is a ref
                    refid, refname = v.split(' ', maxsplit=1)
                    column_info[colname][k] = (refid, refname.strip('"'))
                else:
                    column_info[colname][k] = v
        # now that we have all the info, we can parse relevant values
        unit = column_info[colname].get(UNIT_COLTAG, None)
        for tag in NUMERIC_TAGS:
            if tag in column_info[colname]:
                if unit is not None:
                    val = column_info[colname][tag]
                    column_info[colname][tag] = float(val.rstrip(unit))
    return column_info


def _split_columns(s):
    i, j = -1, 0
    inside_quotes = False
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 1
        elif c == '"':
            inside_quotes = not inside_quotes
        elif c == "," and not inside_quotes:
            yield s[i+1:j]
            i = j
        j += 1
    # don't forget the last one!
    yield s[i+1:j]


def _tokenize_column(s):
    i, j = -1, 0
    inside_quotes, inside_ref = False, False
    tag = None
    while j < len(s):
        c = s[j]
        if c == "\\":
            # always skip escaped chars
            j += 1
        elif tag is None:
            # we are tokenizing a tag
            if c == ':':
                # tag with nontrivial value found
                tag = s[i+1:j]
                i = j
                # lookahead to see if ref
                if s[j+1] == '@':
                    j += 1
                    inside_ref = True
            elif c == " ":
                # this is a marker tag; immediately yield
                yield s[i+1:j], MARKER
                i = j
        else:
            # we are tokenizing a value
            if c == '"' and inside_quotes and inside_ref:
                # this is the end of a ref!
                j += 1
                assert j == len(s) or s[j] == " "
                yield tag, s[i+1:j]
                i = j
                tag = None
                inside_quotes, inside_ref = False, False
            elif c == '"':
                # this is a normal quote
                inside_quotes = not inside_quotes
            elif c == " " and not (inside_quotes or inside_ref):
                # found a legit value
                yield tag, s[i+1:j]
                i = j
                tag = None
        j += 1
    # we've reached the end of the string
    if tag is None:
        yield s[i+1:j], MARKER
    else:
        yield tag, s[i+1:j]


def _sanitize_zinc_series(
        series: pd.Series, colinfo: Dict[str, Any]) -> pd.Series:
    if colinfo:
        kind = colinfo[KIND_COLTAG]
        if kind == NUMBER_KIND:
            if UNIT_COLTAG in colinfo:
                # Now we should be able to safely strip units
                # Parse as numeric type
                unitless = series.str.rstrip(colinfo[UNIT_COLTAG])
                return pd.to_numeric(unitless)
            else:
                return series
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
    return series


def _set_datetime_index(data, colinfo):
    tz = colinfo.get('tz', DEFAULT_TZ)
    data.index = pd.DatetimeIndex(data[0].str.rstrip(tz).str.rstrip())
    data.index.name = 'ts'
    data.drop([0], axis=1, inplace=True)
