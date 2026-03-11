"""
Firebase Firestore initialization and schema management
Handles all database operations with proper error handling
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1 import Client
from google.cloud.firestore_v1.collection import CollectionReference
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

from hermes.config import HermesConfig

logger = logging.getLogger(__name__)

class FirebaseManager:
    """Manages Firebase Firestore connections and operations"""
    
    def __init__(self, config: HermesConfig = None):
        """Initialize Firebase connection"""
        self.config = config or HermesConfig
        self.app = None
        self.db: Optional[Client] = None
        self.collections: Dict[str, CollectionReference] = {}
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Firebase app and database connection"""
        try:
            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.config.FIREBASE.credentials_path)
                self.app = initialize_app(cred, {
                    'projectId': self.config.FIREBASE.project_id
                })
                logger.info(f"Firebase app initialized for project: {self.config.FIREBASE.project_id}")
            else:
                self.app = firebase_admin.get_app()
                logger.info("Using existing Firebase app")
            
            # Initialize Firestore client
            self.db = firestore.client()
            
            # Initialize collection references
            for name, collection_name in self.config.FIREBASE.collections.items():
                self.collections[name] = self.db.collection(collection_name)
            
            logger.info("Firestore client initialized successfully")
            
            # Create indexes if they don't exist
            self._ensure_indexes()
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    def _ensure_indexes(self) -> None:
        """Ensure necessary composite indexes exist"""
        # Note: In production, these indexes should be created in Firebase console
        # This method documents required indexes
        required_indexes = [
            # For wallet scanning
            "wallets: abandonment_score DESC, last_checked ASC",
            "wallets: chain ASC, last_activity DESC",
            
            # For discoveries
            "discoveries: priority_score DESC, status ASC",
            "discoveries: created DESC, usd_value DESC",
            
            # For transactions
            "transactions: timestamp DESC, status ASC"
        ]
        
        logger.debug(f"Required Firestore indexes: {required_indexes}")
    
    def log_system_event(self, event_type: str, message: str, data: Dict = None) -> None:
        """Log system event to Firestore"""
        try:
            event_data = {
                'type': event_type,
                'message': message,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'data': data or {}
            }
            
            self.collections['system_logs'].add(event_data)
            logger.info(f"System event logged: {event_type} - {message}")
            
        except Exception as e:
            logger.error(f"Failed to log system event: {str(e)}")
    
    def update_wallet_state(self, wallet_data: Dict[str, Any]) -> str:
        """
        Update or create wallet document
        Returns document ID
        """
        try:
            wallet_id = f"{wallet_data['chain']}_{wallet_data['address'].lower()}"
            wallet_ref = self.collections['wallets'].document(wallet_id)
            
            # Merge with existing data (don't overwrite unless specified)
            wallet_ref.set(wallet_data, merge=True)
            
            logger.debug(f"Updated wallet state: {wallet_id}")
            return wallet_id
            
        except Exception as e:
            logger.error(f"Failed to update wallet state: {str(e)}")
            raise
    
    def create_discovery(self, discovery_data: Dict[str, Any]) -> str:
        """Create a new discovery document"""
        try:
            # Add metadata
            discovery_data['created'] = firestore.SERVER_TIMESTAMP
            discovery_data['status'] = 'pending_verification'
            
            # Calculate priority score (simplified for Phase 1)
            usd_value = float(discovery_data.get('usd_value', 0))
            gas_estimate = float(discovery_data.get('gas_estimate_eth', 0))
            
            if gas_estimate > 0:
                net_value_ratio = (usd_value - (gas_estimate * 2000)) / usd_value
                discovery_data['priority_score'] = min(100, max(0, net_value_ratio * 100))
            else:
                discovery_data['priority_score'] = 50
            
            # Add to Firestore
            doc_ref = self.collections['discoveries'].add(discovery_data)[1]
            
            logger.info(f"Created discovery: {doc_ref.id} with priority {discovery_data['priority_score']}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to create discovery: {str(e)}")
            raise
    
    def get_pending_discoveries(self, limit: int = 10) -> List[Dict]:
        """Get discoveries pending approval"""
        try:
            query = (
                self.collections['discoveries']
                .where('status', '==', 'pending_verification')
                .order_by('priority_score', direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            discoveries = []
            for doc in query.stream():
                discovery = doc.to_dict()
                discovery['id'] = doc.id
                discoveries.append(discovery)
            
            return discoveries
            
        except Exception as e:
            logger.error(f"Failed to get pending discoveries: {str(e)}")
            return []
    
    def update_discovery_status(self, discovery_id: str, status: str, notes: str = "") -> bool:
        """Update discovery status"""
        try:
            update_data = {
                'status': status,
                'updated': firestore.SERVER_TIMESTAMP
            }
            
            if notes:
                update_data['notes'] = notes
            
            self.collections['discoveries'].document(discovery_id).update(update_data)
            logger.info(f"Updated discovery {discovery_id} to status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update discovery status: {str(e)}")
            return False
    
    def close(self) -> None:
        """Close Firebase connection"""
        try:
            if self.app:
                firebase_admin.delete_app(self.app)
                logger.info("Firebase app deleted")
        except Exception as e:
            logger.error(f"Error closing Firebase connection: {str(e)}")

# Singleton instance
firebase_manager = None

def get_firebase_manager() -> FirebaseManager:
    """Get or create Firebase manager instance"""
    global firebase_manager
    if firebase_manager is None:
        firebase_manager = FirebaseManager()
    return firebase_manager