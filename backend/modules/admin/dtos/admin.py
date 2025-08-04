from backend.modules.base.dto import BaseDTO


class UpdateRoleDTO(BaseDTO):
    target_account: str
    new_role: str
