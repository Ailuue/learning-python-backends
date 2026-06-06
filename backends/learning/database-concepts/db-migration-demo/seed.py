from database import engine, get_session
from models import Base, Author, Book

# Create all tables in SQLite
Base.metadata.create_all(engine)

session = get_session()

authors = [
    Author(name="Ursula K. Le Guin", birth_year=1929),
    Author(name="Frank Herbert", birth_year=1920),
    Author(name="Octavia Butler", birth_year=1947),
]
session.add_all(authors)
session.flush()  # assigns IDs before we reference them in books

books = [
    Book(
        title="The Left Hand of Darkness",
        author_id=authors[0].id,
        published_year=1969,
        genre="Science Fiction",
        summary="An envoy from an interstellar collective visits a planet where inhabitants have no fixed gender.",
    ),
    Book(
        title="The Dispossessed",
        author_id=authors[0].id,
        published_year=1974,
        genre="Science Fiction",
        summary="A physicist travels between an anarchist moon and the capitalist planet it orbits.",
    ),
    Book(
        title="Dune",
        author_id=authors[1].id,
        published_year=1965,
        genre="Science Fiction",
        summary="A noble family is entrusted with control of the most important planet in the galaxy.",
    ),
    Book(
        title="Kindred",
        author_id=authors[2].id,
        published_year=1979,
        genre="Science Fiction",
        summary="A Black woman is repeatedly transported back in time to the antebellum South.",
    ),
    Book(
        title="Parable of the Sower",
        author_id=authors[2].id,
        published_year=1993,
        genre="Science Fiction",
        summary="A young woman survives a collapsing America and builds a new community around her philosophy.",
    ),
]
session.add_all(books)
session.commit()
session.close()

print("Seeded 3 authors and 5 books into SQLite.")
