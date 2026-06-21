import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../services/api.dart';
import '../services/refresh_bus.dart';
import '../widgets.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  late Future<List<Alert>> _future;
  int _v = -1;

  Future<List<Alert>> _load() => context.read<Api>().listAlerts();

  IconData _icon(String severity) => switch (severity) {
        'critical' => Icons.gpp_maybe,
        'warning' => Icons.warning_amber,
        _ => Icons.info_outline,
      };

  Color _color(String severity) => switch (severity) {
        'critical' => const Color(0xFFDC2626),
        'warning' => const Color(0xFFF59E0B),
        _ => Colors.grey,
      };

  Future<void> _markRead(Alert a) async {
    try {
      await context.read<Api>().markAlertRead(a.id);
      if (mounted) setState(() => _future = _load());
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final v = context.watch<RefreshBus>().version;
    if (v != _v) {
      _v = v;
      _future = _load();
    }
    return AsyncView<List<Alert>>(
      future: _future,
      onRefresh: () async {
        setState(() => _future = _load());
        await _future;
      },
      builder: (alerts) {
        if (alerts.isEmpty) {
          return const Center(
              child: Text("No alerts. You're all clear.", style: TextStyle(color: Colors.grey)));
        }
        return ListView.builder(
          padding: const EdgeInsets.all(12),
          itemCount: alerts.length,
          itemBuilder: (_, i) {
            final a = alerts[i];
            return Card(
              color: a.read ? null : const Color(0xFFF8FAFC),
              child: ListTile(
                leading: Icon(_icon(a.severity), color: _color(a.severity)),
                title: Text(a.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(a.message),
                    const SizedBox(height: 2),
                    Text(formatDateIso(a.createdAt),
                        style: const TextStyle(fontSize: 11, color: Colors.grey)),
                  ],
                ),
                trailing: a.read
                    ? null
                    : TextButton(onPressed: () => _markRead(a), child: const Text('Read')),
                isThreeLine: true,
              ),
            );
          },
        );
      },
    );
  }
}
