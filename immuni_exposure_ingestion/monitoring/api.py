from prometheus_client.metrics import Counter

from immuni_common.monitoring.core import NAMESPACE, Subsystem

# Note: We want to be able to monitor uploads / OTP request, separate them by province and also make sure
# that there are not too many dummy requests.
# For the detail level that we want to achieve, the currently existing metric "REQUESTS_LATENCY"
# is insufficient, so we add more information through this metrics.

CHECK_OTP_REQUESTS = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="check_otp_requests",
    labelnames=("dummy", "http_status"),
    documentation="Number of check-otp requests the server responded to.",
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
