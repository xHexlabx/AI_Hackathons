import pandas as pd
import pytest

from common.seed import seed_everything
from common.submission import write_submission


def test_seed_everything_returns_seed():
    assert seed_everything(7) == 7


def test_write_submission_validates_against_sample(tmp_path):
    sample = pd.DataFrame({"id": [1, 2], "target": [0, 0]})
    df = pd.DataFrame({"target": [1, 0], "id": [1, 2]})
    path = write_submission(df, tmp_path, sample=sample, timestamp=False)
    assert path.name == "submission.csv"
    assert list(pd.read_csv(path).columns) == ["id", "target"]
    with pytest.raises(ValueError):
        write_submission(df.iloc[:1], tmp_path, sample=sample)
