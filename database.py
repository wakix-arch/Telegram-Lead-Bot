import sqlite3

DB_NAME = "leads.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            date TEXT NOT NULL,

            name TEXT NOT NULL,

            phone TEXT NOT NULL,

            service TEXT NOT NULL,

            description TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'Новая'

        )
    """)

    conn.commit()
    conn.close()


def save_application(
    date,
    name,
    phone,
    service,
    description
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications
        (
            date,
            name,
            phone,
            service,
            description,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        date,
        name,
        phone,
        service,
        description,
        "Новая"
    ))

    conn.commit()
    conn.close()


def get_applications():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            date,
            name,
            phone,
            service,
            description,
            status

        FROM applications

        ORDER BY id DESC
    """)

    applications = cursor.fetchall()

    conn.close()

    return applications


def update_status(
    application_id,
    new_status
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications

        SET status = ?

        WHERE id = ?
    """, (
        new_status,
        application_id
    ))

    conn.commit()
    conn.close()