"""Ports: abstract interfaces the services depend on. Adapters implement them.

This keeps the bank aggregator (Plaid) and the datastore (Firestore) behind seams so the core
logic is testable with in-memory fakes and a different provider could be swapped in later.
"""
