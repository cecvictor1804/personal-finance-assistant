import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../services/api.dart';
import '../services/refresh_bus.dart';
import '../widgets.dart';

class BudgetsScreen extends StatefulWidget {
  const BudgetsScreen({super.key});

  @override
  State<BudgetsScreen> createState() => _BudgetsScreenState();
}

class _BudgetsScreenState extends State<BudgetsScreen> {
  final String _month = DateFormat('yyyy-MM').format(DateTime.now());
  late Future<Budget> _future;
  int _v = -1;
  int _seededVersion = -2;
  Map<String, int> _caps = {};
  bool _saving = false;

  Future<Budget> _load() => context.read<Api>().getBudget(_month);

  Color _barColor(double pct) {
    if (pct >= 1.0) return const Color(0xFFEF4444);
    if (pct >= 0.8) return const Color(0xFFF59E0B);
    return const Color(0xFF10B981);
  }

  Future<void> _editCap(Category c, int current) async {
    final controller =
        TextEditingController(text: current > 0 ? (current / 100).toStringAsFixed(0) : '');
    final result = await showDialog<int>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('${categoryLabel(c)} budget'),
        content: TextField(
          controller: controller,
          autofocus: true,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(prefixText: '\$ ', labelText: 'Monthly cap'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              final dollars = double.tryParse(controller.text.trim()) ?? 0;
              Navigator.pop(context, (dollars * 100).round());
            },
            child: const Text('Set'),
          ),
        ],
      ),
    );
    if (result == null) return;
    setState(() {
      if (result > 0) {
        _caps[categoryWire(c)] = result;
      } else {
        _caps.remove(categoryWire(c));
      }
    });
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      await context.read<Api>().setBudgetCaps(_month, _caps);
      if (!mounted) return;
      context.read<RefreshBus>().bump();
      messenger.showSnackBar(const SnackBar(content: Text('Budgets saved')));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Failed: $e')));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final v = context.watch<RefreshBus>().version;
    if (v != _v) {
      _v = v;
      _future = _load();
    }
    return AsyncView<Budget>(
      future: _future,
      onRefresh: () async {
        setState(() => _future = _load());
        await _future;
      },
      builder: (budget) {
        // Seed editable caps once per load.
        if (_seededVersion != _v) {
          _seededVersion = _v;
          _caps = Map<String, int>.from(budget.capsCents);
        }
        final rows = [...budgetableCategories]
          ..sort((a, b) =>
              (budget.spentCents[categoryWire(b)] ?? 0) - (budget.spentCents[categoryWire(a)] ?? 0));

        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(DateFormat.yMMMM().format(DateTime.now()),
                      style: Theme.of(context).textTheme.titleMedium),
                  FilledButton(
                    onPressed: _saving ? null : _save,
                    child: _saving
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Text('Save'),
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(12),
                children: rows.map((c) {
                  final wire = categoryWire(c);
                  final spent = budget.spentCents[wire] ?? 0;
                  final cap = _caps[wire] ?? 0;
                  final pct = cap > 0 ? spent / cap : 0.0;
                  return Card(
                    child: ListTile(
                      title: Text(categoryLabel(c)),
                      subtitle: Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: LinearProgressIndicator(
                                value: cap > 0 ? pct.clamp(0.0, 1.0) : 0,
                                minHeight: 6,
                                backgroundColor: const Color(0xFFF1F5F9),
                                color: _barColor(pct),
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              cap > 0
                                  ? '${formatCents(spent)} of ${formatCents(cap)} (${(pct * 100).round()}%)'
                                  : '${formatCents(spent)} spent · no cap',
                              style: const TextStyle(fontSize: 12, color: Colors.grey),
                            ),
                          ],
                        ),
                      ),
                      trailing: IconButton(
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () => _editCap(c, cap),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        );
      },
    );
  }
}
