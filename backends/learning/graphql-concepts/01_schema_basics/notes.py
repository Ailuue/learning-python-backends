"""
01 · Schema Basics — Concepts & Query Reference
================================================

CONTENTS:
  1. GraphQL vs REST — the key difference
  2. The SDL (Schema Definition Language) — what Strawberry generates
  3. The type system — scalars, objects, lists, null
  4. Queries — selecting fields, aliases, variables
  5. Mutations — changing data
  6. Introspection — asking the schema what it supports
  7. Exercises

--- GRAPHQL vs REST ---

REST: the server decides what's in the response.
  GET /books/1  →  {"id": 1, "title": "...", "author": "...", "year": ..., "description": "..."}

GraphQL: the CLIENT decides what fields it needs.
  query { book(id: "1") { title year } }  →  {"book": {"title": "...", "year": ...}}

The client only gets what it asks for — no over-fetching.
The client can ask for multiple resources in one request — no under-fetching.

--- SDL (Schema Definition Language) ---

Strawberry generates this schema from your Python code.
You can view it with: print(schema.as_str())

    type Book {
      id: ID!
      title: String!
      author: String!
      year: Int!
      description: String    # nullable — no !
    }

    input AddBookInput {
      title: String!
      author: String!
      year: Int!
      description: String
    }

    type Query {
      books: [Book!]!
      book(id: ID!): Book     # returns null if not found
    }

    type Mutation {
      addBook(input: AddBookInput!): Book!
      deleteBook(id: ID!): Boolean!
    }

The ! means non-nullable. Fields without ! can return null.

--- THE TYPE SYSTEM ---

Built-in scalars (leaf types — no sub-fields):
  String    UTF-8 text
  Int       32-bit signed integer
  Float     double-precision float
  Boolean   true / false
  ID        opaque identifier (serialized as String)

Python → GraphQL mapping (Strawberry):
  str            → String!
  int            → Int!
  float          → Float!
  bool           → Boolean!
  strawberry.ID  → ID!
  Optional[T]    → T        (nullable)
  list[T]        → [T!]!

Custom scalars (for types like datetime, UUID, JSON):
  @strawberry.scalar(serialize=..., parse_value=...)

--- QUERIES ---

Basic field selection:
    query {
      books {
        id
        title
        author
      }
    }

With arguments:
    query {
      book(id: "2") {
        title
        description
      }
    }

Aliases — query the same field twice with different args:
    query {
      first:  book(id: "1") { title }
      second: book(id: "2") { title }
    }

Named queries with variables — the right way in real apps:
    query GetBook($id: ID!) {
      book(id: $id) {
        title
        year
      }
    }

    Variables: { "id": "1" }

Fragments — reuse a field selection:
    fragment BookFields on Book {
      id
      title
      author
    }

    query {
      books { ...BookFields }
    }

--- MUTATIONS ---

Basic mutation:
    mutation {
      addBook(input: {
        title: "Designing Data-Intensive Applications"
        author: "Martin Kleppmann"
        year: 2017
      }) {
        id
        title
      }
    }

Mutation with variables:
    mutation AddBook($input: AddBookInput!) {
      addBook(input: $input) {
        id
        title
      }
    }

    Variables: {
      "input": {
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "year": 2017
      }
    }

Delete:
    mutation {
      deleteBook(id: "1")
    }

--- INTROSPECTION ---

Ask the schema what types it supports:
    query {
      __schema {
        types { name kind }
      }
    }

Ask about a specific type:
    query {
      __type(name: "Book") {
        fields { name type { name kind } }
      }
    }

The playground's autocomplete and docs panel use introspection automatically.

--- EXERCISES ---

1. Query all books — request only id and title (exclude author and year).
   Notice the response only contains what you asked for.

2. Query a single book by ID. Then query a non-existent ID ("999").
   The field returns null rather than an error.

3. Add a new book using the addBook mutation.
   Request id, title, and author in the response.

4. Delete the book you just added.
   Try deleting a non-existent ID — it returns false.

5. Print the generated SDL:
   Run: python -c "from schema import schema; print(schema.as_str())"
   Compare with the SDL shown above.

6. Use an alias to fetch two different books in one request.
"""

SCALAR_TYPES = {
    "String":  "UTF-8 text — Python str",
    "Int":     "32-bit integer — Python int",
    "Float":   "64-bit float — Python float",
    "Boolean": "true / false — Python bool",
    "ID":      "Opaque identifier — serialized as String",
}

PYTHON_TO_GRAPHQL = {
    "str":           "String!",
    "int":           "Int!",
    "float":         "Float!",
    "bool":          "Boolean!",
    "strawberry.ID": "ID!",
    "Optional[str]": "String   (nullable)",
    "list[str]":     "[String!]!",
}

KEY_DECORATORS = {
    "@strawberry.type":     "Defines a GraphQL object type",
    "@strawberry.input":    "Defines a GraphQL input type (mutation args only)",
    "@strawberry.field":    "Marks a method as a queryable field",
    "@strawberry.mutation": "Marks a method as a mutation field",
    "strawberry.Schema":    "The entry point — wires query/mutation/subscription",
}
