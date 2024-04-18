"""Itential SSoT models."""


from nautobot_ssot.integrations.itential.diffsync.models import SharedAnsibleDeviceDiffsyncModel


class ItentialAnsibleDeviceModel(SharedAnsibleDeviceDiffsyncModel):
    """Itential Ansible Device DiffSyncModel."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create device in Automation Gateway."""
        diffsync.api_client.create_device(device_name=ids.get("name"), variables=attrs.get("variables"))
        diffsync.api_client.add_device_to_group(group_name="all", device_name=ids.get("name"))
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self):
        """Delete device in Automation Gateway."""
        self.diffsync.api_client.delete_device_from_group(group_name="all", device_name=self.name)
        self.diffsync.api_client.delete_device(device_name=self.name)
        return super().delete()

    def update(self, attrs):
        """Update device in Automation Gateway."""
        self.diffsync.api_client.update_device(device_name=self.name, variables=attrs.get("variables"))
        return super().update(attrs)
