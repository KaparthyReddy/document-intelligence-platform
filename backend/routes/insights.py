from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from services.analysis_engine import AnalysisEngine
from database.mongodb import mongodb

insights_router = APIRouter()
analysis_engine = AnalysisEngine()

class CompareRequest(BaseModel):
    document_id_1: str
    document_id_2: str


@insights_router.get("/insights/{document_id}")
async def get_insights(document_id: str):
    """
    Get high-level insights for a document
    """
    try:
        insights = await analysis_engine.get_insights(document_id)
        
        if 'error' in insights:
            raise HTTPException(status_code=404, detail=insights['error'])
        
        return {
            'success': True,
            'data': insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@insights_router.post("/compare")
async def compare_documents(request: CompareRequest):
    """
    Compare two documents
    """
    try:
        comparison = await analysis_engine.compare_documents(
            request.document_id_1,
            request.document_id_2
        )
        
        if 'error' in comparison:
            raise HTTPException(status_code=404, detail=comparison['error'])
        
        return {
            'success': True,
            'data': comparison
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@insights_router.get("/entity-network/{document_id}")
async def get_entity_network(document_id: str, entity: str, depth: int = 1):
    """
    Get entity network (neighbors) for a specific entity
    """
    try:
        from models import kg_builder
        
        # First ensure knowledge graph is built
        analysis = await mongodb.get_analysis(document_id, "complete")
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get the knowledge graph data
        kg_data = analysis[0].get('knowledge_graph', {}) if isinstance(analysis, list) else analysis.get('knowledge_graph', {})
        
        if not kg_data:
            raise HTTPException(status_code=404, detail="Knowledge graph not found")
        
        # Build the graph in kg_builder
        entities_data = analysis[0].get('entities', {}).get('entities', []) if isinstance(analysis, list) else analysis.get('entities', {}).get('entities', [])
        relationships = analysis[0].get('relationships', []) if isinstance(analysis, list) else analysis.get('relationships', [])
        
        await kg_builder.build_graph(entities_data, relationships)
        
        # Get neighbors
        neighbors = await kg_builder.get_entity_neighbors(entity, depth)
        
        return {
            'success': True,
            'data': {
                'entity': entity,
                'depth': depth,
                'neighbors': neighbors['neighbors'],
                'total_neighbors': neighbors['count']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity network: {str(e)}")


@insights_router.get("/central-entities/{document_id}")
async def get_central_entities(document_id: str, top_n: int = 5):
    """
    Get most central/important entities in document
    """
    try:
        from models import kg_builder
        
        # Get analysis
        analysis = await mongodb.get_analysis(document_id, "complete")
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Build graph
        entities_data = analysis[0].get('entities', {}).get('entities', []) if isinstance(analysis, list) else analysis.get('entities', {}).get('entities', [])
        relationships = analysis[0].get('relationships', []) if isinstance(analysis, list) else analysis.get('relationships', [])
        
        await kg_builder.build_graph(entities_data, relationships)
        
        # Get central entities
        central = await kg_builder.get_central_entities(top_n)
        
        return {
            'success': True,
            'data': {
                'central_entities': central,
                'total': len(central)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get central entities: {str(e)}")


@insights_router.get("/document-summary/{document_id}")
async def get_document_summary(document_id: str):
    """
    Get a comprehensive summary of the document
    """
    try:
        # Get document
        document = await mongodb.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get analysis
        analysis = await mongodb.get_analysis(document_id, "complete")
        
        # Build summary
        summary = {
            'document_id': document_id,
            'filename': document.get('filename', ''),
            'file_type': document.get('file_type', ''),
            'upload_date': document.get('upload_date', '').isoformat() if hasattr(document.get('upload_date', ''), 'isoformat') else str(document.get('upload_date', '')),
            'file_size': document.get('file_size', 0)
        }
        
        if analysis:
            analysis_data = analysis[0] if isinstance(analysis, list) else analysis
            
            summary.update({
                'category': analysis_data.get('classification', {}).get('category', 'unknown'),
                'sentiment': analysis_data.get('sentiment', {}).get('overall_sentiment', 'neutral'),
                'total_entities': analysis_data.get('entities', {}).get('total_entities', 0),
                'entity_types': analysis_data.get('entities', {}).get('entity_types', []),
                'total_words': analysis_data.get('statistics', {}).get('total_words', 0),
                'has_tables': analysis_data.get('structure', {}).get('has_tables', False),
                'has_lists': analysis_data.get('structure', {}).get('has_lists', False),
                'dates_mentioned': len(analysis_data.get('dates', []))
            })
            
            # Get insights
            insights = await analysis_engine.get_insights(document_id)
            if 'summary' in insights:
                summary['natural_language_summary'] = insights['summary']
                summary['key_findings'] = insights.get('key_findings', [])
        else:
            summary['analysis_status'] = 'not_analyzed'
        
        return {
            'success': True,
            'data': summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@insights_router.get("/trends")
async def get_trends(limit: int = 100):
    """
    Get trends across all documents
    """
    try:
        # Get recent documents
        documents = await mongodb.get_all_documents(0, limit)
        
        # Aggregate data
        trends = {
            'total_documents': len(documents),
            'document_types': {},
            'common_entities': {},
            'sentiment_distribution': {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            },
            'upload_timeline': []
        }
        
        for doc in documents:
            doc_id = str(doc['_id'])
            
            # Document types
            doc_type = doc.get('file_type', 'unknown')
            trends['document_types'][doc_type] = trends['document_types'].get(doc_type, 0) + 1
            
            # Get analysis if available
            analysis = await mongodb.get_analysis(doc_id, "complete")
            if analysis:
                analysis_data = analysis[0] if isinstance(analysis, list) else analysis
                
                # Sentiment
                sentiment = analysis_data.get('sentiment', {}).get('overall_sentiment', 'neutral')
                trends['sentiment_distribution'][sentiment] += 1
                
                # Entities
                entities = analysis_data.get('entities', {}).get('unique_entities', {})
                for entity_type, entity_list in entities.items():
                    if entity_type not in trends['common_entities']:
                        trends['common_entities'][entity_type] = {}
                    
                    for entity in entity_list:
                        trends['common_entities'][entity_type][entity] = \
                            trends['common_entities'][entity_type].get(entity, 0) + 1
            
            # Upload timeline
            upload_date = doc.get('upload_date', '')
            if upload_date:
                date_str = upload_date.strftime('%Y-%m-%d') if hasattr(upload_date, 'strftime') else str(upload_date)
                trends['upload_timeline'].append(date_str)
        
        # Get top entities per type
        for entity_type in trends['common_entities']:
            sorted_entities = sorted(
                trends['common_entities'][entity_type].items(),
                key=lambda x: x[1],
                reverse=True
            )
            trends['common_entities'][entity_type] = dict(sorted_entities[:10])
        
        return {
            'success': True,
            'data': trends
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


@insights_router.get("/export-report/{document_id}")
async def export_report(document_id: str, format: str = "json"):
    """
    Export comprehensive analysis report
    """
    try:
        # Get document
        document = await mongodb.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get analysis
        analysis = await mongodb.get_analysis(document_id, "complete")
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis_data = analysis[0] if isinstance(analysis, list) else analysis
        
        # Get insights
        insights = await analysis_engine.get_insights(document_id)
        
        # Build comprehensive report
        report = {
            'document_info': {
                'id': document_id,
                'filename': document.get('filename', ''),
                'file_type': document.get('file_type', ''),
                'file_size': document.get('file_size', 0),
                'upload_date': document.get('upload_date', '').isoformat() if hasattr(document.get('upload_date', ''), 'isoformat') else str(document.get('upload_date', ''))
            },
            'classification': analysis_data.get('classification', {}),
            'sentiment': analysis_data.get('sentiment', {}),
            'entities': analysis_data.get('entities', {}),
            'relationships': analysis_data.get('relationships', []),
            'timeline': analysis_data.get('timeline', []),
            'statistics': analysis_data.get('statistics', {}),
            'structure': analysis_data.get('structure', {}),
            'insights': insights,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        if format == "json":
            return {
                'success': True,
                'data': report,
                'format': 'json'
            }
        elif format == "markdown":
            # Convert to markdown (simplified)
            md_report = f"""# Document Analysis Report

## Document Information
- **Filename**: {report['document_info']['filename']}
- **Type**: {report['document_info']['file_type']}
- **Size**: {report['document_info']['file_size']} bytes
- **Uploaded**: {report['document_info']['upload_date']}

## Classification
- **Category**: {report['classification'].get('category', 'unknown')}
- **Confidence**: {report['classification'].get('confidence', 0):.2%}

## Sentiment Analysis
- **Overall Sentiment**: {report['sentiment'].get('overall_sentiment', 'neutral')}
- **Average Score**: {report['sentiment'].get('average_score', 0):.2f}

## Entities
- **Total Entities**: {report['entities'].get('total_entities', 0)}
- **Entity Types**: {', '.join(report['entities'].get('entity_types', []))}

## Key Insights
{insights.get('summary', 'No insights available')}

### Key Findings
{chr(10).join(f'- {finding}' for finding in insights.get('key_findings', []))}

### Recommendations
{chr(10).join(f'- {rec}' for rec in insights.get('recommendations', []))}

---
*Report generated on {report['generated_at']}*
"""
            
            return {
                'success': True,
                'data': md_report,
                'format': 'markdown'
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'markdown'")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")


from datetime import datetime