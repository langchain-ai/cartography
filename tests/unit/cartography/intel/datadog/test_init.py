from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.datadog
from cartography.config import Config


@patch.object(cartography.intel.datadog, "build_session")
def test_start_datadog_ingestion_skips_without_app_key(mock_build_session):
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        datadog_api_key="api-key-only",
    )

    # Act
    cartography.intel.datadog.start_datadog_ingestion(MagicMock(), config)

    # Assert
    mock_build_session.assert_not_called()
