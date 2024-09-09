"""Unit tests for vSphere SSoT DiffSync Models."""

import unittest
from unittest.mock import MagicMock

from diffsync.enum import DiffSyncFlags
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from nautobot.virtualization.models import (
    Cluster,
    ClusterGroup,
    ClusterType,
    VirtualMachine,
    VMInterface,
)

from nautobot_ssot.integrations.vsphere.diffsync.adapters.adapter_nautobot import (
    Adapter,
)
from nautobot_ssot.integrations.vsphere.diffsync.adapters.adapter_vsphere import (
    VsphereDiffSync,
)
from nautobot_ssot.integrations.vsphere.diffsync.models import ClusterGroupModel

from .vsphere_fixtures import create_default_vsphere_config


def _get_virtual_machine_dict(attrs):
    """Build dict used for creating diffsync Virtual Machine."""
    virtual_machine_dict = {
        "status__name": "Active",
        "vcpus": 3,
        "memory": 4096,
        "disk": 50,
        "cluster__name": "TestCluster",
        "primary_ip4__host": None,
        "primary_ip6__host": None,
    }
    virtual_machine_dict.update(attrs)
    return virtual_machine_dict


def _get_virtual_machine_interface_dict(attrs):
    """Build dict used for creating diffsync VM Interface."""
    vm_interface_dict = {
        "enabled": True,
        "status__name": "Active",
        "mac_address": "AA:BB:CC:DD:EE:FF",
    }
    vm_interface_dict.update(attrs)
    return vm_interface_dict


class TestVSphereDiffSyncModels(unittest.TestCase):
    """Test cases for vSphere DiffSync models."""

    def setUp(self):
        """Test class SetUp."""
        self.config = create_default_vsphere_config()
        self.vsphere_adapter = VsphereDiffSync(
            client=MagicMock(), config=self.config, cluster_filter=None
        )
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        ClusterType.objects.all().delete()
        ClusterGroup.objects.all().delete()
        IPAddress.objects.all().delete()
        Prefix.objects.all().delete()
        self.active_status, _ = Status.objects.get_or_create(name="Active")

    def test_clustergroup_creation(self):
        clustergroup_test = self.vsphere_adapter.clustergroup(name="TestClusterGroup")

        self.vsphere_adapter.add(clustergroup_test)

        nb_adapter = Adapter(config=self.config)
        nb_adapter.job = MagicMock()
        nb_adapter.load()
        self.vsphere_adapter.sync_to(nb_adapter)

        nb_clustergroup = ClusterGroup.objects.get(name="TestClusterGroup")
        self.assertEqual(nb_clustergroup.name, "TestClusterGroup")

    def test_cluster_creation(self):
        ClusterGroup.objects.create(name="TestClusterGroup")
        ClusterType.objects.create(name="VMWare vSphere")

        clustergroup_test = self.vsphere_adapter.clustergroup(name="TestClusterGroup")
        cluster_test = self.vsphere_adapter.cluster(
            name="TestCluster",
            cluster_group__name="TestClusterGroup",
            cluster_type__name="VMWare vSphere",
        )
        self.vsphere_adapter.add(clustergroup_test)
        self.vsphere_adapter.add(cluster_test)
        diff_clustergroup = self.vsphere_adapter.get(
            ClusterGroupModel, {"name": "TestClusterGroup"}
        )
        diff_clustergroup.add_child(cluster_test)

        nb_adapter = Adapter(config=self.config)
        nb_adapter.job = MagicMock()
        nb_adapter.load()
        self.vsphere_adapter.sync_to(nb_adapter)

        nb_cluster = Cluster.objects.get(name="TestCluster")
        self.assertEqual(nb_cluster.name, "TestCluster")
        self.assertEqual(nb_cluster.cluster_group.name, "TestClusterGroup")
        self.assertEqual(nb_cluster.cluster_type.name, "VMWare vSphere")

    def test_vm_creation(self):
        nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
        nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
        Cluster.objects.create(
            name="TestCluster",
            cluster_group=nb_clustergroup,
            cluster_type=nb_clustertype,
        )

        clustergroup_test = self.vsphere_adapter.clustergroup(name="TestClusterGroup")
        cluster_test = self.vsphere_adapter.cluster(
            name="TestCluster",
            cluster_group__name="TestClusterGroup",
            cluster_type__name="VMWare vSphere",
        )
        vm_test = self.vsphere_adapter.virtual_machine(
            **_get_virtual_machine_dict({"name": "TestVM"})
        )
        self.vsphere_adapter.add(clustergroup_test)
        self.vsphere_adapter.add(cluster_test)
        self.vsphere_adapter.add(vm_test)
        clustergroup_test.add_child(cluster_test)
        cluster_test.add_child(vm_test)

        nb_adapter = Adapter(config=self.config)
        nb_adapter.job = MagicMock()
        nb_adapter.load()
        self.vsphere_adapter.sync_to(nb_adapter)

        nb_vm = VirtualMachine.objects.get(name="TestVM")
        self.assertEqual(nb_vm.name, "TestVM")
        self.assertEqual(nb_vm.status.name, "Active")
        self.assertEqual(nb_vm.vcpus, 3)
        self.assertEqual(nb_vm.memory, 4096)
        self.assertEqual(nb_vm.disk, 50)
        self.assertEqual(nb_vm.cluster.name, "TestCluster")

    def test_vminterface_creation(self):
        nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
        nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
        Cluster.objects.create(
            name="TestCluster",
            cluster_group=nb_clustergroup,
            cluster_type=nb_clustertype,
        )

        clustergroup_test = self.vsphere_adapter.clustergroup(name="TestClusterGroup")
        cluster_test = self.vsphere_adapter.cluster(
            name="TestCluster",
            cluster_group__name="TestClusterGroup",
            cluster_type__name="VMWare vSphere",
        )
        vm_test = self.vsphere_adapter.virtual_machine(
            **_get_virtual_machine_dict({"name": "TestVM"})
        )
        vm_interface_test = self.vsphere_adapter.interface(
            **_get_virtual_machine_interface_dict(
                {"name": "Network Adapter 1", "virtual_machine__name": "TestVM"}
            )
        )
        self.vsphere_adapter.add(clustergroup_test)
        self.vsphere_adapter.add(cluster_test)
        self.vsphere_adapter.add(vm_test)
        self.vsphere_adapter.add(vm_interface_test)
        clustergroup_test.add_child(cluster_test)
        cluster_test.add_child(vm_test)
        vm_test.add_child(vm_interface_test)

        nb_adapter = Adapter(config=self.config)
        nb_adapter.job = MagicMock()
        nb_adapter.load()
        self.vsphere_adapter.sync_to(nb_adapter)

        nb_vminterface = VMInterface.objects.get(name="Network Adapter 1")
        self.assertEqual(nb_vminterface.name, "Network Adapter 1")
        self.assertEqual(nb_vminterface.enabled, True)
        self.assertEqual(nb_vminterface.virtual_machine.name, "TestVM")

    # def test_ipaddress_creation_existing_prefix(self):
    #     Prefix.objects.create(
    #         prefix="192.168.1.0/16",
    #         status=self.active_status,
    #         namespace=Namespace.objects.get(name="Global"),
    #         type="network",
    #     )
    #     nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
    #     nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
    #     Cluster.objects.create(
    #         name="TestCluster",
    #         cluster_group=nb_clustergroup,
    #         cluster_type=nb_clustertype,
    #     )

    #     clustergroup_test = self.vsphere_adapter.clustergroup(name="TestClusterGroup")
    #     cluster_test = self.vsphere_adapter.cluster(
    #         name="TestCluster",
    #         cluster_group__name="TestClusterGroup",
    #         cluster_type__name="VMWare vSphere",
    #     )
    #     vm_test = self.vsphere_adapter.virtual_machine(
    #         **_get_virtual_machine_dict({"name": "TestVM"})
    #     )
    #     vm_interface_test = self.vsphere_adapter.interface(
    #         **_get_virtual_machine_interface_dict(
    #             {"name": "Network Adapter 1", "virtual_machine__name": "TestVM"}
    #         )
    #     )
    #     vm_interface_ip = self.vsphere_adapter.ip_address(
    #         host="192.168.1.1",
    #         mask_length=24,
    #         status__name="Active",
    #         vm_interfaces=[{"name": "Network Adapter 1"}],
    #     )
    #     self.vsphere_adapter.add(clustergroup_test)
    #     self.vsphere_adapter.add(cluster_test)
    #     self.vsphere_adapter.add(vm_test)
    #     self.vsphere_adapter.add(vm_interface_test)
    #     self.vsphere_adapter.add(vm_interface_ip)
    #     clustergroup_test.add_child(cluster_test)
    #     cluster_test.add_child(vm_test)
    #     vm_test.add_child(vm_interface_test)
    #     vm_interface_test.add_child(vm_interface_ip)

    #     nb_adapter = Adapter(config=self.config)
    #     nb_adapter.job = MagicMock()
    #     nb_adapter.load()
    #     self.vsphere_adapter.sync_to(nb_adapter)

    #     nb_ip = IPAddress.objects.get(host="192.168.1.1", mask_length=24)
    #     self.assertEqual(nb_ip.host, "192.168.1.1")
    #     self.assertEqual(nb_ip.mask_length, 24)
    #     self.assertIn(
    #         "Network Adapter 1",
    #         [interface.name for interface in nb_ip.vm_interfaces.all()],
    #     )

    def test_ipaddress_creation_no_existing_prefix(self):
        nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
        nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
        Cluster.objects.create(
            name="TestCluster",
            cluster_group=nb_clustergroup,
            cluster_type=nb_clustertype,
        )

        clustergroup_test = self.vsphere_adapter.clustergroup(name="TestClusterGroup")
        cluster_test = self.vsphere_adapter.cluster(
            name="TestCluster",
            cluster_group__name="TestClusterGroup",
            cluster_type__name="VMWare vSphere",
        )
        vm_test = self.vsphere_adapter.virtual_machine(
            **_get_virtual_machine_dict({"name": "TestVM"})
        )
        vm_interface_test = self.vsphere_adapter.interface(
            **_get_virtual_machine_interface_dict(
                {"name": "Network Adapter 1", "virtual_machine__name": "TestVM"}
            )
        )
        vm_interface_ip = self.vsphere_adapter.ip_address(
            host="192.168.1.1",
            mask_length=24,
            status__name="Active",
            vm_interfaces=[{"name": "Network Adapter 1"}],
        )
        prefix_test = self.vsphere_adapter.prefix(
            network="192.168.1.0",
            prefix_length=24,
            namespace__name="Global",
            status__name="Active",
            type="network",
        )
        self.vsphere_adapter.add(clustergroup_test)
        self.vsphere_adapter.add(cluster_test)
        self.vsphere_adapter.add(vm_test)
        self.vsphere_adapter.add(vm_interface_test)
        self.vsphere_adapter.add(vm_interface_ip)
        self.vsphere_adapter.add(prefix_test)
        clustergroup_test.add_child(cluster_test)
        cluster_test.add_child(vm_test)
        vm_test.add_child(vm_interface_test)
        vm_interface_test.add_child(vm_interface_ip)

        nb_adapter = Adapter(config=self.config)
        nb_adapter.job = MagicMock()
        nb_adapter.load()
        self.vsphere_adapter.sync_to(nb_adapter)

        nb_ip = IPAddress.objects.get(host="192.168.1.1", mask_length=24)
        self.assertEqual(nb_ip.host, "192.168.1.1")
        self.assertEqual(nb_ip.mask_length, 24)
        self.assertIn(
            "Network Adapter 1",
            [interface.name for interface in nb_ip.vm_interfaces.all()],
        )

    def test_prefix_creation(self):
        prefix_test = self.vsphere_adapter.prefix(
            network="192.168.10.0",
            prefix_length=24,
            namespace__name="Global",
            status__name="Active",
            type="network",
        )
        self.vsphere_adapter.add(prefix_test)

        nb_adapter = Adapter(config=self.config)
        nb_adapter.job = MagicMock()
        nb_adapter.load()
        self.vsphere_adapter.sync_to(nb_adapter)

        nb_prefix = Prefix.objects.get(network="192.168.10.0", prefix_length=24)
        self.assertEqual(nb_prefix.network, "192.168.10.0")
        self.assertEqual(nb_prefix.prefix_length, 24)
        self.assertEqual(str(nb_prefix.prefix), "192.168.10.0/24")
        self.assertEqual(nb_prefix.namespace.name, "Global")
        self.assertEqual(nb_prefix.type, "network")

    def test_vm_creation_and_vm_primary_ip(self):
        nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
        nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
        Cluster.objects.create(
            name="TestCluster",
            cluster_group=nb_clustergroup,
            cluster_type=nb_clustertype,
        )

        clustergroup_test = self.vsphere_adapter.clustergroup(name="TestClusterGroup")
        cluster_test = self.vsphere_adapter.cluster(
            name="TestCluster",
            cluster_group__name="TestClusterGroup",
            cluster_type__name="VMWare vSphere",
        )
        vm_test = self.vsphere_adapter.virtual_machine(
            **_get_virtual_machine_dict(
                {"name": "TestVM", "primary_ip4__host": "192.168.1.1"}
            )
        )
        vm_interface_test = self.vsphere_adapter.interface(
            **_get_virtual_machine_interface_dict(
                {"name": "Network Adapter 1", "virtual_machine__name": "TestVM"}
            )
        )
        vm_interface_ip = self.vsphere_adapter.ip_address(
            host="192.168.1.1",
            mask_length=24,
            status__name="Active",
            vm_interfaces=[{"name": "Network Adapter 1"}],
        )
        prefix_test = self.vsphere_adapter.prefix(
            network="192.168.1.0",
            prefix_length=24,
            namespace__name="Global",
            status__name="Active",
            type="network",
        )
        self.vsphere_adapter.add(clustergroup_test)
        self.vsphere_adapter.add(cluster_test)
        self.vsphere_adapter.add(vm_test)
        self.vsphere_adapter.add(vm_interface_test)
        self.vsphere_adapter.add(vm_interface_ip)
        self.vsphere_adapter.add(prefix_test)
        clustergroup_test.add_child(cluster_test)
        cluster_test.add_child(vm_test)
        vm_test.add_child(vm_interface_test)
        vm_interface_test.add_child(vm_interface_ip)

        nb_adapter = Adapter(config=self.config)
        nb_adapter.job = MagicMock()
        nb_adapter.load()
        self.vsphere_adapter.sync_to(nb_adapter)

        nb_adapter.sync_complete(source=None, diff=None)
        nb_vm = VirtualMachine.objects.get(name="TestVM")
        self.assertEqual(nb_vm.name, "TestVM")
        self.assertEqual(nb_vm.status.name, "Active")
        self.assertEqual(nb_vm.vcpus, 3)
        self.assertEqual(nb_vm.memory, 4096)
        self.assertEqual(nb_vm.disk, 50)
        self.assertEqual(nb_vm.cluster.name, "TestCluster")
        self.assertEqual(nb_vm.primary_ip.host, "192.168.1.1")
