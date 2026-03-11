"""
Hermes Protocol Configuration
Centralized configuration management with environment-aware settings
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ChainConfig:
    """Configuration for a specific blockchain"""
    name: str
    chain_id: int
    rpc_urls: List[str]
    explorer_url: str
    native_symbol: str
    scan_priority: int
    
@dataclass
class FirebaseConfig:
    """Firebase/Firestore configuration"""
    project_id: str
    credentials_path: str
    collections: Dict[str, str]
    
@dataclass
class SecurityConfig:
    """Security and compliance settings"""
    max_recovery_value_usd: float = 10000.0
    min_abandonment_score: float = 0.8
    gas_price_multiplier: float = 1.2
    tx_confirmations: int = 6
    ofac_api_url: str = "https://api.treasury.gov/ofac"
    
class HermesConfig:
    """Main configuration class"""
    
    # Chain configurations
    CHAINS = {
        "ethereum": ChainConfig(
            name="Ethereum",
            chain_id=1,
            rpc_urls=[
                os.getenv("ETH_RPC_1", "https://eth.llamarpc.com"),
                os.getenv("ETH_RPC_2", "https://rpc.ankr.com/eth"),
                os.getenv("ETH_RPC_3", "https://cloudflare-eth.com")
            ],
            explorer_url="https://etherscan.io",
            native_symbol="ETH",
            scan_priority=1
        ),
        "polygon": ChainConfig(
            name="Polygon",
            chain_id=137,
            rpc_urls=[
                os.getenv("POLYGON_RPC_1", "https://polygon-rpc.com"),
                os.getenv("POLYGON_RPC_2", "https://rpc.ankr.com/polygon")
            ],
            explorer_url="https://polygonscan.com",
            native_symbol="MATIC",
            scan_priority=2
        ),
        "arbitrum": ChainConfig(
            name="Arbitrum",
            chain_id=42161,
            rpc_urls=[
                os.getenv("ARB_RPC_1", "https://arb1.arbitrum.io/rpc"),
                os.getenv("ARB_RPC_2", "https://rpc.ankr.com/arbitrum")
            ],
            explorer_url="https://arbiscan.io",
            native_symbol="ETH",
            scan_priority=3
        ),
        "optimism": ChainConfig(
            name="Optimism",
            chain_id=10,
            rpc_urls=[
                os.getenv("OP_RPC_1", "https://mainnet.optimism.io"),
                os.getenv("OP_RPC_2", "https://rpc.ankr.com/optimism")
            ],
            explorer_url="https://optimistic.etherscan.io",
            native_symbol="ETH",
            scan_priority=4
        )
    }
    
    # Firebase configuration
    FIREBASE = FirebaseConfig(
        project_id=os.getenv("FIREBASE_PROJECT_ID", "hermes-protocol"),
        credentials_path=os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json"),
        collections={
            "wallets": "wallets",
            "discoveries": "discoveries",
            "transactions": "transactions",
            "seeds": "seeds_meta",
            "system_logs": "system_logs"
        }
    )
    
    # Security configuration
    SECURITY = SecurityConfig(
        max_recovery_value_usd=float(os.getenv("MAX_RECOVERY_VALUE", "10000.0")),
        min_abandonment_score=float(os.getenv("MIN_ABANDONMENT_SCORE", "0.8")),
        gas_price_multiplier=float(os.getenv("GAS_PRICE_MULTIPLIER", "1.2")),
        tx_confirmations=int(os.getenv("TX_CONFIRMATIONS", "6")),
        ofac_api_url=os.getenv("OFAC_API_URL", "https://api.treasury.gov/ofac/sanctions.json")
    )
    
    # Scanner configuration
    SCAN_BATCH_SIZE = int(os.getenv("SCAN_BATCH_SIZE", "100"))
    SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL", "60"))
    MAX_RPC_RETRIES = int(os.getenv("MAX_RPC_RETRIES", "3"))
    
    # Treasury configuration
    TREASURY_ADDRESS = os.getenv("TREASURY_ADDRESS", "")
    TREASURY_THRESHOLD_ETH = float(os.getenv("TREASURY_THRESHOLD", "0.1"))
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        required_env_vars = ["FIREBASE_PROJECT_ID", "TREASURY_ADDRESS"]
        missing = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        if not os.path.exists(cls.FIREBASE.credentials_path):
            raise FileNotFoundError(
                f"Firebase credentials file not found: {cls.FIREBASE.credentials_path}"
            )
        
        return True
    
    @classmethod
    def get_chain_by_id(cls, chain_id: int) -> ChainConfig:
        """Get chain configuration by chain ID"""
        for chain in cls.CHAINS.values():
            if chain.chain_id == chain_id:
                return chain
        raise ValueError(f"Chain ID {chain_id} not configured")