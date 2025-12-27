from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from typing import Optional
import logging

from config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.db = self.client[settings.MONGODB_DB_NAME]
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def _create_indexes(self):
        """Create necessary indexes"""
        try:
            # Documents collection indexes
            await self.db.documents.create_index("filename")
            await self.db.documents.create_index("upload_date")
            await self.db.documents.create_index("status")
            await self.db.documents.create_index([("text_content", "text")])  # Text search
            
            # Entities collection indexes
            await self.db.entities.create_index("document_id")
            await self.db.entities.create_index("entity_type")
            await self.db.entities.create_index("entity_text")
            
            # Analysis collection indexes
            await self.db.analysis.create_index("document_id")
            await self.db.analysis.create_index("analysis_type")
            
            logger.info("✅ MongoDB indexes created")
            
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    # Document operations
    async def insert_document(self, document: dict):
        """Insert a document"""
        result = await self.db.documents.insert_one(document)
        return str(result.inserted_id)
    
    async def get_document(self, document_id: str):
        """Get a document by ID"""
        from bson import ObjectId
        return await self.db.documents.find_one({"_id": ObjectId(document_id)})
    
    async def get_all_documents(self, skip: int = 0, limit: int = 100):
        """Get all documents with pagination"""
        cursor = self.db.documents.find().skip(skip).limit(limit).sort("upload_date", -1)
        return await cursor.to_list(length=limit)
    
    async def update_document(self, document_id: str, update_data: dict):
        """Update a document"""
        from bson import ObjectId
        result = await self.db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete_document(self, document_id: str):
        """Delete a document"""
        from bson import ObjectId
        result = await self.db.documents.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0
    
    # Entity operations
    async def insert_entities(self, entities: list):
        """Insert multiple entities"""
        if entities:
            result = await self.db.entities.insert_many(entities)
            return result.inserted_ids
        return []
    
    async def get_entities_by_document(self, document_id: str):
        """Get all entities for a document"""
        cursor = self.db.entities.find({"document_id": document_id})
        return await cursor.to_list(length=None)
    
    async def get_entities_by_type(self, document_id: str, entity_type: str):
        """Get entities of specific type"""
        cursor = self.db.entities.find({
            "document_id": document_id,
            "entity_type": entity_type
        })
        return await cursor.to_list(length=None)
    
    # Analysis operations
    async def insert_analysis(self, analysis: dict):
        """Insert analysis results"""
        result = await self.db.analysis.insert_one(analysis)
        return str(result.inserted_id)
    
    async def get_analysis(self, document_id: str, analysis_type: str = None):
        """Get analysis results"""
        query = {"document_id": document_id}
        if analysis_type:
            query["analysis_type"] = analysis_type
        
        cursor = self.db.analysis.find(query)
        return await cursor.to_list(length=None)
    
    # Search operations
    async def search_documents(self, query: str, limit: int = 20):
        """Full-text search across documents"""
        cursor = self.db.documents.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_statistics(self):
        """Get database statistics"""
        total_docs = await self.db.documents.count_documents({})
        total_entities = await self.db.entities.count_documents({})
        total_analyses = await self.db.analysis.count_documents({})
        
        # Document types distribution
        pipeline = [
            {"$group": {"_id": "$doc_type", "count": {"$sum": 1}}}
        ]
        doc_types = await self.db.documents.aggregate(pipeline).to_list(length=None)
        
        return {
            "total_documents": total_docs,
            "total_entities": total_entities,
            "total_analyses": total_analyses,
            "document_types": doc_types
        }

# Global MongoDB instance
mongodb = MongoDB()