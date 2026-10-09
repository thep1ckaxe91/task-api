import logging
from typing import Any, Dict, List, Optional
from flask import Flask, Response, json, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

PROBLEM_JSON_MIME = "application/problem+json"


class ProblemException(Exception):
    """
    Exception conforming to RFC 7807 / RFC 9457 Problem Details for HTTP APIs.
    https://datatracker.ietf.org/doc/html/rfc7807
    """

    def __init__(
        self,
        status: int,
        title: str,
        detail: Optional[str] = None,
        problem_type: Optional[str] = None,
        instance: Optional[str] = None,
        invalid_params: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(detail or title)
        self.status = status
        self.title = title
        self.detail = detail or title
        self.problem_type = problem_type or f"https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{status}"
        self.instance = instance or (request.path if request else None)
        self.invalid_params = invalid_params

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "type": self.problem_type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
        }
        if self.instance:
            data["instance"] = self.instance
        if self.invalid_params is not None:
            data["invalid_params"] = self.invalid_params
        return data

    def to_response(self) -> Response:
        return Response(
            response=json.dumps(self.to_dict()),
            status=self.status,
            mimetype=PROBLEM_JSON_MIME,
        )


def make_problem_response(
    status: int,
    title: str,
    detail: Optional[str] = None,
    problem_type: Optional[str] = None,
    instance: Optional[str] = None,
    invalid_params: Optional[List[Dict[str, Any]]] = None,
) -> Response:
    """Helper function to create an RFC 7807 Response directly."""
    problem = ProblemException(
        status=status,
        title=title,
        detail=detail,
        problem_type=problem_type,
        instance=instance,
        invalid_params=invalid_params,
    )
    return problem.to_response()


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers enforcing RFC 7807 Problem Details."""

    @app.errorhandler(ProblemException)
    def handle_problem_exception(error: ProblemException):
        return error.to_response()

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        # Werkzeug HTTPException handler (e.g. 404, 405, 400)
        return make_problem_response(
            status=error.code or 500,
            title=error.name,
            detail=error.description,
            instance=request.path,
        )

    # If Marshmallow is installed and raises ValidationError
    try:
        from marshmallow import ValidationError

        @app.errorhandler(ValidationError)
        def handle_marshmallow_validation_error(error: ValidationError):
            invalid_params = []
            if isinstance(error.messages, dict):
                for field, msgs in error.messages.items():
                    msg_text = msgs[0] if isinstance(msgs, list) and msgs else str(msgs)
                    invalid_params.append({"name": field, "reason": msg_text})
            else:
                invalid_params.append({"name": "body", "reason": str(error.messages)})

            return make_problem_response(
                status=422,
                title="Unprocessable Entity",
                detail="Request payload validation failed.",
                instance=request.path,
                invalid_params=invalid_params,
            )
    except ImportError:
        pass

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        logger.exception("Unhandled server exception: %s", str(error))
        return make_problem_response(
            status=500,
            title="Internal Server Error",
            detail="An unexpected error occurred while processing the request.",
            instance=request.path,
        )
