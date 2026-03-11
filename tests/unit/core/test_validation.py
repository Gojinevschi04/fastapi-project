import pytest
from pydantic import ValidationError

from app.modules.auth.schema import LoginRequest, RegisterRequest
from app.modules.tasks.schema import TaskBase
from app.modules.templates.schema import TemplateCreate, TemplateUpdate
from app.modules.users.schema import ChangePassword, ProfileUpdate, UserCreate


# --- Auth validation ---


class TestRegisterValidation:
    def test_valid_register(self) -> None:
        data = RegisterRequest(email="test@example.com", password="securepass")
        assert data.email == "test@example.com"

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError, match="email"):
            RegisterRequest(email="not-an-email", password="securepass")

    def test_empty_email(self) -> None:
        with pytest.raises(ValidationError):
            RegisterRequest(email="", password="securepass")

    def test_password_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 8"):
            RegisterRequest(email="test@example.com", password="short")

    def test_password_too_long(self) -> None:
        with pytest.raises(ValidationError, match="at most 128"):
            RegisterRequest(email="test@example.com", password="x" * 129)

    def test_invalid_phone_format(self) -> None:
        with pytest.raises(ValidationError, match="phone"):
            RegisterRequest(email="test@example.com", password="securepass", phone_number="123")

    def test_valid_phone(self) -> None:
        data = RegisterRequest(email="test@example.com", password="securepass", phone_number="+37312345678")
        assert data.phone_number == "+37312345678"


class TestLoginValidation:
    def test_valid_login(self) -> None:
        data = LoginRequest(email="test@example.com", password="pass")
        assert data.email == "test@example.com"

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            LoginRequest(email="bad", password="pass")

    def test_password_too_long(self) -> None:
        with pytest.raises(ValidationError, match="at most 128"):
            LoginRequest(email="test@example.com", password="x" * 129)


# --- Template validation ---


class TestTemplateCreateValidation:
    def test_valid_template(self) -> None:
        data = TemplateCreate(name="My Template", base_script="This is a valid script for the AI to follow.")
        assert data.name == "My Template"

    def test_name_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 2"):
            TemplateCreate(name="X", base_script="This is a valid script for the AI.")

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError, match="at most 100"):
            TemplateCreate(name="X" * 101, base_script="This is a valid script for the AI.")

    def test_empty_name(self) -> None:
        with pytest.raises(ValidationError, match="at least 2"):
            TemplateCreate(name="", base_script="This is a valid script for the AI.")

    def test_base_script_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 10"):
            TemplateCreate(name="Template", base_script="Short")

    def test_base_script_too_long(self) -> None:
        with pytest.raises(ValidationError, match="at most 5000"):
            TemplateCreate(name="Template", base_script="X" * 5001)

    def test_too_many_slots(self) -> None:
        with pytest.raises(ValidationError, match="Maximum 20"):
            TemplateCreate(name="Template", base_script="Valid script content here.", required_slots=[f"slot_{i}" for i in range(21)])

    def test_empty_slot_name(self) -> None:
        with pytest.raises(ValidationError, match="cannot be empty"):
            TemplateCreate(name="Template", base_script="Valid script content here.", required_slots=["valid", ""])

    def test_slot_name_too_long(self) -> None:
        with pytest.raises(ValidationError, match="at most 50"):
            TemplateCreate(name="Template", base_script="Valid script content here.", required_slots=["x" * 51])

    def test_name_strips_whitespace(self) -> None:
        data = TemplateCreate(name="  My Template  ", base_script="Valid script content here.")
        assert data.name == "My Template"


class TestTemplateUpdateValidation:
    def test_valid_partial_update(self) -> None:
        data = TemplateUpdate(name="Updated Name")
        assert data.name == "Updated Name"

    def test_name_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 2"):
            TemplateUpdate(name="X")

    def test_base_script_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 10"):
            TemplateUpdate(base_script="Short")

    def test_null_fields_ok(self) -> None:
        data = TemplateUpdate()
        assert data.name is None
        assert data.base_script is None


# --- Task validation ---


class TestTaskValidation:
    def test_valid_task(self) -> None:
        data = TaskBase(target_phone="+37312345678", template_id=1)
        assert data.target_phone == "+37312345678"

    def test_invalid_phone(self) -> None:
        with pytest.raises(ValidationError, match="phone"):
            TaskBase(target_phone="12345", template_id=1)

    def test_too_many_slots(self) -> None:
        with pytest.raises(ValidationError, match="Maximum 20"):
            TaskBase(target_phone="+37312345678", template_id=1, slot_data={f"k{i}": "v" for i in range(21)})

    def test_slot_key_too_long(self) -> None:
        with pytest.raises(ValidationError, match="exceeds 50"):
            TaskBase(target_phone="+37312345678", template_id=1, slot_data={"x" * 51: "value"})

    def test_slot_value_too_long(self) -> None:
        with pytest.raises(ValidationError, match="exceeds 500"):
            TaskBase(target_phone="+37312345678", template_id=1, slot_data={"key": "x" * 501})


# --- User validation ---


class TestUserCreateValidation:
    def test_valid_user(self) -> None:
        data = UserCreate(email="test@example.com", password="securepass")
        assert data.email == "test@example.com"

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="bad", password="securepass")

    def test_password_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 8"):
            UserCreate(email="test@example.com", password="short")

    def test_invalid_phone(self) -> None:
        with pytest.raises(ValidationError, match="phone"):
            UserCreate(email="test@example.com", password="securepass", phone_number="bad")


class TestProfileUpdateValidation:
    def test_valid_update(self) -> None:
        data = ProfileUpdate(email="new@example.com", phone_number="+37312345678")
        assert data.email == "new@example.com"

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            ProfileUpdate(email="not-email")

    def test_empty_is_ok(self) -> None:
        data = ProfileUpdate()
        assert data.email is None
        assert data.phone_number is None


class TestChangePasswordValidation:
    def test_valid(self) -> None:
        data = ChangePassword(current_password="oldpass", new_password="newpassword")
        assert data.new_password == "newpassword"

    def test_new_password_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 8"):
            ChangePassword(current_password="old", new_password="short")

    def test_new_password_too_long(self) -> None:
        with pytest.raises(ValidationError, match="at most 128"):
            ChangePassword(current_password="old", new_password="x" * 129)
