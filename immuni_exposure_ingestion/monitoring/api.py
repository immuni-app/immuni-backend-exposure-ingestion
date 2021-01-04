from prometheus_client.metrics import Counter

from immuni_common.monitoring.core import NAMESPACE, Subsystem

# NOTE: To monitor uploads / OTP request, adding the dummy and province information is important.
#  The currently existing metric "REQUESTS_LATENCY" is not enough, and adding such labels to all
#  requests would be inappropriate, since meaningless for most of them.
#  Dedicated metrics are added instead.

CHECK_OTP_REQUESTS = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="check_otp_requests",
    labelnames=("dummy", "http_status"),
    documentation="Number of check-otp requests the server responded to.",
)

CHECK_CUN_REQUESTS = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="check_cun_requests",
    labelnames=("dummy", "http_status"),
    documentation="Number of check-cun requests the server responded to.",
)

UPLOAD_REQUESTS = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="upload_requests",
    labelnames=("dummy", "province", "http_status"),
    documentation="Number of upload requests the server responded to.",
)

SUMMARIES_PROCESSED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="summaries_processed",
    documentation="Total number of summaries forwarded to immuni_backend_analytics.",
)
