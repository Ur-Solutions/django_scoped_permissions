from types import SimpleNamespace
from unittest.mock import patch

import pytest
from graphql import GraphQLError

from django_scoped_permissions.graphql import ScopedDjangoFilterUpdateMutation


@pytest.mark.parametrize("granted_company", ["17", "18", None])
def test_filter_update_permission_callback_receives_filter_and_data(granted_company):
    grants = [] if granted_company is None else [f"company:{granted_company}:name:Alice"]
    user = SimpleNamespace(get_granting_scopes=lambda: grants)
    info = SimpleNamespace(context=SimpleNamespace(user=user))
    filters = {"company_id": "17"}
    data = {"name": "Alice"}

    with patch.object(
        ScopedDjangoFilterUpdateMutation,
        "get_permissions",
        side_effect=lambda root, info, filters, data: [
            f"company:{filters['company_id']}:name:{data['name']}"
        ],
    ) as get_permissions:
        if granted_company == "17":
            ScopedDjangoFilterUpdateMutation.check_permissions(None, info, filters, data)
        else:
            with pytest.raises(GraphQLError, match="not permitted"):
                ScopedDjangoFilterUpdateMutation.check_permissions(None, info, filters, data)

    get_permissions.assert_called_once_with(None, info, filters, data)
