
from alembic import op

revision = "0003_unique_names"
down_revision = "0002_profile_and_team_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE projects ADD CONSTRAINT uq_projects_name UNIQUE (name);")
    op.execute("ALTER TABLE applications ADD CONSTRAINT uq_applications_name UNIQUE (name);")


def downgrade() -> None:
    op.execute("ALTER TABLE applications DROP CONSTRAINT uq_applications_name;")
    op.execute("ALTER TABLE projects DROP CONSTRAINT uq_projects_name;")
