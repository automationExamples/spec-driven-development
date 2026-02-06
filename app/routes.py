"""
API Routes - FastAPI endpoints for the test generator service.
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import config
from app.openapi_parser import parse_and_normalize, OpenAPIParseError
from app.generator import TestGenerator, get_llm_client
from app.runner import run_tests
from app.storage.db import get_database


router = APIRouter()


# Request/Response models
class SpecCreate(BaseModel):
    """Request to create a spec"""

    name: str
    content: str


class SpecResponse(BaseModel):
    """Response for spec operations"""

    id: str
    name: str
    title: str
    version: str
    endpoint_count: int
    created_at: str


class SpecDetailResponse(SpecResponse):
    """Detailed spec response with endpoints"""

    endpoints: list[dict]


class GenerateRequest(BaseModel):
    """Request to generate tests"""

    spec_id: str


class GenerationResponse(BaseModel):
    """Response for generation operations"""

    id: str
    spec_id: str
    status: str
    files: list[str]
    created_at: str


class RunRequest(BaseModel):
    """Request to run tests"""

    generation_id: str
    target_url: Optional[str] = None


class FailureInfo(BaseModel):
    """Information about a test failure"""

    name: str
    classname: str
    message: Optional[str] = None
    traceback: Optional[str] = None


class RunResponse(BaseModel):
    """Response for run operations"""

    id: str
    generation_id: str
    status: str
    passed: int
    failed: int
    skipped: int
    errors: int
    total: int
    duration: float
    created_at: str
    completed_at: Optional[str] = None


class RunDetailResponse(RunResponse):
    """Detailed run response with failures"""

    failures: list[FailureInfo]


# Health endpoint
@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Spec endpoints
@router.post("/specs", response_model=SpecResponse, status_code=status.HTTP_201_CREATED)
def create_spec(request: SpecCreate):
    """Upload and store an OpenAPI specification"""
    try:
        # Parse and normalize the spec
        normalized = parse_and_normalize(request.content)

        # Store in database
        db = get_database(config.DATABASE_PATH)
        spec = db.create_spec(
            name=request.name,
            raw_content=request.content,
            title=normalized.title,
            version=normalized.version,
            endpoint_count=len(normalized.endpoints),
        )

        return SpecResponse(
            id=spec.id,
            name=spec.name,
            title=spec.title,
            version=spec.version,
            endpoint_count=spec.endpoint_count,
            created_at=spec.created_at.isoformat(),
        )

    except OpenAPIParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid OpenAPI spec: {e}"
        )


@router.get("/specs", response_model=list[SpecResponse])
def list_specs():
    """List all stored specifications"""
    db = get_database(config.DATABASE_PATH)
    specs = db.list_specs()

    return [
        SpecResponse(
            id=s.id,
            name=s.name,
            title=s.title,
            version=s.version,
            endpoint_count=s.endpoint_count,
            created_at=s.created_at.isoformat(),
        )
        for s in specs
    ]


@router.get("/specs/{spec_id}", response_model=SpecDetailResponse)
def get_spec(spec_id: str):
    """Get detailed information about a specification"""
    db = get_database(config.DATABASE_PATH)
    spec = db.get_spec(spec_id)

    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spec with id '{spec_id}' not found",
        )

    # Parse to get endpoints
    normalized = parse_and_normalize(spec.raw_content)
    endpoints = [
        {
            "path": ep.path,
            "method": ep.method,
            "operation_id": ep.operation_id,
            "summary": ep.summary,
        }
        for ep in normalized.endpoints
    ]

    return SpecDetailResponse(
        id=spec.id,
        name=spec.name,
        title=spec.title,
        version=spec.version,
        endpoint_count=spec.endpoint_count,
        created_at=spec.created_at.isoformat(),
        endpoints=endpoints,
    )


@router.delete("/specs/{spec_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spec(spec_id: str):
    """Delete a specification"""
    db = get_database(config.DATABASE_PATH)
    if not db.delete_spec(spec_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spec with id '{spec_id}' not found",
        )


# Generation endpoints
@router.post(
    "/generate", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED
)
def generate_tests(request: GenerateRequest):
    """Generate pytest files from a specification"""
    db = get_database(config.DATABASE_PATH)

    # Get the spec
    spec = db.get_spec(request.spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spec with id '{request.spec_id}' not found",
        )

    try:
        # Parse the spec
        normalized = parse_and_normalize(spec.raw_content)

        # Generate tests
        generator = TestGenerator(
            llm_client=get_llm_client(), output_dir=config.GENERATED_TESTS_DIR
        )
        generated_files = generator.generate(normalized, request.spec_id)

        # Store generation record
        generation = db.create_generation(
            spec_id=request.spec_id,
            test_dir=str(config.GENERATED_TESTS_DIR / request.spec_id),
            files=[str(f) for f in generated_files],
        )

        return GenerationResponse(
            id=generation.id,
            spec_id=generation.spec_id,
            status=generation.status,
            files=[str(f) for f in generated_files],
            created_at=generation.created_at.isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tests: {e}",
        )


@router.get("/generations/{generation_id}", response_model=GenerationResponse)
def get_generation(generation_id: str):
    """Get information about a test generation"""
    db = get_database(config.DATABASE_PATH)
    generation = db.get_generation(generation_id)

    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation with id '{generation_id}' not found",
        )

    return GenerationResponse(
        id=generation.id,
        spec_id=generation.spec_id,
        status=generation.status,
        files=generation.files,
        created_at=generation.created_at.isoformat(),
    )


@router.get("/generations", response_model=list[GenerationResponse])
def list_generations(spec_id: Optional[str] = None):
    """List all generations, optionally filtered by spec_id"""
    db = get_database(config.DATABASE_PATH)
    generations = db.list_generations(spec_id)

    return [
        GenerationResponse(
            id=g.id,
            spec_id=g.spec_id,
            status=g.status,
            files=g.files,
            created_at=g.created_at.isoformat(),
        )
        for g in generations
    ]


# Run endpoints
@router.post("/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def create_run(request: RunRequest):
    """Execute generated tests and return results"""
    db = get_database(config.DATABASE_PATH)

    # Get the generation
    generation = db.get_generation(request.generation_id)
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation with id '{request.generation_id}' not found",
        )

    if generation.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generation is not completed",
        )

    target_url = request.target_url or config.DEFAULT_TARGET_URL

    # Create run record
    run = db.create_run(generation_id=request.generation_id, target_url=target_url)

    # Execute tests
    test_dir = Path(generation.test_dir)
    result = run_tests(
        test_dir=test_dir, base_url=target_url, timeout=config.TEST_TIMEOUT
    )

    # Update run with results
    status_str = "completed" if result.success else "failed"
    db.update_run(
        run_id=run.id,
        status=status_str,
        passed=result.passed,
        failed=result.failed,
        skipped=result.skipped,
        errors=result.errors,
        total=result.total,
        duration=result.duration,
        junit_xml_path=str(result.junit_xml_path) if result.junit_xml_path else None,
        results_json=json.dumps(result.to_dict()),
    )

    # Get updated run
    run = db.get_run(run.id)

    return RunResponse(
        id=run.id,
        generation_id=run.generation_id,
        status=run.status,
        passed=run.passed,
        failed=run.failed,
        skipped=run.skipped,
        errors=run.errors,
        total=run.total,
        duration=run.duration,
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str):
    """Get detailed results of a test run"""
    db = get_database(config.DATABASE_PATH)
    run = db.get_run(run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found",
        )

    # Parse failures from results_json
    failures = []
    if run.results_json:
        try:
            results = json.loads(run.results_json)
            for f in results.get("failures", []):
                failures.append(
                    FailureInfo(
                        name=f.get("name", ""),
                        classname=f.get("classname", ""),
                        message=f.get("message"),
                        traceback=f.get("traceback"),
                    )
                )
        except json.JSONDecodeError:
            pass

    return RunDetailResponse(
        id=run.id,
        generation_id=run.generation_id,
        status=run.status,
        passed=run.passed,
        failed=run.failed,
        skipped=run.skipped,
        errors=run.errors,
        total=run.total,
        duration=run.duration,
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        failures=failures,
    )


@router.get("/runs/{run_id}/junit")
def get_junit_xml(run_id: str):
    """Get raw JUnit XML for a run"""
    db = get_database(config.DATABASE_PATH)
    run = db.get_run(run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found",
        )

    if not run.junit_xml_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JUnit XML not available for this run",
        )

    junit_path = Path(run.junit_xml_path)
    if not junit_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="JUnit XML file not found"
        )

    return Response(content=junit_path.read_text(), media_type="application/xml")


@router.get("/runs", response_model=list[RunResponse])
def list_runs(generation_id: Optional[str] = None):
    """List all runs, optionally filtered by generation_id"""
    db = get_database(config.DATABASE_PATH)
    runs = db.list_runs(generation_id)

    return [
        RunResponse(
            id=r.id,
            generation_id=r.generation_id,
            status=r.status,
            passed=r.passed,
            failed=r.failed,
            skipped=r.skipped,
            errors=r.errors,
            total=r.total,
            duration=r.duration,
            created_at=r.created_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
        )
        for r in runs
    ]
