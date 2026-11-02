USE alone;

CREATE TABLE IF NOT EXISTS books (
    book_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    total_copies INT UNSIGNED NOT NULL DEFAULT 1,
    available_copies INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (book_id)
);

CREATE TABLE IF NOT EXISTS members (
    member_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    phone VARCHAR(30),
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (member_id)
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    book_id INT UNSIGNED NOT NULL,
    member_id INT UNSIGNED NOT NULL,
    borrowed_at DATE NOT NULL,
    due_date DATE NOT NULL,
    returned_at DATE,
    PRIMARY KEY (loan_id),
    INDEX idx_loans_book_id (book_id),
    INDEX idx_loans_member_id (member_id),
    CONSTRAINT fk_loans_book
        FOREIGN KEY (book_id) REFERENCES books (book_id),
    CONSTRAINT fk_loans_member
        FOREIGN KEY (member_id) REFERENCES members (member_id)
);

INSERT IGNORE INTO books (title, author, isbn, total_copies, available_copies)
VALUES
    ('The Hobbit', 'J. R. R. Tolkien', '9780547928227', 3, 3),
    ('Pride and Prejudice', 'Jane Austen', '9780141439518', 2, 2),
    ('The Little Prince', 'Antoine de Saint-Exupery', '9780156012195', 2, 2);
