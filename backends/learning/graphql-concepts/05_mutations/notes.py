"""
05 · Mutations — Concepts
==========================

CONTENTS:
  1. Mutation mechanics — how mutations differ from queries
  2. Input types in depth — UNSET vs None, partial updates
  3. Simple return patterns — object or null
  4. Mutation payload pattern — typed success + error responses
  5. Error handling strategies compared
  6. Exercises

--- MUTATION MECHANICS ---

Mutations look like queries but:
  1. They use the `mutation` keyword
  2. They run SEQUENTIALLY (not in parallel like query fields)
  3. They're expected to have side effects

    mutation {
      createTodo(input: { title: "Learn mutations", priority: 2 }) {
        ... on CreateTodoSuccess { todo { id title } }
        ... on ValidationError  { field message }
      }
    }

Variables (the right way in apps):
    mutation CreateTodo($input: CreateTodoInput!) {
      createTodo(input: $input) {
        ... on CreateTodoSuccess { todo { id } }
        ... on ValidationError  { field message }
      }
    }

    Variables: { "input": { "title": "Learn mutations", "priority": 2 } }

--- INPUT TYPES IN DEPTH ---

@strawberry.input creates a plain data container — no resolver methods allowed.

For CREATE mutations: require all fields.
    @strawberry.input
    class CreateTodoInput:
        title: str        # required
        priority: int = 1 # optional with default

For UPDATE (PATCH) mutations: all fields optional.
    @strawberry.input
    class UpdateTodoInput:
        title: Optional[str] = None      # None means "not provided"
        done: Optional[bool] = None
        priority: Optional[int] = None

Partial update in the resolver:
    if input.title is not None:
        row["title"] = input.title

UNSET vs None:
  None means "set this field to null"
  strawberry.UNSET means "don't change this field"

  Use UNSET when null and absent are different:
    updateUser(bio: null)    # clear the bio
    updateUser()             # don't touch the bio

    @strawberry.input
    class UpdateUserInput:
        bio: Optional[str] = strawberry.UNSET

    if input.bio is not strawberry.UNSET:
        user.bio = input.bio   # includes setting to null

--- PATTERN A: SIMPLE RETURNS ---

Pros:
  - Simple to implement and read
  - Fewer types to define

Cons:
  - Null means "not found" OR "an error" — ambiguous
  - No structured error information
  - Client must check for null and handle it generically

    @strawberry.mutation
    def toggle_done(self, id: strawberry.ID) -> Optional[TodoItem]:
        ...
        return None   # is this "not found" or "something went wrong"?

--- PATTERN B: MUTATION PAYLOAD ---

The recommended pattern. Return a union of success + possible error types.

    UpdateTodoResult = strawberry.union(
        "UpdateTodoResult",
        types=(UpdateTodoSuccess, TodoNotFound, ValidationError),
    )

    @strawberry.mutation
    def update_todo(self, id: strawberry.ID, input: UpdateTodoInput) -> UpdateTodoResult:
        if not found: return TodoNotFound(id=id)
        if invalid:   return ValidationError(field="title", message="...")
        return UpdateTodoSuccess(todo=...)

Client query:
    mutation {
      updateTodo(id: "1", input: { title: "New title" }) {
        ... on UpdateTodoSuccess { todo { id title done } }
        ... on TodoNotFound      { id message }
        ... on ValidationError   { field message }
      }
    }

Pros:
  - Fully typed errors — clients know exactly what can go wrong
  - Exhaustive — if a new error type is added, clients can update
  - Distinguishable — "not found" vs "validation error" vs "conflict"
  - Never HTTP 500 for expected failures

Cons:
  - More types to define
  - More verbose queries (inline fragments required)

--- ERROR HANDLING STRATEGIES COMPARED ---

Strategy 1: Simple null + HTTP errors
  return None on not found, raise Exception (becomes HTTP 500)
  → Simple but gives clients no structured error info

Strategy 2: Simple null everywhere
  return None on not found AND validation failure
  → Client can't distinguish failures

Strategy 3: Mutation payload (Pattern B, used here)
  union of success + all expected error types
  → Best structured error info, recommended for production

Strategy 4: Top-level errors array
  GraphQL always returns { data: ..., errors: [...] }
  Unhandled exceptions go here automatically
  → Good for unexpected errors, bad for expected failures

Rule of thumb:
  - Expected failures (not found, validation) → mutation payload union
  - Unexpected failures (DB down, bug)         → let them become GraphQL errors

--- EXERCISES ---

1. Call createTodo with an empty title:
       mutation {
         createTodo(input: { title: "" }) {
           ... on ValidationError { field message }
         }
       }

2. Call createTodo with priority: 10 (out of range):
       mutation {
         createTodo(input: { title: "Test", priority: 10 }) {
           ... on ValidationError  { field message }
           ... on CreateTodoSuccess { todo { id } }
         }
       }

3. Update a todo:
       mutation {
         updateTodo(id: "3", input: { done: true, title: "DataLoaders — done!" }) {
           ... on UpdateTodoSuccess { todo { id title done } }
           ... on TodoNotFound     { message }
         }
       }

4. Delete a todo, then try to delete it again:
       mutation { deleteTodo(id: "1") { ... on TodoItem { id } ... on TodoNotFound { message } } }

5. Run two mutations in one request (they run sequentially):
       mutation {
         first:  createTodo(input: { title: "First" }) { ... on CreateTodoSuccess { todo { id } } }
         second: createTodo(input: { title: "Second" }) { ... on CreateTodoSuccess { todo { id } } }
       }

6. Compare with the simple pattern:
   Call toggleDoneSimple with a missing ID — it returns null.
   Call updateTodo with a missing ID — it returns TodoNotFound with a message.
   Which is more useful to clients?
"""

MUTATION_PATTERNS = {
    "Simple (nullable)":       "Return T? — null on failure, no error detail",
    "Simple (bool)":           "Return Boolean — true/false, no entity returned",
    "Mutation payload (union)": "Return Success | Error1 | Error2 — fully typed",
}

UNSET_VS_NONE = {
    "None":             "Client sent null — explicitly clear this field",
    "strawberry.UNSET": "Client didn't send this field — leave it unchanged",
    "use_case":         "PATCH-style partial update where null and absent differ",
}
