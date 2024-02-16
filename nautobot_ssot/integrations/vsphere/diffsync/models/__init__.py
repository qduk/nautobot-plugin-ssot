"""Collection of adapters."""

from .vsphere import IPAddressModel, VMInterfaceModel, VirtualMachineModel, ClusterModel, ClusterGroupModel, PrefixModel

__all__ = (
    "IPAddressModel",
    "VMInterfaceModel",
    "VirtualMachineModel",
    "ClusterModel",
    "ClusterGroupModel",
    "PrefixModel",
)
