"""Unit tests for vSphere SSoT DiffSync Models."""

import unittest
from unittest.mock import MagicMock

from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Prefix
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
from nautobot_ssot.integrations.vsphere.diffsync.models import (
    ClusterGroupModel,
    ClusterModel,
    IPAddressModel,
    PrefixModel,
    VirtualMachineModel,
    VMInterfaceModel,
)


class TestVSphereDiffSyncModels(unittest.TestCase):
    """Test cases for vSphere DiffSync models."""

    def setUp(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        ClusterType.objects.all().delete()
        ClusterGroup.objects.all().delete()
        IPAddress.objects.all().delete()
        Prefix.objects.all().delete()
        self.active_status, _ = Status.objects.get_or_create(name="Active")

    def test_clustergroup_creation(self):
        ClusterGroupModel.create(
            adapter=Adapter(job=MagicMock()),
            ids={"name": "TestClusterGroup"},
            attrs={},
        )
        nb_clustergroup = ClusterGroup.objects.get(name="TestClusterGroup")
        self.assertEqual(nb_clustergroup.name, "TestClusterGroup")

    def test_cluster_creation(self):
        ClusterGroup.objects.create(name="TestClusterGroup")
        ClusterType.objects.create(name="VMWare vSphere")

        ClusterModel.create(
            adapter=Adapter(job=MagicMock()),
            ids={"name": "TestCluster"},
            attrs={
                "cluster_type__name": "VMWare vSphere",
                "cluster_group__name": "TestClusterGroup",
            },
        )
        nb_cluster = Cluster.objects.get(name="TestCluster")
        self.assertEqual(nb_cluster.name, "TestCluster")
        self.assertEqual(nb_cluster.cluster_group.name, "TestClusterGroup")
        self.assertEqual(nb_cluster.cluster_type.name, "VMWare vSphere")

    def test_vm_creation(self):
        nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
        nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
        Cluster.objects.create(
            name="TestCluster",
            cluster_type=nb_clustertype,
            cluster_group=nb_clustergroup,
        )

        VirtualMachineModel.create(
            adapter=Adapter(job=MagicMock()),
            ids={"name": "TestVM"},
            attrs={
                "status__name": "Active",
                "vcpus": 3,
                "memory": 4096,
                "disk": 50,
                "cluster__name": "TestCluster",
                "primary_ip4__host": None,
                "primary_ip6__host": None,
            },
        )
        nb_vm = VirtualMachine.objects.get(name="TestVM")
        self.assertEqual(nb_vm.name, "TestVM")
        self.assertEqual(nb_vm.status.name, "Active")
        self.assertEqual(nb_vm.vcpus, 3)
        self.assertEqual(nb_vm.memory, 4096)
        self.assertEqual(nb_vm.disk, 50)
        self.assertEqual(nb_vm.cluster.name, "TestCluster")

    def test_vm_creation_primary_ips(self):
        nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
        nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
        Cluster.objects.create(
            name="TestCluster",
            cluster_type=nb_clustertype,
            cluster_group=nb_clustergroup,
        )

        Prefix.objects.create(
            network="192.168.0.0",
            prefix_length="24",
            status=Status.objects.get(name="Active"),
        )

        nb_adapter = Adapter(job=MagicMock())
        VirtualMachineModel.create(
            adapter=nb_adapter,
            ids={"name": "TestVM"},
            attrs={
                "status__name": "Active",
                "vcpus": 3,
                "memory": 4096,
                "disk": 50,
                "cluster__name": "TestCluster",
                "primary_ip4__host": "192.168.0.1",
                "primary_ip6__host": None,
            },
        )

        # The interface must be created for the primary IP to run since it is in the `sync_complete` method.
        VMInterfaceModel.create(
            adapter=Adapter(job=MagicMock()),
            ids={"name": "Network Adapter 1", "virtual_machine__name": "TestVM"},
            attrs={
                "enabled": True,
                "status__name": "Active",
                "mac_address": "AA:BB:CC:DD:EE:FF",
            },
        )

        # The IP Address must be created as well.
        IPAddressModel.create(
            adapter=Adapter(job=MagicMock()),
            ids={
                "host": "192.168.0.1",
                "mask_length": "24",
                "vm_interfaces": [{"name": "Network Adapter 1"}],
            },
            attrs={
                "status__name": "Active",
            },
        )

        nb_adapter.sync_complete(source=None, diff=None)
        nb_vm = VirtualMachine.objects.get(name="TestVM")
        self.assertEqual(nb_vm.name, "TestVM")
        self.assertEqual(nb_vm.status.name, "Active")
        self.assertEqual(nb_vm.vcpus, 3)
        self.assertEqual(nb_vm.memory, 4096)
        self.assertEqual(nb_vm.disk, 50)
        self.assertEqual(nb_vm.cluster.name, "TestCluster")
        self.assertEqual(nb_vm.primary_ip.host, "192.168.0.1")

    def test_vminterface_creation(self):
        nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
        nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
        nb_cluster = Cluster.objects.create(
            name="TestCluster",
            cluster_type=nb_clustertype,
            cluster_group=nb_clustergroup,
        )
        VirtualMachine.objects.create(
            name="TestVM", cluster=nb_cluster, status=self.active_status
        )

        VMInterfaceModel.create(
            adapter=Adapter(job=MagicMock()),
            ids={"name": "Network Adapter 1", "virtual_machine__name": "TestVM"},
            attrs={
                "enabled": True,
                "status__name": "Active",
                "mac_address": "AA:BB:CC:DD:EE:FF",
            },
        )
        nb_vminterface = VMInterface.objects.get(name="Network Adapter 1")
        self.assertEqual(nb_vminterface.name, "Network Adapter 1")
        self.assertEqual(nb_vminterface.enabled, True)
        self.assertEqual(nb_vminterface.virtual_machine.name, "TestVM")

    def test_ipaddress_creation(self):
        nb_clustergroup = ClusterGroup.objects.create(name="TestClusterGroup")
        nb_clustertype = ClusterType.objects.create(name="VMWare vSphere")
        nb_cluster = Cluster.objects.create(
            name="TestCluster",
            cluster_type=nb_clustertype,
            cluster_group=nb_clustergroup,
        )
        nb_vm = VirtualMachine.objects.create(
            name="TestVM", cluster=nb_cluster, status=self.active_status
        )
        VMInterface.objects.create(
            name="Network Adapter 1",
            virtual_machine=nb_vm,
            enabled=True,
            status=self.active_status,
        )
        Prefix.objects.create(
            prefix="192.168.1.0/24", status=Status.objects.get(name="Active")
        )
        IPAddressModel.create(
            adapter=Adapter(job=MagicMock()),
            ids={
                "host": "192.168.1.1",
                "mask_length": "24",
                "vm_interfaces": [{"name": "Network Adapter 1"}],
            },
            attrs={
                "status__name": "Active",
            },
        )
        nb_ip = IPAddress.objects.get(host="192.168.1.1", mask_length=24)
        self.assertEqual(nb_ip.host, "192.168.1.1")
        self.assertEqual(nb_ip.mask_length, 24)
        self.assertIn(
            "Network Adapter 1",
            [interface.name for interface in nb_ip.vm_interfaces.all()],
        )

    def test_prefix_creation(self):
        PrefixModel.create(
            adapter=Adapter(job=MagicMock()),
            ids={
                "network": "10.10.10.0",
                "prefix_length": 24,
                "namespace__name": "Global",
                "status__name": "Active",
            },
            attrs={"type": "network"},
        )

        nb_prefix = Prefix.objects.get(network="10.10.10.0", prefix_length="24")
        self.assertEqual(nb_prefix.network, "10.10.10.0")
        self.assertEqual(nb_prefix.prefix_length, 24)
        self.assertEqual(str(nb_prefix.prefix), "10.10.10.0/24")
        self.assertEqual(nb_prefix.namespace.name, "Global")
