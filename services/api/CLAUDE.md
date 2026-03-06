     This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

     ## Commands

     All commands are run from `/services/api/` using [taskipy](https://github.com/taskipy/taskipy) via `pdm run task <name>`:

     | Task | Command | Notes |
     |------|---------|-------|
     | Run dev server | `pdm run task run` | `fastapi dev app/main.py` |
     | Lint | `pdm run task lint` | `ruff check` |
     | Format | `pdm run task format` | Auto-fixes then runs `ruff format` |
     | Test | `pdm run task test` | Formats first, then runs pytest with coverage |

     Run a single test file:
     ```
     pdm run pytest tests/test_lists.py -s -x -vv
     ```

     Run a single test by name:
     ```
     pdm run pytest tests/test_lists.py::test_create_list -s -x -vv
     ```

     ## Why this API exists

     Listmonk natively treats all lists as global — any operator with access to the interface can see and manage all lists, with no concept of per-client ownership. It also
     has no support for multitenancy: you cannot scope a subscriber base or a set of lists to a specific client.

     This API adds a multitenancy layer on top of Listmonk with the following model:

     - Each **client** has a **default list** in Listmonk. Every subscriber added by that client is first enrolled in this default list.
     - A client can create additional **sub-lists**, but those lists only surface subscribers who are already enrolled in the client's default list — the default list acts as
     the superset/filter.
     - **Subscribers are shared** across all of a client's lists (they link via the default list), but clients are fully isolated from each other: client X can only see lists
     and subscribers associated with their own default list.
     - PocketBase stores the ownership mapping: which lists belong to which client (`monk_client_lists`) and the list metadata (`monk_lists`). Listmonk remains the
     authoritative store for actual subscriber data and campaign delivery.

     **Example:** Client `X` owns `LIST_A` (default). They create `LIST_B`. A subscriber added through client `X` is enrolled in `LIST_A` first; they can then be added to
     `LIST_B`, but only if they already belong to `LIST_A`. Client `Y` with a different default list has no visibility into `LIST_A`, `LIST_B`, or their subscribers.

     ## Architecture

     This is a **FastAPI** middleware/proxy service called **listmonk** that bridges two backends:

     - **Listmonk** — an email list management tool. Accessed via HTTP Basic Auth through the `Monk` HTTP client (`app/sessions.py`).
     - **PocketBase** — a backend-as-a-service used as the source of truth for client/list ownership. Accessed via `PocketBaseSession` (`app/sessions.py`).

     ### Request Flow

     Incoming API requests → FastAPI router → `Interface` class (`app/interface.py`) → both Listmonk API and PocketBase are updated in sync.

     The `Interface` class is the core business logic layer. It coordinates writes to both backends, e.g. creating a list in Listmonk and then recording the association in
     PocketBase's `monk_lists` and `monk_client_lists` collections.

     ### Auth

     - Inbound requests to this API use **HTTP Basic Auth**, validated in `get_monk_session()` against `LISTMONK_USER` / `LISTMONK_TOKEN` env vars.
     - Outbound calls to PocketBase use a bot account (`POCKETBASE_BOT_EMAIL` / `POCKETBASE_BOT_PASSWORD`), authenticated as admin by default.

     ### Environment Variables (`.env`)

     ```
     LISTMONK_USER=
     LISTMONK_TOKEN=
     LISTMONK_API_URL=
     POCKETBASE_BOT_EMAIL=
     POCKETBASE_BOT_PASSWORD=
     POCKETBASE_API_URL=
     ```

     ### Key Files

     - `app/interface.py` — `Interface` class with all business logic; `Monk` HTTP client instance (singleton); `get_interface_api()` dependency.
     - `app/sessions.py` — Auth dependencies and the `Monk` HTTP wrapper.
     - `app/schemas.py` — Pydantic schemas for all request/response bodies.
     - `tests/conftest.py` — `get_monk_session` is overridden to bypass auth in tests; integration tests hit real Listmonk and PocketBase instances.

     ### Notes

     - Tests are **integration tests** that hit live Listmonk and PocketBase — a `.env` with valid credentials is required to run them.
     - `app/routers/campaing.py` and `app/routers/leads.py` are stubs (not yet wired into `main.py`).
     - Ruff is configured with `preview = true`, single quotes, and 128-char line length.

     ## Code Style

     All code must be idiomatic Python and pass Ruff checks without errors. Key rules to follow:

     - **No ambiguous variable names**: avoid `l`, `O`, `I` as variable names (E741).
     - **Single quotes** for strings.
     - **Max line length**: 128 characters.
     - Run `pdm run task lint` before considering any code change complete. Fix all reported violations — do not suppress them.
     - Run `pdm run task test` after fix all lints reported violations, and fix all new repoted violations - do not change the tests unless explicited commanded by the owner.
