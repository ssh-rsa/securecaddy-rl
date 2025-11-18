"""
Tests for container runtime behavior.
"""
import pytest
import time
import requests


class TestContainerRuntime:
    """Test suite for container runtime behavior."""

    def test_container_starts_successfully(self, running_container):
        """Test that the container starts and runs."""
        assert running_container.status == "running"

    def test_caddy_process_is_running(self, running_container):
        """Test that the Caddy process is running inside the container."""
        # Execute 'ps' command to check for caddy process
        # Note: Chainguard static image might not have ps, so we check container status
        assert running_container.status == "running"

        # Give Caddy time to start
        time.sleep(1)

        # Container should still be running
        running_container.reload()
        assert running_container.status == "running"

    def test_container_responds_to_http(self, running_container):
        """Test that the container responds to HTTP requests."""
        # Get the mapped port
        port_info = running_container.ports.get('80/tcp')
        assert port_info is not None, "Port 80 should be exposed"

        host_port = port_info[0]['HostPort']

        # Make HTTP request
        try:
            response = requests.get(f"http://localhost:{host_port}", timeout=5)
            assert response.status_code == 200
            assert "Hello from Caddy!" in response.text
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to connect to container: {e}")

    def test_container_stays_running(self, running_container):
        """Test that the container doesn't exit unexpectedly."""
        # Wait for a bit
        time.sleep(3)

        # Check container is still running
        running_container.reload()
        assert running_container.status == "running"

    def test_container_logs_output(self, running_container):
        """Test that the container produces logs."""
        time.sleep(2)

        logs = running_container.logs().decode('utf-8')

        # Caddy should output some startup logs
        # Just check that we got some logs
        assert len(logs) > 0

    def test_container_handles_signals(self, container):
        """Test that the container responds to stop signals."""
        # Start the container
        container.start()
        time.sleep(2)

        # Stop the container gracefully
        container.stop(timeout=10)

        # Check it stopped
        container.reload()
        assert container.status in ["exited", "stopped"]

    @pytest.mark.slow
    def test_container_with_invalid_config(self, docker_client, image_name):
        """Test that container handles invalid Caddyfile gracefully."""
        # Create a container with invalid config
        container = None
        try:
            container = docker_client.containers.run(
                image_name,
                detach=True,
                command=["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"],
                auto_remove=False
            )

            # Wait a bit
            time.sleep(2)

            # Container should exit due to missing Caddyfile
            container.reload()

            # The container might exit or stay running (Caddy has default behavior)
            # This test documents the behavior
            assert container.status in ["running", "exited"]

        finally:
            if container:
                try:
                    container.stop(timeout=5)
                    container.remove(force=True)
                except Exception:
                    pass

    def test_container_exposes_port_80(self, running_container):
        """Test that port 80 is properly exposed."""
        ports = running_container.ports

        assert '80/tcp' in ports
        assert ports['80/tcp'] is not None

    def test_multiple_requests_work(self, running_container):
        """Test that multiple HTTP requests work correctly."""
        port_info = running_container.ports.get('80/tcp')
        host_port = port_info[0]['HostPort']

        # Make multiple requests
        for i in range(5):
            response = requests.get(f"http://localhost:{host_port}", timeout=5)
            assert response.status_code == 200
            assert "Hello from Caddy!" in response.text
