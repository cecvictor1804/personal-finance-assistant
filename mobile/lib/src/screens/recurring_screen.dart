import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../services/api.dart';
import '../services/refresh_bus.dart';
import '../widgets.dart';

class _RecData {
  _RecData(this.forecast, this.streams);
  final CashFlowForecast forecast;
  final List<RecurringStream> streams;
}

class RecurringScreen extends StatefulWidget {
  const RecurringScreen({super.key});

  @override
  State<RecurringScreen> createState() => _RecurringScreenState();
}

class _RecurringScreenState extends State<RecurringScreen> {
  late Future<_RecData> _future;
  int _v = -1;

  Future<_RecData> _load() async {
    final api = context.read<Api>();
    final forecast = await api.getForecast(horizonDays: 30);
    final streams = await api.listRecurring();
    return _RecData(forecast, streams);
  }

  @override
  Widget build(BuildContext context) {
    final v = context.watch<RefreshBus>().version;
    if (v != _v) {
      _v = v;
      _future = _load();
    }
    return AsyncView<_RecData>(
      future: _future,
      onRefresh: () async {
        setState(() => _future = _load());
        await _future;
      },
      builder: (d) {
        final outflows = d.streams.where((s) => s.flow == 'outflow').toList();
        final inflows = d.streams.where((s) => s.flow == 'inflow').toList();
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('30-day forecast', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Row(children: [
              _stat('Balance now', d.forecast.currentBalanceCents),
              const SizedBox(width: 12),
              _stat('Projected', d.forecast.projectedEndBalanceCents, colorize: true),
            ]),
            const SizedBox(height: 12),
            Row(children: [
              _stat('Inflow', d.forecast.projectedInflowCents, colorize: true),
              const SizedBox(width: 12),
              _stat('Outflow', d.forecast.projectedOutflowCents, colorize: true),
            ]),
            const SizedBox(height: 20),
            Text('Subscriptions & bills', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (outflows.isEmpty)
              const Text('No recurring charges detected yet.', style: TextStyle(color: Colors.grey)),
            ...outflows.map(_streamTile),
            const SizedBox(height: 16),
            Text('Recurring income', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (inflows.isEmpty)
              const Text('No recurring income detected yet.', style: TextStyle(color: Colors.grey)),
            ...inflows.map(_streamTile),
          ],
        );
      },
    );
  }

  Widget _streamTile(RecurringStream s) => Card(
        child: ListTile(
          title: Text(s.merchant.isNotEmpty ? s.merchant : '—'),
          subtitle: Text(
            '${s.frequency.toLowerCase()}${s.lastDate != null ? ' · last ${formatDateIso(s.lastDate!)}' : ''}',
          ),
          trailing: MoneyText(s.averageAmountCents, colorize: true),
        ),
      );

  Widget _stat(String label, int cents, {bool colorize = false}) => Expanded(
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
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ),
      );
}
