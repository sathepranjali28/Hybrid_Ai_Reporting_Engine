"""Tests for the anomaly rule in Src/engine_predict.py."""
import pandas as pd

from engine_predict import _iqr_flags


def test_iqr_flags_the_outlier():
    values = pd.Series([10, 11, 10, 12, 11, 10, 11, 500])
    flags = _iqr_flags(values)
    assert flags.tolist() == [False] * 7 + [True]


def test_iqr_flags_nothing_in_flat_data():
    assert not _iqr_flags(pd.Series([5, 5, 5, 5, 5])).any()
