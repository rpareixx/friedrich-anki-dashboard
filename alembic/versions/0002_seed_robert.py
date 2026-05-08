"""seed Robert as user #1 with englisch brawler in slot 1

Revision ID: 0002_seed_robert
Revises: 0001_init
Create Date: 2026-05-08

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "0002_seed_robert"
down_revision: Union[str, Sequence[str], None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            INSERT INTO users (slug, email, timezone)
            VALUES (:slug, :email, :timezone)
            """
        ),
        {"slug": "robert", "email": "robert.parei@parei.eu", "timezone": "Europe/Berlin"},
    )

    user_id = bind.execute(sa.text("SELECT id FROM users WHERE slug = 'robert'")).scalar_one()

    bind.execute(
        sa.text(
            """
            INSERT INTO brawlers (user_id, slot, subject)
            VALUES (:user_id, :slot, :subject)
            """
        ),
        {"user_id": user_id, "slot": 1, "subject": "englisch"},
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM brawlers WHERE subject = 'englisch'"))
    bind.execute(sa.text("DELETE FROM users WHERE slug = 'robert'"))
