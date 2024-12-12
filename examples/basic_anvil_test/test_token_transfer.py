import os

from web3 import Web3
from eth_typing import Hash32
from anvil_testcontainer import AnvilContainer, ContainerConfig

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]


def test_token_transfer():
    # Configuration
    FORK_URL = os.getenv(
        "ETH_RPC_URL", "https://eth-mainnet.alchemyapi.io/v2/your-api-key"
    )
    DAI_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F"  # DAI token on mainnet
    WHALE_ADDRESS = "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503"  # DAI whale address
    RECIPIENT = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    TRANSFER_AMOUNT = 1000 * 10**18  # 1000 DAI

    # Create container config
    config = ContainerConfig(
        fork_url=FORK_URL,
        fork_block_number=19000000,  # Recent mainnet block
        timeout=30,
    )

    # Start container
    with AnvilContainer(config) as anvil:
        w3 = anvil.get_web3()

        # Create contract instance
        dai_contract = w3.eth.contract(
            address=Web3.to_checksum_address(DAI_ADDRESS), abi=ERC20_ABI
        )

        # Take snapshot before operations
        snapshot_id = anvil.create_snapshot()

        # Check initial balances
        whale_balance = dai_contract.functions.balanceOf(WHALE_ADDRESS).call()
        recipient_balance = dai_contract.functions.balanceOf(RECIPIENT).call()

        print(f"Initial whale balance: {whale_balance / 10**18:.2f} DAI")
        print(f"Initial recipient balance: {recipient_balance / 10**18:.2f} DAI")

        # Build and send transfer transaction
        tx_data = dai_contract.encode_abi(
            fn_name="transfer", args=[RECIPIENT, TRANSFER_AMOUNT]
        )

        tx_hash = anvil.send_transaction(
            from_address=WHALE_ADDRESS, to_address=DAI_ADDRESS, data=tx_data
        )

        # Wait for transaction to be mined
        receipt = w3.eth.wait_for_transaction_receipt(
            Hash32(bytes.fromhex(tx_hash[2:]))
        )
        assert receipt["status"] == 1, "Transaction failed"

        # Verify new balances
        new_whale_balance = dai_contract.functions.balanceOf(WHALE_ADDRESS).call()
        new_recipient_balance = dai_contract.functions.balanceOf(RECIPIENT).call()

        print(f"New whale balance: {new_whale_balance / 10**18:.2f} DAI")
        print(f"New recipient balance: {new_recipient_balance / 10**18:.2f} DAI")

        # Verify transfer
        assert new_recipient_balance == recipient_balance + TRANSFER_AMOUNT
        assert new_whale_balance == whale_balance - TRANSFER_AMOUNT

        # Demonstrate snapshot revert
        anvil.revert_snapshot(snapshot_id)
        reverted_balance = dai_contract.functions.balanceOf(RECIPIENT).call()
        assert reverted_balance == recipient_balance, "Snapshot revert failed"


if __name__ == "__main__":
    test_token_transfer()
