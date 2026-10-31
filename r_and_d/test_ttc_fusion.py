import pytest

from ttc_fusion import AlphaBetaTtcFilter, TtcMeasurement


def test_filter_tracks_a_linear_ttc_trend():
    estimator = AlphaBetaTtcFilter()
    values = [estimator.update(TtcMeasurement(index * .1, 5. - index * .2)) for index in range(20)]
    assert values[-1] < values[0]


def test_invalid_measurement_resets_state():
    estimator = AlphaBetaTtcFilter()
    estimator.update(TtcMeasurement(0., 5.))
    assert estimator.update(TtcMeasurement(.1, -1.)) is None
    assert estimator.update(TtcMeasurement(.2, 3.)) == 3.


@pytest.mark.parametrize('kwargs', [dict(alpha=0.), dict(beta=0.), dict(max_residual=0.)])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        AlphaBetaTtcFilter(**kwargs)
