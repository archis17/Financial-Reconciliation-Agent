"""
FastAPI main application.
"""

import os
import uuid
import time
import logging
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from decimal import Decimal

from ingestion import IngestionService
from matching import MatchingEngine, MatchingConfig
from discrepancy import DiscrepancyDetector, DiscrepancyLLMIntegrator
from reporting import ReconciliationReportGenerator, TicketGenerator, TicketFormat
from reporting.models import ReconciliationReport
from llm_service import LLMExplanationService
from api.exceptions import (
    ValidationError,
    FileProcessingError,
    MatchingError,
    LLMServiceError,
    ResourceNotFoundError,
    ServiceUnavailableError
)
from api.middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware
)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state (in production, use Redis or database)
reconciliation_results = {}

# Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Financial Reconciliation API",
        description="AI-powered financial reconciliation agent API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # Add custom middleware (order matters - first added is last executed)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT_PER_MINUTE)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


app = create_app()


# Pydantic models for requests/responses
class ReconciliationRequest(BaseModel):
    """Request model for reconciliation."""
    amount_tolerance: float = Field(default=5.0, description="Amount tolerance in dollars")
    date_window_days: int = Field(default=7, description="Date window in days")
    min_confidence: float = Field(default=0.6, description="Minimum match confidence")
    enable_llm: bool = Field(default=True, description="Enable LLM explanations")
    min_severity_for_tickets: str = Field(default="low", description="Minimum severity for ticket creation")


class ReconciliationResponse(BaseModel):
    """Response model for reconciliation."""
    reconciliation_id: str
    status: str
    report_url: Optional[str] = None
    summary_url: Optional[str] = None
    readable_url: Optional[str] = None
    tickets_url: Optional[str] = None
    summary: dict
    tickets: List[dict] = []


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Financial Reconciliation API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # Check dependencies
    dependencies = {}
    
    # Check OpenAI (optional)
    try:
        from llm_service import LLMExplanationService
        llm_service = LLMExplanationService()
        dependencies["llm"] = "available" if llm_service.api_key else "not_configured"
    except Exception as e:
        dependencies["llm"] = f"error: {str(e)}"
    
    # Check file system
    try:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        test_file = upload_dir / ".health_check"
        test_file.write_text("test")
        test_file.unlink()
        dependencies["filesystem"] = "available"
    except Exception as e:
        dependencies["filesystem"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    health_status["dependencies"] = dependencies
    
    return health_status


@app.post("/api/ingest/bank", response_model=dict)
async def ingest_bank_statement(file: UploadFile = File(...)):
    """Ingest bank statement file."""
    # Validate file
    if not file.filename:
        raise ValidationError("Filename is required", field="file")
    
    if not file.filename.endswith(('.csv', '.CSV')):
        raise ValidationError("Only CSV files are supported", field="file")
    
    try:
        # Check file size
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise ValidationError(
                f"File size exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB",
                field="file",
                details={"max_size_mb": MAX_UPLOAD_SIZE_MB, "file_size_mb": len(content) / (1024 * 1024)}
            )
        
        # Save uploaded file temporarily
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        filepath = upload_dir / f"bank_{uuid.uuid4()}_{file.filename}"
        with open(filepath, "wb") as f:
            f.write(content)
        
        # Ingest
        service = IngestionService()
        result = service.ingest_bank_statement(str(filepath))
        
        return {
            "status": "success",
            "transactions_count": len(result.transactions),
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "stats": result.stats
        }
    
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error ingesting bank statement: {e}", exc_info=True)
        raise FileProcessingError(
            f"Failed to process bank statement: {str(e)}",
            filename=file.filename
        )


@app.post("/api/ingest/ledger", response_model=dict)
async def ingest_ledger(file: UploadFile = File(...)):
    """Ingest ledger file."""
    # Validate file
    if not file.filename:
        raise ValidationError("Filename is required", field="file")
    
    if not file.filename.endswith(('.csv', '.CSV')):
        raise ValidationError("Only CSV files are supported", field="file")
    
    try:
        # Check file size
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise ValidationError(
                f"File size exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB",
                field="file",
                details={"max_size_mb": MAX_UPLOAD_SIZE_MB, "file_size_mb": len(content) / (1024 * 1024)}
            )
        
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        filepath = upload_dir / f"ledger_{uuid.uuid4()}_{file.filename}"
        with open(filepath, "wb") as f:
            f.write(content)
        
        service = IngestionService()
        result = service.ingest_ledger(str(filepath))
        
        return {
            "status": "success",
            "transactions_count": len(result.transactions),
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "stats": result.stats
        }
    
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error ingesting ledger: {e}", exc_info=True)
        raise FileProcessingError(
            f"Failed to process ledger: {str(e)}",
            filename=file.filename
        )


@app.post("/api/reconcile", response_model=ReconciliationResponse)
async def reconcile(
    bank_file: UploadFile = File(...),
    ledger_file: UploadFile = File(...),
    amount_tolerance: float = Form(5.0),
    date_window_days: int = Form(7),
    min_confidence: float = Form(0.6),
    enable_llm: bool = Form(True),
    min_severity_for_tickets: str = Form("low")
):
    """Perform reconciliation."""
    # Validate parameters
    if amount_tolerance < 0:
        raise ValidationError("amount_tolerance must be non-negative", field="amount_tolerance")
    if date_window_days < 0:
        raise ValidationError("date_window_days must be non-negative", field="date_window_days")
    if not 0 <= min_confidence <= 1:
        raise ValidationError("min_confidence must be between 0 and 1", field="min_confidence")
    if min_severity_for_tickets not in ["low", "medium", "high", "critical"]:
        raise ValidationError(
            "min_severity_for_tickets must be one of: low, medium, high, critical",
            field="min_severity_for_tickets"
        )
    
    # Validate files
    if not bank_file.filename or not ledger_file.filename:
        raise ValidationError("Both bank_file and ledger_file are required")
    
    start_time = time.time()
    reconciliation_id = str(uuid.uuid4())
    
    try:
        # Save uploaded files with size validation
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        bank_filepath = upload_dir / f"bank_{reconciliation_id}_{bank_file.filename}"
        ledger_filepath = upload_dir / f"ledger_{reconciliation_id}_{ledger_file.filename}"
        
        bank_content = await bank_file.read()
        ledger_content = await ledger_file.read()
        
        if len(bank_content) > MAX_UPLOAD_SIZE_BYTES:
            raise ValidationError(
                f"Bank file size exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB",
                field="bank_file"
            )
        if len(ledger_content) > MAX_UPLOAD_SIZE_BYTES:
            raise ValidationError(
                f"Ledger file size exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB",
                field="ledger_file"
            )
        
        with open(bank_filepath, "wb") as f:
            f.write(bank_content)
        
        with open(ledger_filepath, "wb") as f:
            f.write(ledger_content)
        
        # Create config from parameters
        config = ReconciliationRequest(
            amount_tolerance=amount_tolerance,
            date_window_days=date_window_days,
            min_confidence=min_confidence,
            enable_llm=enable_llm,
            min_severity_for_tickets=min_severity_for_tickets
        )
        
        # 1. Ingest
        try:
            ingestion_service = IngestionService()
            bank_result = ingestion_service.ingest_bank_statement(str(bank_filepath))
            ledger_result = ingestion_service.ingest_ledger(str(ledger_filepath))
        except Exception as e:
            logger.error(f"Error during ingestion: {e}", exc_info=True)
            raise FileProcessingError(f"Failed to ingest files: {str(e)}")
        
        if not bank_result.transactions:
            raise ValidationError("Bank statement contains no valid transactions")
        if not ledger_result.transactions:
            raise ValidationError("Ledger contains no valid transactions")
        
        # 2. Match
        try:
            matching_config = MatchingConfig(
                amount_tolerance=Decimal(str(config.amount_tolerance)),
                date_window_days=config.date_window_days
            )
            matching_engine = MatchingEngine(matching_config=matching_config)
            match_result = matching_engine.match(
                bank_result.transactions,
                ledger_result.transactions,
                min_confidence=config.min_confidence
            )
        except Exception as e:
            logger.error(f"Error during matching: {e}", exc_info=True)
            raise MatchingError(f"Failed to match transactions: {str(e)}")
        
        # 3. Detect discrepancies
        try:
            detector = DiscrepancyDetector()
            discrepancy_result = detector.detect(
                bank_result.transactions,
                ledger_result.transactions,
                match_result
            )
        except Exception as e:
            logger.error(f"Error during discrepancy detection: {e}", exc_info=True)
            raise MatchingError(f"Failed to detect discrepancies: {str(e)}")
        
        # 4. Enhance with LLM (if enabled)
        llm_calls = 0
        llm_tokens = 0
        if config.enable_llm:
            try:
                llm_service = LLMExplanationService()
                integrator = DiscrepancyLLMIntegrator(llm_service=llm_service, enable_llm=True)
                
                bank_tx_dict = {tx.id: tx for tx in bank_result.transactions}
                ledger_tx_dict = {tx.id: tx for tx in ledger_result.transactions}
                
                enhanced = integrator.enhance_with_explanations(
                    discrepancy_result.discrepancies,
                    bank_tx_dict=bank_tx_dict,
                    ledger_tx_dict=ledger_tx_dict
                )
                discrepancy_result.discrepancies = enhanced
                
                stats = llm_service.get_usage_stats()
                llm_calls = stats["total_requests"]
                llm_tokens = stats["total_tokens_used"]
            except Exception as e:
                logger.warning(f"LLM enhancement failed: {e}")
                # Don't fail the entire reconciliation if LLM fails
                # Just log and continue without LLM explanations
        
        # 5. Create report
        processing_time = time.time() - start_time
        report = ReconciliationReport(
            reconciliation_id=reconciliation_id,
            run_at=datetime.now(),
            status="completed",
            bank_transactions_count=len(bank_result.transactions),
            ledger_transactions_count=len(ledger_result.transactions),
            matched_count=len(match_result.matches),
            unmatched_bank_count=len(match_result.unmatched_bank),
            unmatched_ledger_count=len(match_result.unmatched_ledger),
            discrepancy_count=len(discrepancy_result.discrepancies),
            processing_time_seconds=processing_time,
            llm_calls_made=llm_calls,
            llm_tokens_used=llm_tokens
        )
        
        # 6. Generate reports
        report_generator = ReconciliationReportGenerator(output_dir="reports")
        csv_path = report_generator.generate_csv_report(
            reconciliation_id,
            bank_result.transactions,
            ledger_result.transactions,
            match_result,
            discrepancy_result,
            report
        )
        summary_path = report_generator.generate_summary_report(
            reconciliation_id,
            report,
            match_result,
            discrepancy_result
        )
        readable_path = report_generator.generate_readable_report(
            reconciliation_id,
            report,
            match_result,
            discrepancy_result
        )
        
        # 7. Generate tickets
        from discrepancy.models import DiscrepancySeverity
        severity_map = {
            "low": DiscrepancySeverity.LOW,
            "medium": DiscrepancySeverity.MEDIUM,
            "high": DiscrepancySeverity.HIGH,
            "critical": DiscrepancySeverity.CRITICAL
        }
        min_severity = severity_map.get(config.min_severity_for_tickets, DiscrepancySeverity.LOW)
        
        ticket_generator = TicketGenerator()
        tickets = ticket_generator.generate_tickets_from_discrepancies(
            discrepancy_result.discrepancies,
            reconciliation_id,
            min_severity=min_severity
        )
        
        # Format tickets for response
        formatted_tickets = [
            ticket_generator.format_ticket(ticket, TicketFormat.N8N)
            for ticket in tickets
        ]
        
        # Store results
        reconciliation_results[reconciliation_id] = {
            "report": report,
            "match_result": match_result,
            "discrepancy_result": discrepancy_result,
            "tickets": tickets
        }
        
        return ReconciliationResponse(
            reconciliation_id=reconciliation_id,
            status="completed",
            report_url=f"/api/reports/{reconciliation_id}/csv",
            summary_url=f"/api/reports/{reconciliation_id}/summary",
            readable_url=f"/api/reports/{reconciliation_id}/readable",
            tickets_url=f"/api/tickets/{reconciliation_id}",
            summary={
                "matched": len(match_result.matches),
                "unmatched_bank": len(match_result.unmatched_bank),
                "unmatched_ledger": len(match_result.unmatched_ledger),
                "discrepancies": len(discrepancy_result.discrepancies),
                "processing_time": processing_time
            },
            tickets=formatted_tickets
        )
    
    except (ValidationError, FileProcessingError, MatchingError, LLMServiceError):
        # Re-raise custom exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error during reconciliation: {e}", exc_info=True)
        raise ServiceUnavailableError(f"Reconciliation failed: {str(e)}")


@app.get("/api/reports/{reconciliation_id}/csv")
async def get_csv_report(reconciliation_id: str):
    """Get CSV reconciliation report."""
    reports_dir = Path("reports")
    pattern = f"reconciliation_report_{reconciliation_id}_*.csv"
    
    files = list(reports_dir.glob(pattern))
    if not files:
        raise ResourceNotFoundError("CSV report", reconciliation_id)
    
    return FileResponse(
        files[0],
        media_type="text/csv",
        filename=files[0].name
    )


@app.get("/api/reports/{reconciliation_id}/summary")
async def get_summary_report(reconciliation_id: str):
    """Get JSON summary report."""
    reports_dir = Path("reports")
    pattern = f"reconciliation_summary_{reconciliation_id}_*.json"
    
    files = list(reports_dir.glob(pattern))
    if not files:
        raise ResourceNotFoundError("Summary report", reconciliation_id)
    
    return FileResponse(
        files[0],
        media_type="application/json",
        filename=files[0].name
    )


@app.get("/api/reports/{reconciliation_id}/readable")
async def get_readable_report(reconciliation_id: str):
    """Get readable text report."""
    reports_dir = Path("reports")
    pattern = f"reconciliation_readable_{reconciliation_id}_*.txt"
    
    files = list(reports_dir.glob(pattern))
    if not files:
        raise ResourceNotFoundError("Readable report", reconciliation_id)
    
    return FileResponse(
        files[0],
        media_type="text/plain",
        filename=files[0].name
    )


@app.get("/api/tickets/{reconciliation_id}")
async def get_tickets(
    reconciliation_id: str,
    format: str = "n8n"
):
    """Get tickets in specified format."""
    if reconciliation_id not in reconciliation_results:
        raise ResourceNotFoundError("Reconciliation", reconciliation_id)
    
    format_map = {
        "jira": TicketFormat.JIRA,
        "servicenow": TicketFormat.SERVICENOW,
        "n8n": TicketFormat.N8N,
        "generic": TicketFormat.GENERIC,
        "email": TicketFormat.EMAIL
    }
    
    if format.lower() not in format_map:
        raise ValidationError(
            f"Invalid format. Must be one of: {', '.join(format_map.keys())}",
            field="format"
        )
    
    tickets = reconciliation_results[reconciliation_id]["tickets"]
    ticket_generator = TicketGenerator()
    ticket_format = format_map[format.lower()]
    
    formatted_tickets = [
        ticket_generator.format_ticket(ticket, ticket_format)
        for ticket in tickets
    ]
    
    return JSONResponse(content=formatted_tickets)


@app.get("/api/reconciliation/{reconciliation_id}")
async def get_reconciliation(reconciliation_id: str):
    """Get reconciliation details."""
    if reconciliation_id not in reconciliation_results:
        raise ResourceNotFoundError("Reconciliation", reconciliation_id)
    
    data = reconciliation_results[reconciliation_id]
    return {
        "reconciliation_id": reconciliation_id,
        "report": data["report"].to_dict(),
        "summary": {
            "matches": len(data["match_result"].matches),
            "discrepancies": len(data["discrepancy_result"].discrepancies)
        }
    }

