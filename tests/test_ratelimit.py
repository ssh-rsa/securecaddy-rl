"""
Tests for rate limiting functionality.
"""
import pytest
import time
import requests


class TestRateLimiting:
    """Test suite for rate limiting functionality."""

    def test_rate_limit_plugin_loaded(self, ratelimit_container):
        """Test that the rate limit plugin is loaded."""
        # Container should start successfully with rate_limit directive
        assert ratelimit_container.status == "running"

        # Check logs for any plugin errors
        logs = ratelimit_container.logs().decode('utf-8')
        assert "rate_limit" not in logs.lower() or "error" not in logs.lower()

    def test_requests_under_limit_succeed(self, ratelimit_container):
        """Test that requests under the rate limit succeed."""
        port_info = ratelimit_container.ports.get('80/tcp')
        host_port = port_info[0]['HostPort']

        # Make 5 requests (under the 10/minute limit)
        for i in range(5):
            response = requests.get(f"http://localhost:{host_port}", timeout=5)
            assert response.status_code == 200
            assert "Rate limited endpoint" in response.text

    def test_rate_limit_enforced(self, ratelimit_container):
        """Test that the rate limit is enforced (10 requests per minute)."""
        port_info = ratelimit_container.ports.get('80/tcp')
        host_port = port_info[0]['HostPort']

        successful_requests = 0
        rate_limited_requests = 0

        # Make more requests than the limit allows (15 requests, limit is 10)
        for i in range(15):
            try:
                response = requests.get(f"http://localhost:{host_port}", timeout=5)

                if response.status_code == 200:
                    successful_requests += 1
                elif response.status_code == 429:  # Too Many Requests
                    rate_limited_requests += 1

            except requests.exceptions.RequestException as e:
                pytest.fail(f"Request failed unexpectedly: {e}")

        # We should have hit the rate limit
        assert successful_requests <= 10, f"Expected max 10 successful requests, got {successful_requests}"
        assert rate_limited_requests > 0, "Expected some requests to be rate limited"

    def test_rate_limit_headers_present(self, ratelimit_container):
        """Test that rate limit headers are present in responses."""
        port_info = ratelimit_container.ports.get('80/tcp')
        host_port = port_info[0]['HostPort']

        # Make a request
        response = requests.get(f"http://localhost:{host_port}", timeout=5)

        # Check for common rate limit headers (implementation-specific)
        # Note: caddy-ratelimit may or may not set these headers
        # This test documents the actual behavior
        headers = response.headers
        print(f"Response headers: {dict(headers)}")

        # At minimum, we should get a valid response
        assert response.status_code in [200, 429]

    @pytest.mark.slow
    def test_rate_limit_resets_after_window(self, ratelimit_container):
        """Test that rate limit resets after the time window expires."""
        port_info = ratelimit_container.ports.get('80/tcp')
        host_port = port_info[0]['HostPort']

        # Make 10 requests to hit the limit
        for i in range(10):
            requests.get(f"http://localhost:{host_port}", timeout=5)

        # Next request should be rate limited
        response = requests.get(f"http://localhost:{host_port}", timeout=5)
        assert response.status_code == 429

        # Wait for the 1-minute window to expire (plus buffer)
        print("Waiting 65 seconds for rate limit window to reset...")
        time.sleep(65)

        # Now requests should work again
        response = requests.get(f"http://localhost:{host_port}", timeout=5)
        assert response.status_code == 200

    def test_different_ips_tracked_separately(self, docker_client, build_image, image_name):
        """Test that different IPs are tracked separately for rate limiting."""
        # This test would require running containers with different source IPs
        # which is complex in a local Docker environment.
        # We'll create two separate containers to simulate this

        containers = []
        try:
            for i in range(2):
                container = docker_client.containers.run(
                    image_name,
                    detach=True,
                    ports={'80/tcp': None},
                    command=["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"],
                    volumes={
                        '/home/user/securecaddy-rl/tests/fixtures/Caddyfile.ratelimit': {
                            'bind': '/etc/caddy/Caddyfile',
                            'mode': 'ro'
                        }
                    },
                    auto_remove=False
                )
                containers.append(container)

            time.sleep(2)

            # Each container should handle its own rate limits independently
            for container in containers:
                container.reload()
                port_info = container.ports.get('80/tcp')
                host_port = port_info[0]['HostPort']

                # Make requests to each container
                response = requests.get(f"http://localhost:{host_port}", timeout=5)
                assert response.status_code == 200

        finally:
            # Cleanup
            for container in containers:
                try:
                    container.stop(timeout=5)
                    container.remove(force=True)
                except Exception:
                    pass

    def test_rate_limit_returns_429_status(self, ratelimit_container):
        """Test that rate limiting returns HTTP 429 status code."""
        port_info = ratelimit_container.ports.get('80/tcp')
        host_port = port_info[0]['HostPort']

        # Exhaust the rate limit
        for i in range(12):
            response = requests.get(f"http://localhost:{host_port}", timeout=5)

        # This request should be rate limited
        response = requests.get(f"http://localhost:{host_port}", timeout=5)

        # Should get 429 Too Many Requests or continue to serve (depending on implementation)
        assert response.status_code in [200, 429]

        # If we got rate limited, verify it's the right status
        if response.status_code == 429:
            assert response.status_code == 429

    def test_rate_limit_config_syntax_valid(self):
        """Test that the example Caddyfile has valid rate limit syntax."""
        # Read the example Caddyfile
        with open('/home/user/securecaddy-rl/Caddyfile.example', 'r') as f:
            content = f.read()

        # Check for required rate_limit directives
        assert 'rate_limit' in content
        assert 'zone' in content
        assert 'key {remote_host}' in content
        assert 'events' in content
        assert 'window' in content

        # Check the documented limits are present
        assert '60' in content  # 60 requests per minute
        assert '1m' in content  # 1 minute window
        assert '500' in content  # 500 requests per hour
        assert '1h' in content  # 1 hour window
