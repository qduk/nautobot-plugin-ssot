#  pylint: disable=keyword-arg-before-vararg
#  pylint: disable=too-few-public-methods
#  pylint: disable=too-many-locals
#  pylint: disable=abstract-method

"""Job for vSphere integration with SSoT app."""

from django.templatetags.static import static
from django.urls import reverse
from nautobot.core.forms import DynamicModelChoiceField
from nautobot.extras.jobs import BooleanVar
from nautobot.virtualization.models import Cluster

from nautobot_ssot.integrations.vsphere import defaults
from nautobot_ssot.integrations.vsphere.diffsync.adapters import Adapter, VsphereDiffSync
from nautobot_ssot.integrations.vsphere.utilities import VsphereClient
from nautobot_ssot.jobs.base import DataMapping, DataSource

name = "SSoT - Virtualization"  # pylint: disable=invalid-name


# class OptionalObjectVar(ScriptVariable):
#     """Custom implementation of an Optional ObjectVar.

#     An object primary key is returned and accessible in job kwargs.
#     """

#     form_field = DynamicModelChoiceField

#     def __init__(
#         self,
#         model=None,
#         display_field="display",
#         query_params=None,
#         null_option=None,
#         *args,
#         **kwargs,
#     ):
#         """Init."""
#         super().__init__(*args, **kwargs)

#         if model is not None:
#             self.field_attrs["queryset"] = model.objects.all()
#         else:
#             raise TypeError("ObjectVar must specify a model")

#         self.field_attrs.update(
#             {
#                 "display_field": display_field,
#                 "query_params": query_params,
#                 "null_option": null_option,
#             }
#         )


# pylint:disable=too-few-public-methods
class VspherecDataSource(DataSource):  # pylint: disable=too-many-instance-attributes
    """vSphere SSoT Data Source."""

    debug = BooleanVar(description="Enable for more verbose debug logging")
    sync_vsphere_tagged_only = BooleanVar(
        default=False,
        label="Sync Tagged Only",
        description="Only sync objects that have the 'ssot-synced-from-vsphere' tag.",
    )
    if defaults.DEFAULT_USE_CLUSTERS:
        cluster_filter = DynamicModelChoiceField(
            label="Only sync Nautobot records belonging to a single Cluster.",
            queryset=Cluster.objects.all(),
            required=False,
        )

    class Meta:
        """Metadata about this Job."""

        name = "VMWare vSphere ⟹ Nautobot"
        data_source = "VMWare vSphere"
        data_source_icon = static("nautobot_ssot_vsphere/vmware.png")
        description = "Sync data from VMWare vSphere into Nautobot."
        field_order = (
            "debug",
            "sync_vsphere_tagged_only",
            "dry_run",
        )

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return (
            DataMapping("Data Center", None, "ClusterGroup", reverse("virtualization:clustergroup_list")),
            DataMapping("Cluster", None, "Cluster", reverse("virtualization:cluster_list")),
            DataMapping("Virtual Machine", None, "Virtual Machine", reverse("virtualization:virtualmachine_list")),
            DataMapping("VM Interface", None, "VMInterface", reverse("virtualization:vminterface_list")),
            DataMapping("IP Addresses", None, "IP Addresses", reverse("ipam:ipaddress_list")),
        )

    @classmethod
    def config_information(cls):
        """Configuration of this DataSource."""
        return {
            "vSphere URI": defaults.VSPHERE_URI,
            "vSphere Username": defaults.VSPHERE_USERNAME,
            "vSphere Verify SSL": "False" if not defaults.VSPHERE_VERIFY_SSL else "True",
            "vSphere Cluster Type": defaults.DEFAULT_VSPHERE_TYPE,
            "Enforce ClusterGroup as Top Level": "False" if not defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL else "True",
            "Default Virtual Machine Status Map": defaults.DEFAULT_VM_STATUS_MAP,
            "Default VMInterface Enabled Map": defaults.VSPHERE_VM_INTERFACE_MAP,
            "Default IP Status Map": defaults.DEFAULT_IP_STATUS_MAP,
            "Primary IP Assignment": defaults.PRIMARY_IP_SORT_BY,
            "Default Use Clusers": defaults.DEFAULT_USE_CLUSTERS,
            "Default Cluster Name": defaults.DEFAULT_CLUSTER_NAME,
        }

    def log_debug(self, message):
        """Conditionally log a debug message."""
        if self.debug:
            self.logger.debug(message)

    def load_source_adapter(self):
        """Load vSphere adapter."""
        self.logger.info("Connecting to vSphere.")
        self.source_adapter = VsphereDiffSync(
            job=self,
            sync=self.sync,
            client=VsphereClient(),
            cluster_filter=self.cluster_filter_object,
        )
        self.logger.debug("Loading data from vSphere...")
        self.source_adapter.load()

    def load_target_adapter(self):
        """Load Nautobot Adapter."""
        self.target_adapter = Adapter(
            job=self,
            sync=self.sync,
            sync_vsphere_tagged_only=self.sync_vsphere_tagged_only,
            cluster_filter=self.cluster_filter_object,
        )

        self.logger.info(message="Loading current data from Nautobot...")
        self.target_adapter.load()

    def run(self, dryrun, debug, memory_profiling, sync_vsphere_tagged_only, cluster_filter=None, *args, **kwargs):  # pylint: disable=arguments-differ, too-many-arguments
        """Run sync."""
        self.dryrun = dryrun
        self.debug = debug
        self.memory_profiling = memory_profiling
        self.sync_vsphere_tagged_only = sync_vsphere_tagged_only
        self.cluster_filter = cluster_filter
        if defaults.DEFAULT_USE_CLUSTERS:
            self.cluster_filter_object = (  # pylint: disable=attribute-defined-outside-init
                Cluster.objects.get(pk=self.cluster_filter) if self.cluster_filter else None
            )
        else:
            self.logger.info(message="`DEFAULT_USE_CLUSTERS` is set to `False`")
            if defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL:
                self.logger.failure(
                    message="Cannot `ENFORCE_CLUSTER_GROUP_TOP_LEVEL` and disable `DEFAULT_USE_CLUSTERS`"
                )
                self.logger.info(
                    message="Set `ENFORCE_CLUSTER_GROUP_TOP_LEVEL` to `False` or `DEFAULT_USE_CLUSTERS` to `True`"
                )
        options = f"`Debug`: {self.debug}, `Dry Run`: {self.dryrun}, `Sync Tagged Only`: {self.sync_vsphere_tagged_only}, `Cluster Filter`: {self.cluster_filter_object}"  # NOQA
        self.logger.info(message=f"Starting job with the following options: {options}")
        return super().run(dryrun, memory_profiling, sync_vsphere_tagged_only, *args, **kwargs)


jobs = [VspherecDataSource]
