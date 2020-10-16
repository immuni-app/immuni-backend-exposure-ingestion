from prometheus_client import Counter, Gauge

from immuni_common.monitoring.core import NAMESPACE, Subsystem

BATCH_FILES_CREATED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="batch_files_created",
    documentation="Total number of created BatchFiles.",
)

BATCH_FILES_EU_CREATED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="batch_files_eu_created",
    documentation="Total number of created BatchFilesEU.",
)

BATCH_FILES_DELETED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="batch_files_deleted",
    documentation="Total number of deleted BatchFiles.",
)

BATCH_FILES_EU_DELETED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="batch_files_eu_deleted",
    documentation="Total number of deleted BatchFilesEU.",
)

KEYS_PROCESSED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="keys_processed",
    documentation="Total number of processed keys.",
)

KEYS_EU_PROCESSED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="keys_eu_processed",
    documentation="Total number of processed keys coming from EU.",
)

UPLOADS_DELETED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="uploads_deleted",
    documentation="Total number of deleted Uploads.",
)

UPLOADS_EU_DELETED = Counter(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="uploads_eu_deleted",
    documentation="Total number of deleted Uploads coming from EU.",
)

UPLOADS_ENQUEUED = Gauge(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="uploads_enqueued",
    documentation="Total number of Uploads still to be processed after completing a BatchFile.",
)

UPLOADS_EU_ENQUEUED = Gauge(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="uploads_eu_enqueued",
    documentation="Total number of Uploads coming from EU still to be processed after completing "
                  "a BatchFileEu.",
)
