"""Service layer: normalization, categorization, dedup, and the sync orchestrator.

Services depend only on the ports (BankProvider, Repository) and the domain layer, never on
concrete adapters, so they're unit-tested with in-memory fakes.
"""
