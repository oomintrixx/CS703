from unittest.mock import patch

from cs703.data import precincts


@patch("cs703.data.precincts.fetch_all")
def test_fetch_precincts_requests_full_resource(mock_fetch_all):
    mock_fetch_all.return_value = [{"precinct": "1"}]

    result = precincts.fetch_precincts()

    assert result == [{"precinct": "1"}]
    assert mock_fetch_all.call_args.args[0] == precincts.RESOURCE_ID
