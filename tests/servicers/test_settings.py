def test_service_properties(test_servicer_tls_config):
    assert isinstance(test_servicer_tls_config.hostport, str)
    assert test_servicer_tls_config.use_server_ssl is True
    assert test_servicer_tls_config.ssl_server_credentials is not None
    assert test_servicer_tls_config.ssl_channel_credentials is not None
