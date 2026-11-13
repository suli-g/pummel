# Dependency Manifest

This document defines the pre-approved technology stack and dependency governance protocol for the **PUML-to-Code** (`pummel`) compiler pipeline.

## Pre-Approved Dependencies & Toolchain

| Category | Approved Tool / Package | Scope / Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.12+ | Core runtime and type system |
| **Package Manager** | `uv` | Environment management and dependency locking |
| **Data Validation** | `pydantic` (V2) | Strict boundary validation and schema modeling |
| **State Persistence** | `sqlite3` (Python stdlib) | Local relational state storage (no external ORMs/drivers) |
| **Vector Search (RAG)** | `sqlite-vec` *(authorized)* | Embedded SQLite vector similarity search (`vec0`) |
| **Embeddings (RAG)** | `sentence-transformers` *(authorized)* | Local embedding generation for RAG indexing & retrieval |
| **Linting & Formatting** | `ruff`, `flake8` | PEP 8 compliance, import sorting, and static lint checks |
| **Type Checking** | `mypy` (strict mode) | Static type verification across all modules |
| **Testing** | `pytest` | Unit and integration test execution |
| **System Binaries** | `git`, `gh`, `plantuml`, `mmdc` | Version control, GitHub CLI, and diagram rendering |

## Dependency Governance Protocol

1. **Strict Prohibition on Unapproved Dependencies**: No external PyPI packages, third-party libraries, or system binaries outside the pre-approved list above may be adopted, installed, or imported into the codebase.
2. **Standard Library Preference**: All utility functionality (e.g., subprocess execution, SQLite persistence, path handling, logging, dataclasses/protocols) must rely exclusively on the Python 3.12+ standard library unless covered by the pre-approved list.
3. **Change Authorization Procedure**:
   - If a feature or bug fix requires a new external PyPI package or system binary, execution **must halt immediately**.
   - The requirement, justification, and security/maintenance impact must be explicitly documented.
   - Explicit authorization from the developer must be obtained before modifying `pyproject.toml`, `uv.lock`, or system tooling.
