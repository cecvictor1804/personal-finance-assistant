import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../services/api.dart';
import '../services/refresh_bus.dart';
import '../widgets.dart';

class TransactionsScreen extends StatefulWidget {
  const TransactionsScreen({super.key});

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  late Future<List<Transaction>> _future;
  int _v = -1;

  Future<List<Transaction>> _load() => context.read<Api>().listTransactions(limit: 200);

  Future<void> _recategorize(Transaction t) async {
    final picked = await showModalBottomSheet<Category>(
      context: context,
      showDragHandle: true,
      builder: (_) => ListView(
        children: Category.values
            .map((c) => ListTile(
                  leading: CategoryChip(c),
                  trailing: c == t.category ? const Icon(Icons.check) : null,
                  onTap: () => Navigator.pop(context, c),
                ))
            .toList(),
      ),
    );
    if (picked == null || picked == t.category) return;
    try {
      await context.read<Api>().recategorize(t.id, picked);
      if (mounted) setState(() => _future = _load());
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final v = context.watch<RefreshBus>().version;
    if (v != _v) {
      _v = v;
      _future = _load();
    }
    return AsyncView<List<Transaction>>(
      future: _future,
      onRefresh: () async {
        setState(() => _future = _load());
        await _future;
      },
      builder: (txns) {
        if (txns.isEmpty) {
          return const Center(child: Text('No transactions yet.', style: TextStyle(color: Colors.grey)));
        }
        return ListView.builder(
          padding: const EdgeInsets.all(12),
          itemCount: txns.length,
          itemBuilder: (_, i) {
            final t = txns[i];
            return Card(
              child: ListTile(
                title: Row(children: [
                  Flexible(child: Text(t.title, overflow: TextOverflow.ellipsis)),
                  if (t.pending) const Padding(
                    padding: EdgeInsets.only(left: 6),
                    child: Text('pending', style: TextStyle(fontSize: 10, color: Colors.orange)),
                  ),
                  if (t.possibleDuplicateOf != null) const Padding(
                    padding: EdgeInsets.only(left: 6),
                    child: Icon(Icons.copy, size: 14, color: Colors.deepOrange),
                  ),
                ]),
                subtitle: Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
                    CategoryChip(t.category),
                    Text(formatDateIso(t.date), style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ]),
                ),
                trailing: MoneyText(t.amountCents, colorize: true),
                onTap: () => _recategorize(t),
              ),
            );
          },
        );
      },
    );
  }
}
