"""
Django Models for recording the status and progress of data synchronization between data sources.

The interaction between these models and Nautobot's native JobResult model deserves some examination.

- A JobResult is created each time a data sync is requested.
  - This stores a reference to the specific sync operation requested (JobResult.name),
    much as a Job-related JobResult would reference the name of the Job.
  - This stores a 'job_id', which this plugin uses to reference the specific sync instance.
  - This stores the 'created' and 'completed' timestamps, and the requesting user (if any)
  - This stores the overall 'status' of the job (pending, running, completed, failed, errored.)
  - This stores a 'data' field which, in theory can store arbitrary JSON data, but in practice
    expects a fairly strict structure for logging of various status messages.
    This field is therefore not suitable for storage of in-depth data synchronization log messages,
    which have a different set of content requirements, but is used for high-level status reporting.

JobResult 1-->1 Sync 1-->n SyncLogEntry 1-->1 ObjectChange
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from nautobot.core.models import BaseModel
from nautobot.extras.models import ChangeLoggedModel, CustomFieldModel, JobResult, ObjectChange, RelationshipModel

from .choices import SyncLogEntryActionChoices, SyncLogEntryStatusChoices


class Sync(BaseModel, ChangeLoggedModel, CustomFieldModel, RelationshipModel):
    """High-level overview of a data sync event/process/attempt.

    Essentially an extension of the JobResult model to add a few additional fields.
    """

    dry_run = models.BooleanField(
        default=False, help_text="Report what data would be synced but do not make any changes"
    )
    diff = models.JSONField()
    job_result = models.ForeignKey(to=JobResult, on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def get_absolute_url(self):
        return reverse("plugins:nautobot_data_sync:sync", kwargs={"pk": self.pk})


class SyncLogEntry(BaseModel):
    """Record of a single event during a data sync operation.

    Detailed sync logs are recorded in this model, rather than in JobResult.data, because
    JobResult.data imposes fairly strict expectations about the structure of its contents
    that do not align well with the requirements of this plugin.

    This model somewhat "shadows" Nautobot's built-in ObjectChange model; the key distinction to
    bear in mind is that an ObjectChange reflects a change that *did happen*, while a SyncLogEntry
    may reflect this or may reflect a change that *could not happen* or *failed*.
    """

    sync = models.ForeignKey(
        to=Sync, on_delete=models.CASCADE, related_name="logs", related_query_name="log"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    action = models.CharField(max_length=32, choices=SyncLogEntryActionChoices)
    status = models.CharField(max_length=32, choices=SyncLogEntryStatusChoices)
    diff = models.JSONField()

    changed_object_type = models.ForeignKey(
        to=ContentType, blank=True, null=True, on_delete=models.PROTECT,
    )
    changed_object_id = models.UUIDField(blank=True, null=True)
    changed_object = GenericForeignKey(ct_field="changed_object_type", fk_field="changed_object_id")

    object_repr = models.CharField(max_length=200, editable=False)
    object_change = models.ForeignKey(to=ObjectChange, on_delete=models.SET_NULL, blank=True, null=True)

    message = models.CharField(max_length=511, blank=True)

    @property
    def dry_run(self):
        return self.overview.dry_run

    class Meta:
        verbose_name_plural = "sync log entries"
        ordering = ["sync", "timestamp"]

    def get_action_class(self):
        """Map self.action to a Bootstrap label class."""
        return {
            SyncLogEntryActionChoices.ACTION_NO_CHANGE: "default",
            SyncLogEntryActionChoices.ACTION_CREATE: "success",
            SyncLogEntryActionChoices.ACTION_UPDATE: "info",
            SyncLogEntryActionChoices.ACTION_DELETE: "warning",
        }.get(self.action)

    def get_status_class(self):
        """Map self.status to a Bootstrap label class."""
        return {
            SyncLogEntryStatusChoices.STATUS_SUCCESS: "success",
            SyncLogEntryStatusChoices.STATUS_FAILURE: "warning",
            SyncLogEntryStatusChoices.STATUS_ERROR: "danger",
        }.get(self.status)