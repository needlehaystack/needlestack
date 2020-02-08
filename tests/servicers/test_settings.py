def test_service_properties(test_servicer_config):
    assert isinstance(test_servicer_config.hostport, str)
    assert test_servicer_config.use_ssl is True
    assert test_servicer_config.ssl_server_credentials is not None
