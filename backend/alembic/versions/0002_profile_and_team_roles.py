
from alembic import op

revision = "0002_profile_and_team_roles"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

TEAM_ROLE_VALUES = (
    "team_lead",
    "application_owner",
    "developer",
    "qa",
    "devops",
    "business_analyst",
    "support",
)


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
            ADD COLUMN phone_number VARCHAR(50) NULL,
            ADD COLUMN office_location VARCHAR(255) NULL,
            ADD COLUMN avatar_url TEXT NULL;
        """
    )
    op.execute("ALTER TABLE application_roles DROP CONSTRAINT application_roles_role_name_check;")
    op.execute(f"ALTER TABLE application_roles ADD CONSTRAINT ck_application_roles_role_name CHECK (role_name IN {TEAM_ROLE_VALUES});")


def downgrade() -> None:
    op.execute("ALTER TABLE application_roles DROP CONSTRAINT ck_application_roles_role_name;")
    op.execute("ALTER TABLE application_roles ADD CONSTRAINT application_roles_role_name_check CHECK (role_name IN ('team_lead', 'application_owner'));")
    op.execute(
        """
        ALTER TABLE users
            DROP COLUMN phone_number,
            DROP COLUMN office_location,
            DROP COLUMN avatar_url;
        """
    )
