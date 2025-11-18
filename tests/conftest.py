"""
Pytest configuration and fixtures for securecaddy-rl tests.
"""
import pytest
import docker
import time
import os


@pytest.fixture(scope="session")
def docker_client():
    """Provide a Docker client for the test session."""
    return docker.from_env()


@pytest.fixture(scope="session")
def image_name():
    """Return the image name to test."""
    return os.getenv("TEST_IMAGE_NAME", "securecaddy-rl:test")


@pytest.fixture(scope="session")
def build_image(docker_client, image_name):
    """Build the Docker image before running tests."""
    print(f"\nBuilding image: {image_name}")

    # Build the image
    image, build_logs = docker_client.images.build(
        path="/home/user/securecaddy-rl",
        tag=image_name,
        rm=True,
        forcerm=True
    )

    # Print build logs
    for log in build_logs:
        if 'stream' in log:
            print(log['stream'].strip())

    yield image

    # Cleanup: remove the test image after tests
    # Uncomment if you want to clean up after tests
    # docker_client.images.remove(image.id, force=True)


@pytest.fixture
def container(docker_client, build_image, image_name):
    """Create and start a container for testing."""
    container = None
    try:
        container = docker_client.containers.create(
            image_name,
            detach=True,
            auto_remove=False
        )
        yield container
    finally:
        if container:
            try:
                container.stop(timeout=5)
                container.remove(force=True)
            except Exception as e:
                print(f"Warning: Failed to cleanup container: {e}")


@pytest.fixture
def running_container(docker_client, build_image, image_name):
    """Create, start, and provide a running container for testing."""
    container = None
    try:
        # Create container with a test Caddyfile
        container = docker_client.containers.run(
            image_name,
            detach=True,
            ports={'80/tcp': None},  # Random port
            command=["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"],
            volumes={
                '/home/user/securecaddy-rl/tests/fixtures/Caddyfile.test': {
                    'bind': '/etc/caddy/Caddyfile',
                    'mode': 'ro'
                }
            },
            auto_remove=False
        )

        # Wait for container to be ready
        time.sleep(2)

        # Reload container to get updated port info
        container.reload()

        yield container
    finally:
        if container:
            try:
                container.stop(timeout=5)
                container.remove(force=True)
            except Exception as e:
                print(f"Warning: Failed to cleanup running container: {e}")


@pytest.fixture
def ratelimit_container(docker_client, build_image, image_name):
    """Create a container with rate limiting configuration for testing."""
    container = None
    try:
        container = docker_client.containers.run(
            image_name,
            detach=True,
            ports={'80/tcp': None},  # Random port
            command=["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"],
            volumes={
                '/home/user/securecaddy-rl/tests/fixtures/Caddyfile.ratelimit': {
                    'bind': '/etc/caddy/Caddyfile',
                    'mode': 'ro'
                }
            },
            auto_remove=False
        )

        # Wait for container to be ready
        time.sleep(2)

        # Reload container to get updated port info
        container.reload()

        yield container
    finally:
        if container:
            try:
                container.stop(timeout=5)
                container.remove(force=True)
            except Exception as e:
                print(f"Warning: Failed to cleanup ratelimit container: {e}")
