"""Seed script for the Demo bookstore application."""
import os
import random
import string
import sys

from datetime import date

from app import create_app, db
from app.models import User, Book, Category


def generate_unique_isbn(session):
    """
    Generate a random 13-digit ISBN (numeric), and make sure
    it doesn’t already exist in the books table. Retry until unique.
    """
    while True:
        # Generate a 13-digit random numeric string
        isbn_candidate = "".join(random.choices(string.digits, k=13))
        exists = session.query(Book).filter_by(isbn=isbn_candidate).first()
        if not exists:
            return isbn_candidate


def seed_admin():
    """Create a default admin user if none exists."""

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")

    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        print(
            f"[seed_all] Admin user {admin_email} already exists → skipping."
        )
        return

    admin = User(email=admin_email, is_admin=True)
    admin.set_password(admin_password)
    db.session.add(admin)
    print(f"[seed_all] Created admin user: {admin_email}")


def seed_categories_and_books():
    """Create default categories and books if they don’t exist."""

    default_data = {
        "Fiction": [
            {
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "description": "A novel set in the Roaring Twenties...",
                "price": 10.99,
                "stock": 5,
            },
            {
                "title": "1984",
                "author": "George Orwell",
                "description": "Dystopian novel about totalitarianism...",
                "price": 8.99,
                "stock": 10,
            },
            {
                "title": "Things Fall Apart",
                "author": "Chinua Achebe",
                "isbn": "9780385474542",
                "description": "A powerful tale of colonialism and culture clash in pre-colonial Igbo society.",
                "price": 18.50,
                "stock": 20,
                "publication_date": date(1958, 6, 17),
            },
            {
                "title": "The Secret Lives of Baba Segi’s Wives",
                "author": "Lola Shoneyin",
                "isbn": "9781845235677",
                "description": "A humorous and tragic tale of polygamy, family secrets, and personal discovery.",
                "price": 17.00,
                "stock": 12,
                "publication_date": date(2010, 5, 1),
            },
            {
                "title": "Americanah",
                "author": "Chimamanda Ngozi Adichie",
                "isbn": "9780307455927",
                "description": "A witty love story that also explores race, identity, and immigration.",
                "price": 19.50,
                "stock": 18,
                "publication_date": date(2013, 5, 14),
            },
            {
                "title": "Born on a Tuesday",
                "author": "Elnathan John",
                "isbn": "9780802124821",
                "description": "A coming-of-age novel set amidst political and religious upheaval in northern Nigeria.",
                "price": 15.00,
                "stock": 8,
                "publication_date": date(2015, 11, 10),
            },
        ],
        "Non-Fiction": [
            {
                "title": "Sapiens",
                "author": "Yuval Noah Harari",
                "description": "A brief history of humankind...",
                "price": 12.99,
                "stock": 7,
            }
        ],
        "Business": [
            {
                "title": "Rich Dad Poor Dad",
                "author": "Robert T. Kiyosaki",
                "isbn": "9780446677455",
                "description": "What the Rich Teach Their Kids About Money That the Poor and Middle Class Do Not!",
                "price": 15.00,
                "stock": 19,
                "publication_date": date(2000, 1, 1),
            },
            {
                "title": "The Lean Startup",
                "author": "Eric Ries",
                "description": "A guide to building successful startups...",
                "price": 15.99,
                "stock": 3,
            },
            {
                "title": "Good to Great",
                "author": "Jim Collins",
                "description": "Why some companies make the leap and others don’t...",
                "price": 14.99,
                "stock": 4,
            },
            {
                "title": "Principles: Life and Work",
                "author": "Ray Dalio",
                "isbn": "9781501124020",
                "description": "Practical lessons for achieving success from a legendary investor.",
                "price": 27.50,
                "stock": 15,
                "publication_date": date(2017, 9, 19),
            },
        ],
        "Satire": [
            {
                "title": "I Do Not Come to You by Chance",
                "author": "Adaobi Tricia Nwaubani",
                "isbn": "9780316072391",
                "description": "A satirical take on email scams, survival, and corruption in Nigeria.",
                "price": 14.99,
                "stock": 11,
                "publication_date": date(2009, 5, 18),
            },
        ],
        "Fantasy": [
            {
                "title": "Freshwater",
                "author": "Akwaeke Emezi",
                "isbn": "9780802127358",
                "description": "A bold, genre-defying exploration of identity, spirituality, and trauma.",
                "price": 22.00,
                "stock": 7,
                "publication_date": date(2018, 2, 13),
            },
            {
                "title": "The Lord of the Rings",
                "author": "J.R.R. Tolkien",
                "isbn": "9780618053267",
                "description": "A high-fantasy epic journey to destroy the One Ring.",
                "price": 25.50,
                "stock": 20,
                "publication_date": date(1954, 7, 29),
            },
            {
                "title": "The Hobbit",
                "author": "J.R.R. Tolkien",
                "isbn": "9780345339683",
                "description": "Bilbo Baggins' unexpected journey and adventure.",
                "price": 10.99,
                "stock": 30,
                "publication_date": date(1937, 9, 21),
            },
            {
                "title": "Mistborn: The Final Empire",
                "author": "Brandon Sanderson",
                "isbn": "9780765350382",
                "description": "In a world of ash and mist, a young thief discovers her power.",
                "price": 15.00,
                "stock": 14,
                "publication_date": date(2006, 7, 25),
            },
        ],
        "History": [
            {
                "title": "Sapiens: A Brief History of Humankind",
                "author": "Yuval Noah Harari",
                "isbn": "9780062316097",
                "description": "Explores the history of Homo sapiens from the Stone Age to the 21st century.",
                "price": 18.75,
                "stock": 18,
                "publication_date": date(2014, 2, 10),
            },
            {
                "title": "The Gulag Archipelago",
                "author": "Aleksandr Solzhenitsyn",
                "isbn": "9780813332890",
                "description": "A non-fiction text on the Soviet forced labor camp system.",
                "price": 24.00,
                "stock": 7,
                "publication_date": date(1973, 1, 1),
            },
        ],
        "Thriller": [
            {
                "title": "My Sister, the Serial Killer",
                "author": "Oyinkan Braithwaite",
                "isbn": "9780385544238",
                "description": "A darkly funny thriller about family loyalty and murder in Lagos.",
                "price": 20.00,
                "stock": 14,
                "publication_date": date(2018, 11, 20),
            },
            {
                "title": "The Silent Patient",
                "author": "Alex Michaelides",
                "isbn": "9781250301697",
                "description": "A shocking psychological thriller about a woman's act of violence.",
                "price": 14.50,
                "stock": 22,
                "publication_date": date(2019, 2, 5),
            },
            {
                "title": "Gone Girl",
                "author": "Gillian Flynn",
                "isbn": "9780307588373",
                "description": "A psychological thriller about a woman's disappearance.",
                "price": 13.00,
                "stock": 16,
                "publication_date": date(2012, 5, 24),
            },
            {
                "title": "The Girl with the Dragon Tattoo",
                "author": "Stieg Larsson",
                "isbn": "9780307474270",
                "description": "A journalist and hacker investigate a disappearance.",
                "price": 13.50,
                "stock": 19,
                "publication_date": date(2005, 8, 1),
            },
        ],
        "Science Fiction": [
            {
                "title": "Dune",
                "author": "Frank Herbert",
                "isbn": "9780441013593",
                "description": "A science fiction epic set on the desert planet Arrakis.",
                "price": 19.99,
                "stock": 10,
                "publication_date": date(1965, 8, 1),
            },
            {
                "title": "Neuromancer",
                "author": "William Gibson",
                "isbn": "9780441569595",
                "description": "A cyberpunk novel that defined a genre.",
                "price": 15.00,
                "stock": 12,
                "publication_date": date(1984, 7, 1),
            },
            {
                "title": "A Brief History of Time",
                "author": "Stephen Hawking",
                "isbn": "9780553380163",
                "description": "From the Big Bang to Black Holes.",
                "price": 17.50,
                "stock": 13,
                "publication_date": date(1988, 4, 1),
            },
            {
                "title": "The Martian",
                "author": "Andy Weir",
                "isbn": "9780804139021",
                "description": "An astronaut is stranded on Mars and must find a way to survive.",
                "price": 14.00,
                "stock": 18,
                "publication_date": date(2014, 2, 11),
            },
        ],
        "Romance": [
            {
                "title": "Pride and Prejudice",
                "author": "Jane Austen",
                "description": "A classic romance novel...",
                "price": 9.99,
                "stock": 6,
            },
            {
                "title": "The Fault in Our Stars",
                "author": "John Green",
                "description": "A poignant love story between two teens with cancer...",
                "price": 11.99,
                "stock": 8,
            },
        ],
        "Poetry": [
            {
                "title": "The Sun and Her Flowers",
                "author": "Rupi Kaur",
                "description": "A collection of poetry and prose about growth, healing, and self-love.",
                "price": 12.00,
                "stock": 9,
            },
            {
                "title": "Milk and Honey",
                "author": "Rupi Kaur",
                "description": "A collection of poetry exploring love, loss, trauma, and healing.",
                "price": 10.00,
                "stock": 15,
            },
        ],
        "Self-Help": [
            {
                "title": "Atomic Habits",
                "author": "James Clear",
                "description": "An easy & proven way to build good habits & break bad ones.",
                "price": 16.99,
                "stock": 10,
                "publication_date": date(2018, 10, 16),
            },
            {
                "title": "The Power of Now",
                "author": "Eckhart Tolle",
                "description": "A guide to spiritual enlightenment and living in the present moment.",
                "price": 14.99,
                "stock": 5,
            },
            {
                "title": "The 7 Habits of Highly Effective People",
                "author": "Stephen Covey",
                "isbn": "9780743269512",
                "description": "Powerful Lessons in Personal Change.",
                "price": 19.99,
                "stock": 20,
                "publication_date": date(1989, 8, 15),
            },
            {
                "title": "The Power of Habit",
                "author": "Charles Duhigg",
                "isbn": "9780812981605",
                "description": "Why We Do What We Do in Life and Business.",
                "price": 15.50,
                "stock": 23,
                "publication_date": date(2012, 2, 28),
            },
        ],
        "Biography": [
            {
                "title": "Steve Jobs",
                "author": "Walter Isaacson",
                "isbn": "9781451648539",
                "description": "Biography of Steve Jobs by Walter Isaacson.",
                "price": 34.99,
                "stock": 12,
                "publication_date": date(2011, 10, 24),
            },
            {
                "title": "Becoming",
                "author": "Michelle Obama",
                "isbn": "9781524763138",
                "description": "A memoir by former First Lady of the United States Michelle Obama.",
                "price": 28.00,
                "stock": 14,
                "publication_date": date(2018, 11, 13),
            },
            {
                "title": "Long Walk to Freedom",
                "author": "Nelson Mandela",
                "isbn": "9780316548182",
                "description": "The autobiography of Nelson Mandela, chronicling his early life, education, and 27 years in prison.",
                "price": 25.00,
                "stock": 10,
                "publication_date": date(1994, 1, 1),
            },
            {
                "title": "Educated",
                "author": "Tara Westover",
                "isbn": "9780399590504",
                "description": "A memoir about a young girl's quest for knowledge against all odds.",
                "price": 16.50,
                "stock": 11,
                "publication_date": date(2018, 2, 20),
            },
            {
                "title": "Butterfly Fish",
                "author": "Irenosen Okojie",
                "isbn": "9781909762222",
                "description": "A haunting narrative blending grief, West African history, and magical realism.",
                "price": 18.25,
                "stock": 9,
                "publication_date": date(2015, 6, 1),
            },
        ],
        "Children's": [
            {
                "title": "Where the Wild Things Are",
                "author": "Maurice Sendak",
                "description": "A classic children's book about imagination and adventure.",
                "price": 7.99,
                "stock": 15,
            },
            {
                "title": "Harry Potter and the Sorcerer's Stone",
                "author": "J.K. Rowling",
                "description": "The first book in the Harry Potter series...",
                "price": 9.99,
                "stock": 20,
            },
        ],
        "Literary Fiction": [
            {
                "title": "Stay With Me",
                "author": "Ayọ̀bámi Adébáyọ̀",
                "isbn": "9780451494603",
                "description": "An emotional novel of marriage, motherhood, and societal expectations in Nigeria.",
                "price": 16.75,
                "stock": 10,
                "publication_date": date(2017, 3, 2),
            },
        ],
        "Historical Fiction": [
            {
                "title": "Half of a Yellow Sun",
                "author": "Chimamanda Ngozi Adichie",
                "isbn": "9781400095209",
                "description": "A story of love and war set during the Biafran conflict in 1960s Nigeria.",
                "price": 21.99,
                "stock": 15,
                "publication_date": date(2006, 9, 4),
            },
        ],
        "Programming": [
            {
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "isbn": "9780132350884",
                "description": "A Handbook of Agile Software Craftsmanship.",
                "price": 45.99,
                "stock": 15,
                "publication_date": date(2008, 8, 1),
            },
            {
                "title": "The Pragmatic Programmer",
                "author": "Andrew Hunt and David Thomas",
                "isbn": "9780135957059",
                "description": "Your journey to mastery, 20th Anniversary Edition.",
                "price": 39.99,
                "stock": 10,
                "publication_date": date(2019, 9, 13),
            },
            {
                "title": "Python Crash Course",
                "author": "Eric Matthes",
                "isbn": "9781593279288",
                "description": "A hands-on, project-based introduction to programming.",
                "price": 32.00,
                "stock": 17,
                "publication_date": date(2019, 5, 2),
            },
            {
                "title": "Cracking the Coding Interview",
                "author": "Gayle Laakmann McDowell",
                "isbn": "9780984782857",
                "description": "189 Programming Questions and Solutions.",
                "price": 49.99,
                "stock": 10,
                "publication_date": date(2015, 7, 1),
            },
        ],
    }

    # Ensure the default categories and books are created
    for cat_name, books in default_data.items():
        category = Category.query.filter_by(name=cat_name).first()
        if not category:
            category = Category(name=cat_name)
            db.session.add(category)
            db.session.flush()
            print(f"[seed_all] Created category: {cat_name}")
        else:
            print(f"[seed_all] Category {cat_name} already exists → skipping.")

        for book_info in books:
            title = book_info["title"]
            existing_book = Book.query.filter_by(title=title).first()
            if existing_book:
                print(f"[seed_all] Book '{title}' already exists → skipping.")
                continue

            # Provide default ISBN and publication_date if missing
            if book_info.get("isbn"):
                isbn_val = book_info["isbn"]
                # If someone manually provided an ISBN, we should still check uniqueness
                if Book.query.filter_by(isbn=isbn_val).first():
                    print(
                        f"[seed_all] Provided ISBN {isbn_val} for '{title}' already exists! "
                        "Generating a new random one."
                    )
                    isbn_val = generate_unique_isbn(db.session)
            else:
                isbn_val = generate_unique_isbn(db.session)

            # Determine publication_date: use provided or default to Jan 1, 2000
            pub_date = book_info.get("publication_date")
            if not pub_date:
                pub_date = date(2000, 1, 1)

            # Determine summary: use provided or None
            summary = book_info.get("summary")

            new_book = Book(
                title=title,
                author=book_info["author"],
                description=book_info.get("description", ""),
                isbn=isbn_val,
                price=book_info["price"],
                stock=book_info["stock"],
                publication_date=pub_date,
                category_id=category.id,
                summary=summary,
                is_active=True,
            )
            db.session.add(new_book)
            print(
                f"[seed_all] Created book: '{title}' in category '{cat_name}'"
            )


def main():
    """
    Entrypoint: runs both seed_admin and seed_categories_and_books.
    """
    app = create_app()
    with app.app_context():
        try:
            seed_admin()
            seed_categories_and_books()
            db.session.commit()
            print("[seed_all] Seeding complete.")
        except Exception as e:
            db.session.rollback()
            print(
                f"[seed_all] ERROR during seeding: {str(e)}", file=sys.stderr
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
