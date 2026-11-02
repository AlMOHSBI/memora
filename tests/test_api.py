def test_api_has_health_route():
    from memora.api import app
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/v1/memories/search" in paths
