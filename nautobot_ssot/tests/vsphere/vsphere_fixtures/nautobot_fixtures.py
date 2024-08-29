"""Nautobot Object Fixtures."""
import os
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.dcim.models import Location, LocationType
from nautobot.extras.models import Role, Status
from nautobot.tenancy.models import Tenant
from nautobot.virtualization.models import (
    Cluster,  # VMInterface,
    ClusterGroup,
    ClusterType,
    VirtualMachine,
)
from nautobot_ssot.integrations.vsphere.utilities import VsphereClient

LOCALHOST = os.environ.get("TEST_LOCALHOST_URL", "https://vcenter.local")
DEFAULT_VM_STATUS_MAP = {
    "POWERED_OFF": "Offline",
    "POWERED_ON": "Active",
    "SUSPENDED": "Suspended",
}
DEFAULT_IP_STATUS_MAP = {"PREFERRED": "Active", "UNKNOWN": "Reserved"}
DEFAULT_VM_INTERFACE_MAP = {"NOT_CONNECTED": False, "CONNECTED": True}
DEFAULT_PRIMARY_IP_SORT = "Lowest"
DEFAULT_IGNORE_LINK_LOCAL = True


def localhost_client_vsphere(localhost_url):
    """Return InfobloxAPI client for testing."""
    return VsphereClient(  # nosec
        vsphere_uri=localhost_url,
        username="test-user",
        password="test-password",
        verify_ssl=False,
        vm_status_map=DEFAULT_VM_STATUS_MAP,
        ip_status_map=DEFAULT_IP_STATUS_MAP,
        vm_interface_map=DEFAULT_VM_INTERFACE_MAP,
        primary_ip_sort_by=DEFAULT_PRIMARY_IP_SORT,
        ignore_link_local=DEFAULT_IGNORE_LINK_LOCAL,
        debug=False,
    )
