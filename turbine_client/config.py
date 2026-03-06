"""
Chain configuration for the Turbine Python client.
"""

from dataclasses import dataclass
from typing import Dict

from turbine_client.constants import AVALANCHE_MAINNET, BASE_SEPOLIA, POLYGON_MAINNET


@dataclass
class ChainConfig:
    """Configuration for a specific blockchain."""

    chain_id: int
    name: str
    settlement_address: str
    ctf_address: str
    usdc_address: str
    default_host: str


# Chain configurations
CHAIN_CONFIGS: Dict[int, ChainConfig] = {
    BASE_SEPOLIA: ChainConfig(
        chain_id=BASE_SEPOLIA,
        name="Base Sepolia",
        settlement_address="0xF37B881F236033E55bF1cdAB628c7Cd88aAd89D4",
        ctf_address="0xc5Eb8d9dE7c56CC600B9ed4E71318307C740f5ED",
        usdc_address="0xf9065CCFF7025649F16D547DC341DAffF0C7F7f6",
        default_host="https://api.turbinefi.com",
    ),
    POLYGON_MAINNET: ChainConfig(
        chain_id=POLYGON_MAINNET,
        name="Polygon",
        settlement_address="0xdB96C91d9e5930fE3Ed1604603CfA4ece454725c",
        ctf_address="0xA86e521D596D626E2347875F1a4a23719dDaC0B6",
        usdc_address="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
        default_host="https://api.turbinefi.com",
    ),
    AVALANCHE_MAINNET: ChainConfig(
        chain_id=AVALANCHE_MAINNET,
        name="Avalanche",
        settlement_address="0x893ca652525B1F9DC25189ED9c3AD0543ACfb989",
        ctf_address="0xA86e521D596D626E2347875F1a4a23719dDaC0B6",
        usdc_address="0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        default_host="https://api.turbinefi.com",
    ),
}


def get_chain_config(chain_id: int) -> ChainConfig:
    """Get the configuration for a specific chain.

    Args:
        chain_id: The chain ID.

    Returns:
        The chain configuration.

    Raises:
        ValueError: If the chain ID is not supported.
    """
    if chain_id not in CHAIN_CONFIGS:
        raise ValueError(
            f"Unsupported chain ID: {chain_id}. "
            f"Supported chains: {list(CHAIN_CONFIGS.keys())}"
        )
    return CHAIN_CONFIGS[chain_id]


def get_settlement_address(chain_id: int) -> str:
    """Get the settlement contract address for a chain.

    Args:
        chain_id: The chain ID.

    Returns:
        The settlement contract address.
    """
    return get_chain_config(chain_id).settlement_address
