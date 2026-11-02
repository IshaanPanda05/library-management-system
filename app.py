import os
from datetime import date

import mysql.connector
from flask import Flask, redirect, render_template, request, url_for
from mysql.connector import Error

app = Flask(__name__)

STATUS_MESSAGES = {
    "book_added": ("success", "Book added to the library."),
    "member_added": ("success", "Member registered."),
    "borrowed": ("success", "Book borrowed successfully."),
    "returned": ("success", "Book returned successfully."),
    "duplicate": ("error", "That ISBN or email is already in use."),
    "invalid": ("error", "Please check the form and enter valid information."),
    "unavailable": ("error", "That book has no available copies."),
    "database_error": ("error", "The database could not complete the request. Check the MySQL setup and try again."),
    "not_found": ("error", "That loan was not found or has already been returned."),
}


def get_database_config():
    return {
        "host": os.getenv("LIBRARY_DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("LIBRARY_DB_PORT", "3306")),
        "user": os.getenv("LIBRARY_DB_USER", "root"),
        "password": os.getenv("LIBRARY_DB_PASSWORD", ""),
        "database": os.getenv("LIBRARY_DB_NAME", "alone"),
    }


def status_message():
    return STATUS_MESSAGES.get(request.args.get("status"))


@app.route("/")
def books():
    search = request.args.get("search", "").strip()
    connection = None
    book_rows = []
    database_error = False

    try:
        connection = mysql.connector.connect(**get_database_config())
        cursor = connection.cursor(dictionary=True)
        if search:
            search_pattern = f"%{search}%"
            cursor.execute(
                """
                SELECT book_id, title, author, isbn, total_copies, available_copies
                FROM books
                WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s
                ORDER BY title
                """,
                (search_pattern, search_pattern, search_pattern),
            )
        else:
            cursor.execute(
                """
                SELECT book_id, title, author, isbn, total_copies, available_copies
                FROM books
                ORDER BY title
                """
            )
        book_rows = cursor.fetchall()
        cursor.close()
    except Error:
        app.logger.exception("Unable to load books from MySQL")
        database_error = True
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return render_template(
        "books.html",
        books=book_rows,
        search=search,
        database_error=database_error,
        status=status_message(),
    )


@app.post("/books/add")
def add_book():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    isbn = request.form.get("isbn", "").strip() or None
    try:
        total_copies = int(request.form.get("total_copies", ""))
    except ValueError:
        return redirect(url_for("books", status="invalid"))

    if not title or not author or total_copies < 1:
        return redirect(url_for("books", status="invalid"))

    connection = None
    try:
        connection = mysql.connector.connect(**get_database_config())
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO books (title, author, isbn, total_copies, available_copies)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (title, author, isbn, total_copies, total_copies),
        )
        connection.commit()
        cursor.close()
    except Error as error:
        if connection is not None:
            connection.rollback()
        if getattr(error, "errno", None) == 1062:
            return redirect(url_for("books", status="duplicate"))
        app.logger.exception("Unable to add book to MySQL")
        return redirect(url_for("books", status="database_error"))
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("books", status="book_added"))


@app.route("/members")
def members():
    connection = None
    member_rows = []
    database_error = False

    try:
        connection = mysql.connector.connect(**get_database_config())
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT member_id, full_name, email, phone FROM members ORDER BY full_name"
        )
        member_rows = cursor.fetchall()
        cursor.close()
    except Error:
        app.logger.exception("Unable to load members from MySQL")
        database_error = True
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return render_template(
        "members.html",
        members=member_rows,
        database_error=database_error,
        status=status_message(),
    )


@app.post("/members/add")
def add_member():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip() or None
    if not full_name or not email or "@" not in email:
        return redirect(url_for("members", status="invalid"))

    connection = None
    try:
        connection = mysql.connector.connect(**get_database_config())
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO members (full_name, email, phone) VALUES (%s, %s, %s)",
            (full_name, email, phone),
        )
        connection.commit()
        cursor.close()
    except Error as error:
        if connection is not None:
            connection.rollback()
        if getattr(error, "errno", None) == 1062:
            return redirect(url_for("members", status="duplicate"))
        app.logger.exception("Unable to register member in MySQL")
        return redirect(url_for("members", status="database_error"))
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("members", status="member_added"))


@app.route("/loans")
def loans():
    connection = None
    available_books = []
    member_rows = []
    active_loans = []
    database_error = False

    try:
        connection = mysql.connector.connect(**get_database_config())
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT book_id, title, author, available_copies
            FROM books
            WHERE available_copies > 0
            ORDER BY title
            """
        )
        available_books = cursor.fetchall()
        cursor.execute(
            "SELECT member_id, full_name, email FROM members ORDER BY full_name"
        )
        member_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT loans.loan_id, books.title, members.full_name,
                   loans.borrowed_at, loans.due_date
            FROM loans
            JOIN books ON books.book_id = loans.book_id
            JOIN members ON members.member_id = loans.member_id
            WHERE loans.returned_at IS NULL
            ORDER BY loans.due_date, books.title
            """
        )
        active_loans = cursor.fetchall()
        cursor.close()
    except Error:
        app.logger.exception("Unable to load loans from MySQL")
        database_error = True
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return render_template(
        "loans.html",
        books=available_books,
        members=member_rows,
        loans=active_loans,
        database_error=database_error,
        status=status_message(),
        today=date.today(),
    )


@app.post("/loans/borrow")
def borrow_book():
    try:
        book_id = int(request.form.get("book_id", ""))
        member_id = int(request.form.get("member_id", ""))
        due_date = date.fromisoformat(request.form.get("due_date", ""))
    except (TypeError, ValueError):
        return redirect(url_for("loans", status="invalid"))

    if due_date < date.today():
        return redirect(url_for("loans", status="invalid"))

    connection = None
    try:
        connection = mysql.connector.connect(**get_database_config())
        cursor = connection.cursor()
        cursor.execute(
            "SELECT available_copies FROM books WHERE book_id = %s FOR UPDATE",
            (book_id,),
        )
        book = cursor.fetchone()
        if book is None:
            connection.rollback()
            return redirect(url_for("loans", status="invalid"))
        if book[0] < 1:
            connection.rollback()
            return redirect(url_for("loans", status="unavailable"))

        cursor.execute(
            """
            INSERT INTO loans (book_id, member_id, borrowed_at, due_date)
            VALUES (%s, %s, CURDATE(), %s)
            """,
            (book_id, member_id, due_date),
        )
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s",
            (book_id,),
        )
        connection.commit()
        cursor.close()
    except Error:
        if connection is not None:
            connection.rollback()
        app.logger.exception("Unable to create book loan in MySQL")
        return redirect(url_for("loans", status="database_error"))
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("loans", status="borrowed"))


@app.post("/loans/<int:loan_id>/return")
def return_book(loan_id):
    connection = None
    try:
        connection = mysql.connector.connect(**get_database_config())
        cursor = connection.cursor()
        cursor.execute(
            "SELECT book_id FROM loans WHERE loan_id = %s AND returned_at IS NULL FOR UPDATE",
            (loan_id,),
        )
        loan = cursor.fetchone()
        if loan is None:
            connection.rollback()
            return redirect(url_for("loans", status="not_found"))

        cursor.execute(
            "UPDATE loans SET returned_at = CURDATE() WHERE loan_id = %s",
            (loan_id,),
        )
        cursor.execute(
            """
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE book_id = %s
            """,
            (loan[0],),
        )
        connection.commit()
        cursor.close()
    except Error:
        if connection is not None:
            connection.rollback()
        app.logger.exception("Unable to return book to MySQL")
        return redirect(url_for("loans", status="database_error"))
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("loans", status="returned"))


if __name__ == "__main__":
    app.run()
