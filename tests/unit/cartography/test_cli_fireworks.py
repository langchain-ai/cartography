from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.cli


def test_fireworks_cli_config(monkeypatch):
    # Arrange
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_FIREWORKS_API_KEY", "fw_test_key")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "fireworks",
                "--fireworks-apikey-env-var",
                "TEST_FIREWORKS_API_KEY",
                "--fireworks-account-id",
                "springfield-nuclear",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.fireworks_apikey == "fw_test_key"
    assert config.fireworks_account_id == "springfield-nuclear"
