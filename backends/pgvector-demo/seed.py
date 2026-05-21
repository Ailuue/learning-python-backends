from database import engine, get_session
from models import Base, Comment, User

Base.metadata.create_all(engine)

session = get_session()

users = [
    User(username="alice", email="alice@example.com"),
    User(username="bob", email="bob@example.com"),
    User(username="carol", email="carol@example.com"),
]
session.add_all(users)
session.flush()

comments = [
    Comment(user_id=users[0].id, body="I love hiking in the mountains. The fresh air and views are incredible."),
    Comment(user_id=users[0].id, body="Just finished reading a great sci-fi novel. Highly recommend it to everyone."),
    Comment(user_id=users[1].id, body="The new coffee shop downtown has amazing espresso. Worth the visit."),
    Comment(user_id=users[1].id, body="Python's type hints have made my code so much easier to maintain."),
    Comment(user_id=users[1].id, body="Tried a new pasta recipe last night. Turned out better than expected."),
    Comment(user_id=users[2].id, body="Machine learning is transforming how we approach data analysis."),
    Comment(user_id=users[2].id, body="The weather this weekend was perfect for outdoor activities."),
    Comment(user_id=users[2].id, body="Vector databases are a fascinating tool for semantic search applications."),
    Comment(user_id=users[0].id, body="I spent the afternoon gardening. Planted tomatoes and basil."),
    Comment(user_id=users[2].id, body="Neural networks can find patterns in data that humans would never notice."),
]
session.add_all(comments)
session.commit()
session.close()

print(f"Seeded {len(users)} users and {len(comments)} comments (no embeddings yet).")
