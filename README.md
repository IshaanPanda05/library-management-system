# Library Management System

This Flask website uses the existing MySQL database named `alone`. It uses Flask and `mysql-connector-python`; it does not use an ORM or any additional Python packages. SQL statements are executed with the MySQL connector cursor.

## Start the website

In Command Prompt, go to the project folder and activate the virtual environment:

```cmd
cd /d "path\to\library-management-system"
call .venv\Scripts\activate.bat
```

If your MySQL `root` user has a password, set it in this same window:

```cmd
set "LIBRARY_DB_PASSWORD=your_mysql_password"
```

Then run:

```cmd
py app.py
```

Open <http://127.0.0.1:5000> in Chrome. Keep the Command Prompt window open while using the site. If the app was already running when files changed, stop it with Ctrl+C and run `py app.py` again.

## Use the website

- **Books:** search the collection and add books with their total copy count.
- **Members:** register members with a unique email address.
- **Borrow / Return:** select a member, an available book, and a due date to record a loan. Use **Mark returned** when the book comes back.

Borrowing and returning update the loan record and the book's available-copy count together. The database tables must already exist in `alone`; if needed, run `schema.sql` from the MySQL command-line client.
