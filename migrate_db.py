from sqlalchemy import text

from app.database.database import engine


columns = {
    "metrics_snapshot": "TEXT",
    "logs_snapshot": "TEXT",
    "events_snapshot": "TEXT",
    "investigation_root_cause": "TEXT",
    "investigation_evidence": "TEXT",
    "investigation_impact": "TEXT",
    "investigation_confidence": "REAL",
    "recommended_action": "TEXT",
    "recommended_action_type": "VARCHAR(50)",
}


with engine.begin() as connection:
    existing_columns = {
        row[1]
        for row in connection.execute(
            text("PRAGMA table_info(incidents)")
        )
    }

    for column_name, column_type in columns.items():

        if column_name not in existing_columns:

            connection.execute(
                text(
                    f"ALTER TABLE incidents "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )

            print(f"Added column: {column_name}")

        else:
            print(f"Already exists: {column_name}")


print("Database migration completed.")