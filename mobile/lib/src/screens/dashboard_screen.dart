import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../services/api.dart';
import '../services/refresh_bus.dart';
import '../widgets.dart';

class _DashData {
  _DashData(this.accounts, this.txns);
  final List<Account> accounts;
  final List<Transaction> txns;
}

bool _isSpend(Transaction t) =>
    t.amountCents < 0 && t.category != Category.transfer && t.category != Category.income;

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<_DashData> _future;
  int _v = -1;

  Future<_DashData> _load() async {
    final api = context.read<Api>();
    final accounts = await api.listAccounts();
    final txns = await api.listTransactions(limit: 500);
    return _DashData(accounts, txns);
  }

  @override
  Widget build(BuildContext context) {
    final v = context.watch<RefreshBus>().version;
    if (v != _v) {
      _v = v;
      _future = _load();
    }
    return AsyncView<_DashData>(
      future: _future,
      onRefresh: () async {
        setState(() => _future = _load());
        await _future;
      },
      builder: _content,
    );
  }

  Widget _content(_DashData d) {
    final month = DateFormat('yyyy-MM').format(DateTime.now());
    var assets = 0, liabilities = 0;
    for (final a in d.accounts) {
      if (a.isLiability) {
        liabilities += a.balanceCents;
      } else {
        assets += a.balanceCents;
      }
    }
    var spend = 0, income = 0;
    for (final t in d.txns) {
      if (t.date.length < 7 || t.date.substring(0, 7) != month) continue;
      if (_isSpend(t)) spend += -t.amountCents;
      if (t.amountCents > 0 && t.category != Category.transfer) income += t.amountCents;
    }
    final recent = [...d.txns]..sort((a, b) => b.date.compareTo(a.date));

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(children: [
          _stat('Net worth', assets - liabilities, colorize: true),
          const SizedBox(width: 12),
          _stat('Assets', assets),
        ]),
        const SizedBox(height: 12),
        Row(children: [
          _stat('Spending (mo)', -spend, colorize: true),
          const SizedBox(width: 12),
          _stat('Income (mo)', income, colorize: true),
        ]),
        const SizedBox(height: 20),
        Text('Accounts', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        if (d.accounts.isEmpty)
          const Text('No accounts yet — connect a bank.', style: TextStyle(color: Colors.grey)),
        ...d.accounts.map((a) => Card(
              child: ListTile(
                title: Text(a.name),
                subtitle: Text('${a.type}${a.mask != null ? ' ••${a.mask}' : ''}'),
                trailing: MoneyText(a.isLiability ? -a.balanceCents : a.balanceCents, colorize: true),
              ),
            )),
        const SizedBox(height: 12),
        Text('Recent transactions', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        if (recent.isEmpty)
          const Text('No transactions yet.', style: TextStyle(color: Colors.grey)),
        ...recent.take(8).map((t) => Card(
              child: ListTile(
                title: Text(t.title),
                subtitle: Text(formatDateIso(t.date)),
                trailing: MoneyText(t.amountCents, colorize: true),
              ),
            )),
      ],
    );
  }

  Widget _stat(String label, int cents, {bool colorize = false}) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 6),
              MoneyText(cents,
                  colorize: colorize,
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            ],
          ),
        ),
      ),
    );
  }
}
