"""
Multi-chain wallet scanner with BIP44 derivation and state tracking
Implements the core scanning logic with robust error handling
"""
import logging
import time
from typing import Dict, List, Optional, Tuple
from eth_account import Account
from web3 import Web3
from web3.exceptions import TransactionNotFound, ContractLogicError
import requests
import json

from hermes.config import HermesConfig
from hermes.firebase_setup import get_firebase_manager

logger = logging.getLogger(__name__)

class WalletScanner:
    """Scans wallets across multiple chains for dormant assets"""
    
    def __init__(self):
        self.config = HermesConfig
        self.firebase = get_firebase_manager()
        self.web3_clients = {}
        self._init_web3_clients()
    
    def _init_web3_clients(self) -> None:
        """Initialize Web3 clients for each chain"""
        for chain_name, chain_config in self.config.CHAINS.items():
            web3_instance = None
            last_error = None
            
            # Try each RPC URL until one works
            for rpc_url in chain_config.rpc_urls:
                try:
                    web3_instance = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                    
                    # Test connection
                    if web3_instance.is_connected():
                        self.web3_clients[chain_name] = web3_instance
                        logger.info(f"Connected to {chain_name} via {rpc_url[:30]}...")
                        break
                    else:
                        raise ConnectionError(f"Failed to connect to {rpc_url}")
                        
                except Exception as e:
                    last_error = e
                    logger.warning(f"Failed to connect to {chain_name} RPC {rpc_url[:30]}...: {str(e)}")
                    continue
            
            if chain_name not in self.web3_clients:
                logger.error(f"Failed to connect to any {chain_name} RPC: {last_error}")
    
    def derive_addresses