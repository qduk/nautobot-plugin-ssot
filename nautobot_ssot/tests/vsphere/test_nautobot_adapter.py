"""Nautobot Adapter Tests"""

from unittest.mock import MagicMock
from django.test import TestCase

from nautobot.extras.models.statuses import Status
from nautobot.extras.models.tags import Tag
from nautobot.virtualization.models import Cluster, ClusterType, ClusterGroup, VirtualMachine, VMInterface
from nautobot_ssot.integrations.vsphere.diffsync.adapters.adapter_nautobot import Adapter
from nautobot_ssot.integrations.vsphere.diffsync.models.vsphere import (
    ClusterGroupModel,
    ClusterModel,
    VirtualMachineModel,
    VMInterfaceModel,
)


class TestNautobotAdapter(TestCase):
    """Test cases for vSphere Nautobot adapter."""

    def setUp(self):
        test_cluster_type, _ = ClusterType.objects.get_or_create(name="Test")
        self.test_cluster_group, _ = ClusterGroup.objects.get_or_create(name="Test Group")
        self.test_cluster, _ = Cluster.objects.get_or_create(
            name="Test Cluster", cluster_type=test_cluster_type, cluster_group=self.test_cluster_group
        )
        self.status, _ = Status.objects.get_or_create(name="Active")
        self.tags = [Tag.objects.create(name=tag_name) for tag_name in ["Tag Test 1", "Tag Test 2", "Tag Test 3"]]
        self.test_virtualmachine, _ = VirtualMachine.objects.get_or_create(
            name="Test VM", cluster=self.test_cluster, status=self.status, vcpus=2, memory=4094, disk=50
        )
        self.test_virtualmachine.tags.set(self.tags)
        self.vm_interface_1 = VMInterface.objects.get_or_create(
            name="Test Interface",
            enabled=True,
            virtual_machine=self.test_virtualmachine,
            mac_address="AA:BB:CC:DD:EE:FF",
            status=self.status,
        )

    def test_load(self):
        adapter = Adapter(job=MagicMock())
        adapter.load()
        # ClusterGroup Asserts
        diffsync_clustergroup = adapter.get(ClusterGroupModel, {"name": "Test Group"})
        self.assertEqual(diffsync_clustergroup.name, "Test Group")
        # Cluster Asserts
        diffsync_cluster = adapter.get(ClusterModel, {"name": "Test Cluster"})
        self.assertEqual(diffsync_cluster.name, "Test Cluster")
        self.assertEqual(diffsync_cluster.cluster_type__name, "Test")
        self.assertEqual(diffsync_cluster.cluster_group__name, "Test Group")
        # VirtualMachine Asserts
        diffsync_virtualmachine = adapter.get(VirtualMachineModel, {"name": "Test VM"})
        self.assertEqual(diffsync_virtualmachine.name, "Test VM")
        self.assertEqual(diffsync_virtualmachine.cluster__name, "Test Cluster")
        self.assertEqual(diffsync_virtualmachine.status__name, "Active")
        self.assertEqual(diffsync_virtualmachine.vcpus, 2)
        self.assertEqual(diffsync_virtualmachine.memory, 4094)
        self.assertEqual(diffsync_virtualmachine.disk, 50)

        # VMInterface Asserts
        diffsync_vminterface = adapter.get(
            VMInterfaceModel, {"name": "Test Interface", "virtual_machine__name": "Test VM"}
        )
        self.assertEqual(diffsync_vminterface.name, "Test Interface")
        self.assertEqual(diffsync_vminterface.virtual_machine__name, "Test VM")
        self.assertEqual(diffsync_vminterface.enabled, True)
        self.assertEqual(diffsync_vminterface.mac_address, "AA:BB:CC:DD:EE:FF")
