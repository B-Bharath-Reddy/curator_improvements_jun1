from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from opentelemetry.trace import Status, StatusCode, SpanKind

from app.config import settings
from app.curator_models import (
    CuratorReviewRequest,
    CuratorFeedbackResponse,
    ReflectorRow,
)
from app.curator_service import curate_feedback
from app.curator_input_store import bigquery_input_store
from app.curator_output_store import curator_output_store
from app.observability import setup_phoenix, get_tracer, shutdown_phoenix



@asynccontextmanager
async def lifespan(app: FastAPI):
    phoenix_enabled = os.getenv("PHOENIX_ENABLED", "false").lower() == "true"

    if phoenix_enabled:
        setup_phoenix(app)

    try:
        yield
    finally:
        if phoenix_enabled:
            shutdown_phoenix()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Curator Agent — normalizes Reflector events and builds DPO training examples",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "status":                   "ok",
        "app":                      settings.app_name,
        "version":                  settings.app_version,
        "bigquery_input_available": bigquery_input_store.is_available(),
        "bigquery_output_available": curator_output_store.is_available(),
    }


#  PRODUCTION endpoint
# Reflector POSTs { "request_id": "..." } here via curator_callback_url

# @app.post("/v1/ace/curator:review-human-feedback", response_model=CuratorFeedbackResponse)
# async def review_human_feedback(req: CuratorReviewRequest):
#     tracer = get_tracer()
#     with tracer.start_as_current_span("curator.request") as root_span:
#         root_span.set_attribute("curator.request_id", req.request_id)
#         root_span.set_attribute("curator.endpoint", "production")
#         try:
#             row = await bigquery_input_store.fetch_by_request_id(req.request_id)
#
#             if not row:
#                 raise HTTPException(
#                     status_code=404,
#                     detail=f"No data found for request_id={req.request_id}",
#                 )
#
#             reflector_row = ReflectorRow(**row)
#
#             return await curate_feedback(reflector_row, store_output=True)
#
#         except HTTPException:
#             raise
#         except (KeyError, ValueError) as e:
#             raise HTTPException(status_code=400, detail=str(e))
#         except Exception as e:
#             root_span.record_exception(e)
#             root_span.set_status(Status(StatusCode.ERROR, str(e)))
#             raise HTTPException(status_code=500, detail=str(e))



# @app.post("/v1/ace/curator:review-human-feedback", response_model=CuratorFeedbackResponse)
# async def review_human_feedback(req: CuratorReviewRequest):
#     tracer = get_tracer()
#     with tracer.start_as_current_span("curator.request") as root_span:
#         root_span.set_attribute("curator.request_id", req.request_id)
#         root_span.set_attribute("curator.endpoint", "production")
#
#         try:
#             row = await bigquery_input_store.fetch_by_request_id(req.request_id)
#
#             if not row:
#                 # Tell the trace this was a 404 error
#                 root_span.set_status(Status(StatusCode.ERROR, "No data found"))
#                 raise HTTPException(
#                     status_code=404,
#                     detail=f"No data found for request_id={req.request_id}",
#                 )
#
#             reflector_row = ReflectorRow(**row)
#
#             # 1. SAVE the response to a variable first
#             response = await curate_feedback(reflector_row, store_output=True)
#
#             # 2. SET the green OK status!
#             root_span.set_status(Status(StatusCode.OK))
#
#             # 3. RETURN the response
#             return response
#
#         except HTTPException:
#             raise
#         except (KeyError, ValueError) as e:
#             # Tell the trace this was a 400 validation error
#             root_span.record_exception(e)
#             root_span.set_status(Status(StatusCode.ERROR, "Validation Error"))
#             raise HTTPException(status_code=400, detail=str(e))
#         except Exception as e:
#             root_span.record_exception(e)
#             root_span.set_status(Status(StatusCode.ERROR, str(e)))
#             raise HTTPException(status_code=500, detail=str(e))









# # ... existing code ...
# @app.post("/v1/ace/curator:review-human-feedback", response_model=CuratorFeedbackResponse)
# async def review_human_feedback(req: CuratorReviewRequest):
#     tracer = get_tracer()
#     with tracer.start_as_current_span("curator.request", kind=SpanKind.SERVER) as root_span:
#         # Set input.value attribute with stringified JSON payload
#         root_span.set_attribute("input.value", req.model_dump_json())
#         root_span.set_attribute("curator.request_id", req.request_id)
#         root_span.set_attribute("curator.endpoint", "production")
#         root_span.set_attribute("span.kind", "server")
#         root_span.set_attribute("service.name", "curator-agent")
#         root_span.set_attribute("http.method", "POST")
#         root_span.set_attribute("http.url", "/v1/ace/curator:review-human-feedback")
#
#         try:
#             row = await bigquery_input_store.fetch_by_request_id(req.request_id)
#
#             if not row:
#                 # Tell the trace this was a 404 error
#                 root_span.set_status(Status(StatusCode.ERROR, "No data found"))
#                 raise HTTPException(
#                     status_code=404,
#                     detail=f"No data found for request_id={req.request_id}",
#                 )
#
#             reflector_row = ReflectorRow(**row)
#
#             # Add event for upstream decision annotation
#             root_span.add_event("upstream_decision", {"decision": reflector_row.decision or "unknown"})
#
#             # 1. SAVE the response to a variable first
#             response = await curate_feedback(reflector_row, store_output=True)
#
#             # Add events for upstream reward annotations
#             if response.reward_score is not None:
#                 root_span.add_event("upstream_reward_score", {"reward_score": response.reward_score})
#             if response.reward_label:
#                 root_span.add_event("upstream_reward_label", {"reward_label": response.reward_label})
#             if response.issue_codes:
#                 root_span.add_event("upstream_issue_codes", {"issue_codes": response.issue_codes})
#
#             # 2. SET the green OK status!
#             root_span.set_status(Status(StatusCode.OK))
#
#             # Set output.value attribute with stringified JSON response
#             root_span.set_attribute("output.value", response.model_dump_json())
#
#             # 3. RETURN the response
#             return response
#
#         except HTTPException:
#             raise
#         except (KeyError, ValueError) as e:
#             # Tell the trace this was a 400 validation error
#             root_span.record_exception(e)
#             root_span.set_status(Status(StatusCode.ERROR, "Validation Error"))
#             raise HTTPException(status_code=400, detail=str(e))
#         except Exception as e:
#             root_span.record_exception(e)
#             root_span.set_status(Status(StatusCode.ERROR, str(e)))
#             raise HTTPException(status_code=500, detail=str(e))


# ... existing code ...
@app.post("/v1/ace/curator:review-human-feedback", response_model=CuratorFeedbackResponse)
async def review_human_feedback(req: CuratorReviewRequest):
    tracer = get_tracer()
    with tracer.start_as_current_span("curator.request", kind=SpanKind.SERVER) as root_span:
        # Set input.value attribute with stringified JSON payload
        root_span.set_attribute("input.value", req.model_dump_json())
        root_span.set_attribute("curator.request_id", req.request_id)
        root_span.set_attribute("curator.endpoint", "production")
        root_span.set_attribute("span.kind", "server")
        root_span.set_attribute("service.name", "curator-agent")

        try:
            row = await bigquery_input_store.fetch_by_request_id(req.request_id)

            if not row:
                # SET STATUS BEFORE RAISING
                root_span.set_status(Status(StatusCode.ERROR, "No data found"))
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for request_id={req.request_id}",
                )

            reflector_row = ReflectorRow(**row)

            # Add event for upstream decision annotation
            root_span.add_event("upstream_decision", {"decision": reflector_row.decision or "unknown"})

            # 1. SAVE the response to a variable first
            response = await curate_feedback(reflector_row, store_output=True)

            # Add events for upstream reward annotations
            if response.reward_score is not None:
                root_span.add_event("upstream_reward_score", {"reward_score": response.reward_score})
            if response.reward_label:
                root_span.add_event("upstream_reward_label", {"reward_label": response.reward_label})
            if response.issue_codes:
                root_span.add_event("upstream_issue_codes", {"issue_codes": response.issue_codes})

            # Output BEFORE Status
            root_span.set_attribute("output.value", response.model_dump_json())

            # SET STATUS LAST in success path
            root_span.set_status(Status(StatusCode.OK))

            return response

        except HTTPException:
            # EMPTY HANDLER - status already set before raise
            raise
        except (KeyError, ValueError) as e:
            # SET STATUS BEFORE RAISING
            root_span.record_exception(e)
            root_span.set_status(Status(StatusCode.ERROR, "Validation Error"))
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # SET STATUS BEFORE RAISING
            root_span.record_exception(e)
            root_span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))







#  MANUAL TESTING endpoint
# POST the full ReflectorRow directly — no BigQuery fetch needed
# Use the real BigQuery row JSON you already have for testing

@app.post("/v1/ace/curator:review-human-feedback-direct", response_model=CuratorFeedbackResponse)
async def review_human_feedback_direct(req: ReflectorRow):
    try:
        # Direct endpoint is for local validation with full payload.
        # It bypasses BigQuery input fetch and still exercises the same curator logic.
        return await curate_feedback(req)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
