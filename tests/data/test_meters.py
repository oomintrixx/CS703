from unittest.mock import patch

from cs703.data import meters


@patch("cs703.data.meters.fetch_all")
def test_fetch_meters_requests_full_resource(mock_fetch_all):
    mock_fetch_all.return_value = [{"meter_number": "1"}]

    result = meters.fetch_meters()

    assert result == [{"meter_number": "1"}]
    assert mock_fetch_all.call_args.args[0] == meters.RESOURCE_ID
    assert "max_rows" not in mock_fetch_all.call_args.kwargs
