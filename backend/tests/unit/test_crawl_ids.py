import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT_DIR))

from data.pipeline.common import stable_job_id

pytestmark = pytest.mark.unit


def test_stable_job_id_is_deterministic_and_source_scoped():
    url = "https://example.test/jobs/backend-engineer-123#details"
    assert stable_job_id("topcv", url) == stable_job_id(
        "topcv", " HTTPS://EXAMPLE.TEST/jobs/backend-engineer-123 "
    )
    assert stable_job_id("topcv", url) != stable_job_id("itviec", url)


def test_stable_job_id_avoids_same_trailing_number_collision():
    first = stable_job_id("topcv", "https://example.test/jobs/data-analyst-123")
    second = stable_job_id("topcv", "https://example.test/jobs/web-developer-123")
    assert first != second
