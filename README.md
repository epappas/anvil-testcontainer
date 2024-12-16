# Anvil Test Container

A Python library for managing Anvil Ethereum test containers with security and ease of use in mind. This library provides a clean interface for running and interacting with Anvil instances in Docker containers, making it perfect for testing Ethereum smart contracts and DApps.

## Features

This library offers several key features for Ethereum development and testing:

### Core Functionality

- Automated container lifecycle management
- Ethereum chain forking and manipulation
- Secure command execution
- Transaction handling
- Block time control

### Advanced Features

- Chain state snapshots and restoration
- Health monitoring and diagnostics
- Container log access
- Resource cleanup and management
- Environment variable handling

### Security

- Input validation for Ethereum addresses
- Command injection protection
- Secure transaction handling
- Safe environment variable management
- Resource isolation

## Installation

You can install the library using pip:

```bash
pip install anvil-testcontainer
```

Or with Poetry (recommended):

```bash
poetry add anvil-testcontainer
```

### Prerequisites

- Python 3.8 or higher
- Docker installed and running
- Access to an Ethereum node for forking (e.g., Infura, Alchemy)

## Quick Start

Here's a simple example to get you started:

```python
from anvil_testcontainer import AnvilContainer

with AnvilContainer("<rpc provider url eg https://eth-mainnet.alchemyapi.io/v2..>") as anvil:
    web3 = anvil.get_web3()
    
    print(f"Current block: {web3.eth.block_number}")
    
    anvil.move_time(86400)
```

## Advanced Usage

### Configuration

Use the `ContainerConfig` class for more control:

```python
from anvil_testcontainer import AnvilContainer, ContainerConfig

config = ContainerConfig(
    fork_url="<provider URL>",
    fork_block_number=14000000,
    image="ghcr.io/foundry-rs/foundry:nightly",
    port=8545,
    timeout=60,
    env_vars={"ETHERSCAN_API_KEY": "your-key"}
)

with AnvilContainer(config) as anvil:
    snapshot_id = anvil.create_snapshot()

    tx_hash = anvil.send_transaction(
        from_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        to_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        value=100000000000000000  # 0.1 ETH
    )

    receipt = anvil.get_web3().eth.wait_for_transaction_receipt(tx_hash)

    anvil.revert_snapshot(snapshot_id)
```

### Health Monitoring

Monitor container health and access logs:

```python
with AnvilContainer(config) as anvil:
    # Check container health
    if anvil.verify_health():
        print("Container is healthy")
    
    # Access container logs
    logs = anvil.get_logs()
    print(logs)
```

## API Reference

### AnvilContainer

The main class for container management.

#### Basic Methods

- `start()`: Start the container
- `stop()`: Stop the container
- `get_web3()`: Get Web3 instance
- `move_time(seconds: int)`: Advance blockchain time
- `reset_fork(block_number: int)`: Reset to specific block

#### Advanced Methods

- `create_snapshot()`: Create chain state snapshot
- `revert_snapshot(snapshot_id: str)`: Restore chain state
- `send_transaction(...)`: Execute transaction
- `verify_health()`: Check container health
- `get_logs()`: Retrieve container logs

### ContainerConfig

Configuration class for container initialization.

```python
ContainerConfig(
    fork_url: str,
    fork_block_number: Optional[int] = None,
    image: str = "ghcr.io/foundry-rs/foundry:nightly",
    port: int = 8545,
    timeout: int = 60,
    env_vars: Optional[Dict[str, str]] = None
)
```

## Error Handling

The library provides custom exceptions for better error handling:

```python
from anvil_testcontainer import ValidationError

try:
    with AnvilContainer(config) as anvil:
        anvil.send_transaction(
            from_address="invalid_address",
            to_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            value=1000000000000000000
        )
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add or update tests
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/epappas/anvil-testcontainer.git
cd anvil-testcontainer

poetry install

poetry run pytest
```

### Testing

Run the test suite:

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=anvil_testcontainer
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:

1. Check the documentation
2. Search existing issues
3. Create a new issue if needed

## Acknowledgments

- Foundry team for Anvil
- OpenZeppelin for security best practices
- Web3.py team for Ethereum interaction capabilities
