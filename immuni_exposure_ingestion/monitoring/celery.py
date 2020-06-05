from prometheus_client import Counter, Gauge

from immuni_common.monitoring.core import NAMESPACE, Subsystem

BATCH_FILES_CREATED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="batch_files_created",
    documentation="Total number of created BatchFiles.",
)

BATCH_FILES_DELETED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="batch_files_deleted",
    documentation="Total number of deleted BatchFiles.",
)

KEYS_PROCESSED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="keys_processed",
    documentation="Total number of processed keys.",
)

UPLOADS_DELETED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="uploads_deleted",
    documentation="Total number of deleted Uploads.",
)

UPLOADS_ENQUEUED = Gauge(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="uploads_enqueued",
    documentation="Total number of Uploads still to be processed after completing a BatchFile.",
)
