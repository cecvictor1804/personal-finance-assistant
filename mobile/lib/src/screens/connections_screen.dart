import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../services/api.dart';
import '../services/plaid_service.dart';
import '../widgets.dart';

class ConnectionsScreen extends StatefulWidget {
  const ConnectionsScreen({super.key});

  @override
  State<ConnectionsScreen> createState() => _ConnectionsScreenState();
}

class _ConnectionsScreenState extends State<ConnectionsScreen> {
  late Future<List<PlaidItem>> _future;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<PlaidItem>> _load() => context.read<Api>().listItems();

  void _reload() => setState(() => _future = _load());

  Future<void> _addBank() async {
    setState(() => _busy = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final ok = await context.read<PlaidService>().addBank();
      if (ok) messenger.showSnackBar(const SnackBar(content: Text('Bank connected — syncing…')));
      _reload();
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Could not add bank: $e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _reconnect(PlaidItem item) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await context.read<PlaidService>().reauth(item.id);
      messenger.showSnackBar(const SnackBar(content: Text('Reconnected')));
      _reload();
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Reconnect failed: $e')));
    }
  }

  ({Color color, String label}) _status(String status) => switch (status) {
        'active' => (color: const Color(0xFF16A34A), label: 'Connected'),
        'needsReauth' => (color: const Color(0xFFF59E0B), label: 'Needs re-auth'),
        _ => (color: const Color(0xFFDC2626), label: 'Error'),
      };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Connections')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _busy ? null : _addBank,
        icon: const Icon(Icons.add),
        label: const Text('Add bank'),
      ),
      body: AsyncView<List<PlaidItem>>(
        future: _future,
        onRefresh: () async {
          _reload();
          await _future;
        },
        builder: (items) {
          if (items.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text('No banks linked yet. Tap “Add bank” to connect one.',
                    textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
              ),
            );
          }
          return ListView(
            padding: const EdgeInsets.all(12),
            children: items.map((item) {
              final s = _status(item.status);
              return Card(
                child: ListTile(
                  title: Text(item.institutionName.isNotEmpty ? item.institutionName : item.id),
                  subtitle: Text(item.lastSyncAt != null
                      ? 'Last synced ${formatDateIso(item.lastSyncAt!)}'
                      : 'Not yet synced'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: s.color.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(s.label, style: TextStyle(color: s.color, fontSize: 12)),
                      ),
                      if (item.status == 'needsReauth')
                        TextButton(onPressed: () => _reconnect(item), child: const Text('Fix')),
                    ],
                  ),
                ),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}
