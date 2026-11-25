from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.cli


def test_stripe_cli_config(monkeypatch):
    # Arrange
    cli = cartography.cli.CLI(MagicMock(), "test")
    monkeypatch.setenv("TEST_STRIPE_API_KEY", "rk_test_fake")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "stripe",
                "--stripe-api-key-env-var",
                "TEST_STRIPE_API_KEY",
                "--stripe-sync-connected-accounts",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.stripe_api_key == "rk_test_fake"
    assert config.stripe_sync_connected_accounts is True
