import json
import logging
import uuid
from datetime import datetime, timezone

import requests
import werkzeug.wrappers
from fastapi import APIRouter
from jose import jwt

from odoo import fields, http, models
from odoo.http import request
from odoo.tools import date_utils

from odoo.addons.graphql_base import GraphQLControllerMixin

from ..schema import schema
from ..tools import constants

_logger = logging.getLogger(__name__)


class TestFastapiEndpoint(models.Model):

    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("social_registry", "Social Registry Endpoint")],
        ondelete={"social_registry": "cascade"},
    )

    def _get_fastapi_routers(self):
        if self.app == "social_registry":
            return [social_registry_api_router]
        return super()._get_fastapi_routers()


social_registry_api_router = APIRouter()

cache_jwks = {}


def verify_and_decode_signature(token, iss_uri, jwks_uri):
    try:
        if not cache_jwks:
            jwks_res = requests.get(jwks_uri)
            jwks_res.raise_for_status()
            cache_jwks.update(jwks_res.json())

        return True, jwt.decode(
            token,
            cache_jwks,
            options={
                "verify_aud": False,
                "verify_iss": False,
                "verify_sub": False,
            },
        )
    except Exception as e:
        return False, str(e)


def response_wrapper(status, data):
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data, default=date_utils.json_default) if data else None,
    )


def error_wrapper(code, message):
    error = {"error": {"code": code, "message": message}}
    return response_wrapper(code, error)


def get_auth_header(headers, raise_exception=False):
    auth_header = headers.get("Authorization") or headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        if raise_exception:
            error = {
                "error": "Unauthorized",
                "error_description": "Your token could not be authenticated.",
            }
            return response_wrapper(401, error)
    return auth_header


class G2PDciApiServer(http.Controller, GraphQLControllerMixin):
    @http.route(
        constants.SYNC_SEARCH_ENDPOINT,
        auth="none",
        methods=["POST"],
        type="http",
        csrf=False,
    )
    # @social_registry_api_router.post(constants.SYNC_SEARCH_ENDPOINT)
    def retrieve_registry(self, **kw):
        auth_header = get_auth_header(request.httprequest.headers, raise_exception=True)
        access_token = auth_header.replace("Bearer ", "").replace("\\n", "")

        iss_uri = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_social_registry_auth_iss", "")
        )
        jwks_uri = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_social_registry_auth_jwks_uri", "")
        )
        verified, payload = verify_and_decode_signature(access_token, iss_uri, jwks_uri)

        if not verified:
            return error_wrapper(401, "Invalid Access Token.")

        req = http.request

        data = req.httprequest.data or "{}"
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            return error_wrapper(400, "data must be in JSON format.")

        header = data.get("header", "")

        header_error = self.check_content(
            header,
            "header",
            ["message_id", "message_ts", "action", "sender_id", "total_count"],
        )
        if header_error:
            return error_wrapper(header_error.get("code"), header_error.get("message"))

        message = data.get("message", "")
        message_error = self.check_content(
            message, "message", ["transaction_id", "search_request"]
        )
        if message_error:
            return error_wrapper(
                message_error.get("code"), message_error.get("message")
            )

        message_id = header["message_id"]
        transaction_id = message.get("transaction_id")
        search_requests = message["search_request"]

        today_isoformat = datetime.now(timezone.utc).isoformat()
        correlation_id = str(uuid.uuid4())

        # Process search requests and modify search_responses
        search_responses = []
        self.process_search_requests(search_requests, today_isoformat, search_responses)

        header = {
            "message_id": message_id,
            "message_ts": today_isoformat,
            "action": "search",
            "status": "succ",
        }
        message = {
            "transaction_id": transaction_id,
            "correlation_id": correlation_id,
            "search_response": search_responses,
        }

        data = {
            "header": header,
            "message": message,
        }
        return response_wrapper(200, data)

    def check_content(self, content, label, required_parameters):
        if not content:
            return {"code": 400, "message": f"{label} is required."}

        for param in required_parameters:
            if param not in content:
                parameter_str = ", ".join(required_parameters)
                return {
                    "code": 400,
                    "message": f"{label} should have these parameters: {parameter_str}",
                }

        return None

    def process_queries(self, query_type, queries, graphql_schema, error=None):
        for query in queries:

            if query_type == constants.GRAPHQL:
                query_error = self.check_content(query, "query", ["expression1"])
                if query_error:
                    return error_wrapper(
                        query_error.get("code"), query_error.get("message")
                    )
                expression = query.get("expression1")
                response = self._process_request(
                    graphql_schema, data={"query": expression}
                )

                response_error = json.loads(response.data).get("errors", "")
                if response_error:
                    _logger.error("Error in the query result", response_error)
                    error = True
                    return error, response_error

                return error, json.loads(response.data)["data"]

    def process_search_requests(
        self, search_requests, today_isoformat, search_responses
    ):
        for req in search_requests:
            req_error = self.check_content(
                req, "search_request", ["reference_id", "timestamp", "search_criteria"]
            )
            if req_error:
                return error_wrapper(req_error.get("code"), req_error.get("message"))

            search_criteria = req.get("search_criteria")
            search_criteria_error = self.check_content(
                search_criteria, "search_criteria", ["reg_type", "query_type", "query"]
            )
            if search_criteria_error:
                return error_wrapper(
                    search_criteria_error.get("code"),
                    search_criteria_error.get("message"),
                )

            query_type = search_criteria.get("query_type")
            if query_type not in constants.ALLOWED_QUERY_TYPE:
                return error_wrapper(
                    400,
                    f"query_type only accepts these values: {', '.join(constants.ALLOWED_QUERY_TYPE)}",
                )

            reg_type = search_criteria.get("reg_type")

            if reg_type not in constants.REG_TYPE_CHOICES:
                return error_wrapper(
                    400,
                    f"These are the only supported reg type: {', '.join(constants.REG_TYPE_CHOICES)}",
                )

            reference_id = req.get("reference_id")
            queries = search_criteria.get("query")

            # Process Queries
            error, query_result = self.process_queries(
                query_type, queries, schema.graphql_schema, None
            )

            if query_result and not error:
                search_responses.append(
                    {
                        "reference_id": reference_id,
                        "timestamp": today_isoformat,
                        "status": "succ",
                        "data": {
                            "reg_record_type": "person",
                            "reg_type": reg_type,
                            "reg_record": query_result,
                        },
                        "locale": "eng",
                    }
                )

        return search_responses
