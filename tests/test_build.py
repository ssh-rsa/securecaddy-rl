"""
Tests for Docker image build verification.
"""
import pytest


class TestDockerBuild:
    """Test suite for Docker build process."""

    def test_image_builds_successfully(self, build_image):
        """Test that the Docker image builds without errors."""
        assert build_image is not None
        assert build_image.id is not None

    def test_image_has_correct_labels(self, build_image):
        """Test that the image has the expected labels."""
        labels = build_image.labels

        assert "org.opencontainers.image.authors" in labels
        assert labels["org.opencontainers.image.authors"] == "m@tusk.sh"

        assert "com.tusk.version" in labels
        assert "com.tusk.release-date" in labels

    def test_image_has_caddy_binary(self, docker_client, build_image, image_name):
        """Test that the Caddy binary exists in the image."""
        # Run a command to check if caddy binary exists
        result = docker_client.containers.run(
            image_name,
            command=["version"],
            remove=True,
            stdout=True,
            stderr=True
        )

        output = result.decode('utf-8')
        assert "v2." in output  # Caddy version should be v2.x

    def test_image_size_is_reasonable(self, build_image):
        """Test that the image size is reasonable (under 100MB)."""
        # Get image size in MB
        size_mb = build_image.attrs['Size'] / (1024 * 1024)

        # Image should be small due to Chainguard base
        # Allow up to 100MB (should be much smaller in practice)
        assert size_mb < 100, f"Image size is {size_mb:.2f}MB, expected under 100MB"

    def test_caddy_binary_is_executable(self, docker_client, image_name):
        """Test that the Caddy binary has execute permissions."""
        result = docker_client.containers.run(
            image_name,
            command=["--version"],
            remove=True,
            stdout=True,
            stderr=True
        )

        output = result.decode('utf-8')
        # Should output version without permission errors
        assert "v2." in output or "Caddy" in output

    def test_image_uses_minimal_layers(self, build_image):
        """Test that the image has a reasonable number of layers."""
        # Multi-stage builds should result in minimal final layers
        history = build_image.history()

        # Count non-empty layers
        layers = [layer for layer in history if layer.get('Size', 0) > 0]

        # Should have relatively few layers due to multi-stage build
        assert len(layers) < 15, f"Image has {len(layers)} layers, expected fewer"

    def test_entrypoint_is_set(self, build_image):
        """Test that ENTRYPOINT is correctly set."""
        config = build_image.attrs['Config']

        assert 'Entrypoint' in config
        assert config['Entrypoint'] == ['/usr/bin/caddy']

    def test_default_cmd_is_set(self, build_image):
        """Test that default CMD is correctly set."""
        config = build_image.attrs['Config']

        assert 'Cmd' in config
        expected_cmd = ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
        assert config['Cmd'] == expected_cmd
