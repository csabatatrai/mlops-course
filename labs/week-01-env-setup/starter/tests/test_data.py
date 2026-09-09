import pytest

from week_01_env_setup.config import load_settings
from week_01_env_setup.data import build_dataset, load_dataframe


def test_split_ratios() -> None:
    """Verify the train/test split."""
    settings = load_settings()
    frame = load_dataframe(settings)
    x_train, x_test, _y_train, _y_test = build_dataset(settings)

    assert len(x_train) + len(x_test) == len(frame)

    actual_test_fraction = len(x_test) / len(frame)
    assert actual_test_fraction == pytest.approx(settings.test_size, abs=0.01)
