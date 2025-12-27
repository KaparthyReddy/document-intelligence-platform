from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from database.mongodb import mongodb
from database.redis_cache import redis_client
from services.analysis_engine import AnalysisEngine
from models import ner_model, sentiment_model, doc_classifier, kg_builder

analysis_router = APIRouter()
analysis_engine = AnalysisEngine()

class AnalysisRequest(BaseModel):
    document_id: str
    force: Optional[bool] = False


@analysis_router.post("/analyze")
async def analyze_document(
    background_tasks: BackgroundTasks,
    request: AnalysisRequest
):
    """
    Trigger comprehensive document analysis
    """
    try:
        # Get document
        document = await mongodb.get_document(request.document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        text = document.get('text_content', '')
        
        if not text:
            raise HTTPException(status_code=400, detail="Document has no text content")
        
        # Update status
        await mongodb.update_document(request.document_id, {
            'analysis_status': 'processing'
        })
        
        # Run analysis in background
        background_tasks.add_task(
            run_analysis_task,
            request.document_id,
            text,
            request.force
        )
        
        return {
            'success': True,
            'message': 'Analysis started',
            'document_id': request.document_id,
            'status': 'processing'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@analysis_router.get("/analysis/{document_id}")
async def get_analysis(document_id: str):
    """
    Get analysis results for a document
    """
    try:
        # Check cache first
        cached = await redis_client.get_cached_analysis(document_id, 'complete')
        if cached:
            return {
                'success': True,
                'data': cached,
                'cached': True
            }
        
        # Get from database
        analysis_list = await mongodb.get_analysis(document_id)
        
        if not analysis_list:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get the most recent analysis
        analysis = analysis_list[0] if isinstance(analysis_list, list) else analysis_list
        
        return {
            'success': True,
            'data': analysis,
            'cached': False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@analysis_router.get("/entities/{document_id}")
async def get_entities(document_id: str, entity_type: Optional[str] = None):
    """
    Get extracted entities from document
    """
    try:
        if entity_type:
            entities = await mongodb.get_entities_by_type(document_id, entity_type)
        else:
            entities = await mongodb.get_entities_by_document(document_id)
        
        # Convert ObjectId to string
        for entity in entities:
            entity['_id'] = str(entity['_id'])
        
        return {
            'success': True,
            'data': {
                'entities': entities,
                'total': len(entities),
                'entity_type': entity_type
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")


@analysis_router.get("/sentiment/{document_id}")
async def get_sentiment(document_id: str):
    """
    Get sentiment analysis for document
    """
    try:
        analysis_list = await mongodb.get_analysis(document_id, "complete")
        
        if not analysis_list:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis = analysis_list[0] if isinstance(analysis_list, list) else analysis_list
        sentiment = analysis.get('sentiment', {})
        
        return {
            'success': True,
            'data': sentiment
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sentiment: {str(e)}")


@analysis_router.get("/knowledge-graph/{document_id}")
async def get_knowledge_graph(document_id: str):
    """
    Get knowledge graph for document
    """
    try:
        analysis_list = await mongodb.get_analysis(document_id, "complete")
        
        if not analysis_list:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis = analysis_list[0] if isinstance(analysis_list, list) else analysis_list
        kg = analysis.get('knowledge_graph', {})
        
        return {
            'success': True,
            'data': kg
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge graph: {str(e)}")


@analysis_router.get("/timeline/{document_id}")
async def get_timeline(document_id: str):
    """
    Get timeline extracted from document
    """
    try:
        analysis_list = await mongodb.get_analysis(document_id, "complete")
        
        if not analysis_list:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis = analysis_list[0] if isinstance(analysis_list, list) else analysis_list
        timeline = analysis.get('timeline', [])
        dates = analysis.get('dates', [])
        
        return {
            'success': True,
            'data': {
                'timeline': timeline,
                'dates': dates,
                'total_events': len(timeline)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@analysis_router.get("/search")
async def search_documents(query: str, limit: int = 20):
    """
    Search across all documents
    """
    try:
        results = await mongodb.search_documents(query, limit)
        
        # Convert ObjectId to string
        for doc in results:
            doc['_id'] = str(doc['_id'])
        
        return {
            'success': True,
            'data': {
                'results': results,
                'query': query,
                'total': len(results)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Background task
async def run_analysis_task(document_id: str, text: str, force: bool):
    """
    Background task to run analysis
    """
    try:
        await analysis_engine.analyze_document(document_id, text, force)
        print(f"✅ Analysis completed for document {document_id}")
    except Exception as e:
        print(f"❌ Analysis failed for document {document_id}: {e}")
        await mongodb.update_document(document_id, {
            'analysis_status': 'failed',
            'error': str(e)
        })