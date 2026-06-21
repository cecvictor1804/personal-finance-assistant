import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/api.dart';
import '../services/auth_service.dart';
import '../services/messaging_service.dart';
import '../services/refresh_bus.dart';
import 'add_transaction_screen.dart';
import 'alerts_screen.dart';
import 'budgets_screen.dart';
import 'connections_screen.dart';
import 'dashboard_screen.dart';
import 'recurring_screen.dart';
import 'transactions_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;
  bool _syncing = false;

  static const _titles = ['Dashboard', 'Transactions', 'Budgets', 'Recurring', 'Alerts'];
  static const _pages = [
    DashboardScreen(),
    TransactionsScreen(),
    BudgetsScreen(),
    RecurringScreen(),
    AlertsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => context.read<MessagingService>().init());
  }

  Future<void> _syncNow() async {
    setState(() => _syncing = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      await context.read<Api>().syncNow();
      if (!mounted) return;
      context.read<RefreshBus>().bump();
      messenger.showSnackBar(const SnackBar(content: Text('Synced')));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Sync failed: $e')));
    } finally {
      if (mounted) setState(() => _syncing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_index]),
        actions: [
          IconButton(
            onPressed: _syncing ? null : _syncNow,
            icon: _syncing
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.sync),
            tooltip: 'Sync now',
          ),
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'connections') {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const ConnectionsScreen()),
                );
              } else if (value == 'signout') {
                context.read<AuthService>().signOut();
              }
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'connections', child: Text('Connections')),
              PopupMenuItem(value: 'signout', child: Text('Sign out')),
            ],
          ),
        ],
      ),
      body: IndexedStack(index: _index, children: _pages),
      floatingActionButton: _index == 1
          ? FloatingActionButton(
              onPressed: () async {
                await Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const AddTransactionScreen()),
                );
                if (mounted) context.read<RefreshBus>().bump();
              },
              child: const Icon(Icons.add),
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), label: 'Txns'),
          NavigationDestination(icon: Icon(Icons.track_changes_outlined), label: 'Budgets'),
          NavigationDestination(icon: Icon(Icons.repeat), label: 'Recurring'),
          NavigationDestination(icon: Icon(Icons.notifications_outlined), label: 'Alerts'),
        ],
      ),
    );
  }
}
