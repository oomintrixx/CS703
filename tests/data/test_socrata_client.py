from unittest.mock import patch, Mock

import pytest
import requests

from cs703.data.socrata_client import fetch_all


def _mock_response(rows):
    resp = Mock()
    resp.json.return_value = rows
    resp.raise_for_status.return_value = None
    return resp


@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_paginates_until_short_page(mock_get):
    page1 = [{"id": i} for i in range(3)]
    page2 = [{"id": i} for i in range(3, 5)]  # shorter than page_size -> last page
    mock_get.side_effect = [_mock_response(page1), _mock_response(page2)]

    rows = fetch_all("abcd-1234", page_size=3)

    assert rows == page1 + page2
    assert mock_get.call_count == 2


@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_stops_at_max_rows(mock_get):
    page1 = [{"id": i} for i in range(3)]
    page2 = [{"id": i} for i in range(3, 6)]
    mock_get.side_effect = [_mock_response(page1), _mock_response(page2)]

    rows = fetch_all("abcd-1234", page_size=3, max_rows=5)

    assert rows == (page1 + page2)[:5]


@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_builds_expected_query_params(mock_get):
    mock_get.side_effect = [_mock_response([])]

    fetch_all(
        "abcd-1234",
        select="a,b",
        where="c > 1",
        group="a",
        order="a",
        page_size=10,
        app_token="tok123",
    )

    called_url = mock_get.call_args.args[0]
    called_params = mock_get.call_args.kwargs["params"]
    assert called_url == "https://data.cityofnewyork.us/resource/abcd-1234.json"
    assert called_params["$select"] == "a,b"
    assert called_params["$where"] == "c > 1"
    assert called_params["$group"] == "a"
    assert called_params["$order"] == "a"
    assert called_params["$limit"] == 10
    assert called_params["$offset"] == 0
    assert called_params["$$app_token"] == "tok123"


@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_omits_app_token_param_when_none(mock_get):
    mock_get.side_effect = [_mock_response([])]

    fetch_all("abcd-1234")

    called_params = mock_get.call_args.kwargs["params"]
    assert "$$app_token" not in called_params


@patch("cs703.data.socrata_client.time.sleep")
@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_retries_on_timeout_then_succeeds(mock_get, mock_sleep):
    success_resp = Mock()
    success_resp.json.return_value = [{"id": 1}]
    success_resp.raise_for_status.return_value = None
    mock_get.side_effect = [requests.exceptions.Timeout("timed out"), success_resp]

    rows = fetch_all("abcd-1234", page_size=50_000)

    assert rows == [{"id": 1}]
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()


@patch("cs703.data.socrata_client.time.sleep")
@patch("cs703.data.socrata_client.requests.get")
def test_fetch_all_raises_after_exhausting_retries(mock_get, mock_sleep):
    mock_get.side_effect = requests.exceptions.Timeout("timed out")

    with pytest.raises(requests.exceptions.Timeout):
        fetch_all("abcd-1234", max_retries=2)

    assert mock_get.call_count == 3  # initial attempt + 2 retries
