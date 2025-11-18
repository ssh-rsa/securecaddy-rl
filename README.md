# securecaddy-rl

> [!NOTE]
> This is **_not_** an official repository/image of the [Caddy Web Server](https://github.com/caddyserver) organization.

A caddy image with rate-limiting that i built to practice building custom docker images.  The image is based on the [Chainguard Static Starter Image](https://chainguard.dev) 

It also includes the [caddy-ratelimit](https://github.com/mholt/caddy-ratelimit) by MHolt, an easy to use rate limiting plugin for Caddy 2.

## Building

Simply clone the repository

```sh
git clone https://github.com/ssh-rsa/securecaddy-rl && cd securecaddy-rl
```
and then build with `docker build`!

```sh
docker build -t securecaddy-rl:latest .
```

## Testing

This project includes comprehensive tests for build verification, runtime behavior, and rate limiting functionality.

### Running Tests Locally

1. Install test dependencies:
```sh
pip install -r requirements-test.txt
```

2. Run all tests:
```sh
pytest -v
```

3. Run specific test categories:
```sh
# Build tests only
pytest tests/test_build.py -v

# Runtime tests only
pytest tests/test_runtime.py -v

# Rate limiting tests only
pytest tests/test_ratelimit.py -v

# Skip slow tests
pytest -m "not slow" -v
```

### Test Coverage

The test suite covers:
- **Build Verification**: Ensures the Docker image builds correctly with all required components
- **Runtime Behavior**: Validates container startup, HTTP responses, and process management
- **Rate Limiting**: Tests the core rate limiting functionality with various scenarios

### CI/CD

Tests run automatically on:
- Push to `main` branch
- Pull requests
- Manual workflow dispatch

## Usage

### With Docker Compose

```sh
docker-compose up -d
```

### With Docker

```sh
docker run -d \
  -p 80:80 -p 443:443 \
  -v $(pwd)/Caddyfile:/etc/caddy/Caddyfile \
  -v caddy_data:/data \
  -v caddy_config:/config \
  ghcr.io/ssh-rsa/securecaddy-rl:latest
```

See `Caddyfile.example` for rate limiting configuration examples.


