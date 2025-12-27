from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List
import shutil
from datetime import datetime

from config import settings
from database.mongodb import mongodb
from database.redis_cache import redis_client
from services.document_processor import DocumentProcessor
from utils.validators import validate_file

upload_router = APIRouter()
doc_processor = DocumentProcessor()

@upload_router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a document for processing
    
    Supports: PDF, PNG, JPG, JPEG, XLSX, XLS, CSV
    """
    try:
        # Validate file
        validation = validate_file(file, settings.MAX_UPLOAD_SIZE, settings.ALLOWED_EXTENSIONS)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['error'])
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = settings.UPLOAD_DIR / safe_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        doc_data = await doc_processor.process_document(str(file_path), file.filename)
        
        # Save to database
        doc_record = {
            'filename': file.filename,
            'stored_filename': safe_filename,
            'file_path': str(file_path),
            'file_type': Path(file.filename).suffix.lower(),
            'file_size': doc_data.get('file_size', 0),
            'text_content': doc_data.get('text_content', ''),
            'requires_ocr': doc_data.get('requires_ocr', False),
            'metadata': doc_data.get('metadata', {}),
            'document_hash': doc_data.get('document_hash', ''),
            'upload_date': datetime.utcnow(),
            'status': 'uploaded',
            'analysis_status': 'pending'
        }
        
        doc_id = await mongodb.insert_document(doc_record)
        
        # Apply OCR if needed (in background)
        if doc_data.get('requires_ocr'):
            background_tasks.add_task(apply_ocr_to_document, doc_id, str(file_path))
        
        return {
            'success': True,
            'message': 'Document uploaded successfully',
            'data': {
                'document_id': doc_id,
                'filename': file.filename,
                'file_type': doc_record['file_type'],
                'file_size': doc_record['file_size'],
                'requires_ocr': doc_record['requires_ocr'],
                'status': doc_record['status']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@upload_router.post("/upload/batch")
async def upload_multiple_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Upload multiple documents at once
    """
    try:
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
        
        results = []
        
        for file in files:
            try:
                # Validate file
                validation = validate_file(file, settings.MAX_UPLOAD_SIZE, settings.ALLOWED_EXTENSIONS)
                if not validation['valid']:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': validation['error']
                    })
                    continue
                
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = f"{timestamp}_{file.filename}"
                file_path = settings.UPLOAD_DIR / safe_filename
                
                # Save file
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Process document
                doc_data = await doc_processor.process_document(str(file_path), file.filename)
                
                # Save to database
                doc_record = {
                    'filename': file.filename,
                    'stored_filename': safe_filename,
                    'file_path': str(file_path),
                    'file_type': Path(file.filename).suffix.lower(),
                    'file_size': doc_data.get('file_size', 0),
                    'text_content': doc_data.get('text_content', ''),
                    'requires_ocr': doc_data.get('requires_ocr', False),
                    'metadata': doc_data.get('metadata', {}),
                    'upload_date': datetime.utcnow(),
                    'status': 'uploaded',
                    'analysis_status': 'pending'
                }
                
                doc_id = await mongodb.insert_document(doc_record)
                
                # Apply OCR if needed
                if doc_data.get('requires_ocr'):
                    background_tasks.add_task(apply_ocr_to_document, doc_id, str(file_path))
                
                results.append({
                    'filename': file.filename,
                    'success': True,
                    'document_id': doc_id
                })
                
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'message': f'Processed {len(results)} files',
            'results': results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@upload_router.get("/documents")
async def list_documents(skip: int = 0, limit: int = 50):
    """
    List all uploaded documents
    """
    try:
        documents = await mongodb.get_all_documents(skip, limit)
        
        # Convert ObjectId to string
        for doc in documents:
            doc['_id'] = str(doc['_id'])
            doc['upload_date'] = doc.get('upload_date', datetime.utcnow()).isoformat()
        
        return {
            'success': True,
            'data': {
                'documents': documents,
                'total': len(documents),
                'skip': skip,
                'limit': limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@upload_router.get("/document/{document_id}")
async def get_document(document_id: str):
    """
    Get document details by ID
    """
    try:
        # Check cache first
        cached = await redis_client.get_cached_document(document_id)
        if cached:
            return {
                'success': True,
                'data': cached,
                'cached': True
            }
        
        # Get from database
        document = await mongodb.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Convert ObjectId to string
        document['_id'] = str(document['_id'])
        document['upload_date'] = document.get('upload_date', datetime.utcnow()).isoformat()
        
        # Cache result
        await redis_client.cache_document(document_id, document)
        
        return {
            'success': True,
            'data': document,
            'cached': False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


@upload_router.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document
    """
    try:
        # Get document first
        document = await mongodb.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file
        file_path = Path(document.get('file_path', ''))
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        deleted = await mongodb.delete_document(document_id)
        
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
        # Clear cache
        await redis_client.delete(f"doc:{document_id}")
        
        return {
            'success': True,
            'message': 'Document deleted successfully',
            'document_id': document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@upload_router.get("/statistics")
async def get_statistics():
    """
    Get database statistics
    """
    try:
        stats = await mongodb.get_statistics()
        
        return {
            'success': True,
            'data': stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# Background task functions
async def apply_ocr_to_document(document_id: str, file_path: str):
    """
    Background task to apply OCR to document
    """
    try:
        ocr_result = await doc_processor.apply_ocr(file_path)
        
        # Update document with OCR text
        await mongodb.update_document(document_id, {
            'text_content': ocr_result.get('text', ''),
            'ocr_confidence': ocr_result.get('confidence', 0.0),
            'ocr_applied': True,
            'status': 'processed'
        })
        
        # Clear cache
        await redis_client.delete(f"doc:{document_id}")
        
        print(f"✅ OCR completed for document {document_id}")
        
    except Exception as e:
        print(f"❌ OCR failed for document {document_id}: {e}")
        await mongodb.update_document(document_id, {
            'status': 'ocr_failed',
            'error': str(e)
        })