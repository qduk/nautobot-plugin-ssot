"""Forms implementation for SSOT vSphere."""

from django import forms

from nautobot.extras.forms import NautobotModelForm, NautobotFilterForm
from nautobot.apps.forms import add_blank_choice, JSONField, StaticSelect2, StaticSelect2Multiple

from .models import SSOTvSphereConfig
from .choices import PrimaryIpSortByChoices


class SSOTvSphereConfigForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """SSOTvSphereConfig creation/edit form."""

    default_vm_status_map = JSONField(
        required=True,
        label="Virtual Machine Status Map",
        help_text="Maps vSphere Virtual Machine statuses to Nautobot statuses.",
    )
    default_ip_status_map = JSONField(
        required=True,
        label="Virtual Machine IP Status Map",
        help_text="Maps Virtual Machine IP statuses to Nautobot statuses.",
    )
    default_vm_interface_map = JSONField(
        required=True,
        label="Virtual Machine Interface Status Map",
        help_text="Maps Virtual Machine Interface statuses to Nautobot statuses.",
    )
    primary_ip_sort_by = forms.ChoiceField(
        choices=PrimaryIpSortByChoices,
        required=True,
        label="Primary IP Sort Logic",
        widget=StaticSelect2(),
    )

    class Meta:
        """Meta attributes for the SSOTvSpereConfigForm class."""

        model = SSOTvSphereConfig
        fields = "__all__"


class SSOTvSphereConfigFilterForm(NautobotFilterForm):
    """Filter form for SSOTInfobloxConfig filter searches."""

    model = SSOTvSphereConfig

    class Meta:
        """Meta attributes for the SSOTvSphereConfigFilterForm class."""

        model = SSOTvSphereConfig
        fields = "__all__"
