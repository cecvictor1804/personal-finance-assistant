import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'services/api.dart';
import 'services/app_lock.dart';
import 'services/auth_service.dart';
import 'services/messaging_service.dart';
import 'services/plaid_service.dart';
import 'services/refresh_bus.dart';
import 'screens/home_shell.dart';
import 'screens/lock_screen.dart';
import 'screens/login_screen.dart';
import 'theme.dart';

class PfaApp extends StatelessWidget {
  const PfaApp({super.key, required this.auth, required this.api});
  final AuthService auth;
  final Api api;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthService>.value(value: auth),
        Provider<Api>.value(value: api),
        ChangeNotifierProvider<AppLock>(create: (_) => AppLock()),
        ChangeNotifierProvider<RefreshBus>(create: (_) => RefreshBus()),
        Provider<PlaidService>(create: (_) => PlaidService(api)),
        Provider<MessagingService>(create: (_) => MessagingService(api)),
      ],
      child: MaterialApp(
        title: 'Finance Assistant',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(),
        home: const AuthGate(),
      ),
    );
  }
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    if (!auth.isSignedIn) return const LoginScreen();
    return const LockGate(child: HomeShell());
  }
}

/// Wraps the app in a biometric lock that engages when backgrounded.
class LockGate extends StatefulWidget {
  const LockGate({super.key, required this.child});
  final Widget child;

  @override
  State<LockGate> createState() => _LockGateState();
}

class _LockGateState extends State<LockGate> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final lock = context.read<AppLock>();
      if (lock.enabled) lock.lock();
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused) {
      context.read<AppLock>().lock();
    }
  }

  @override
  Widget build(BuildContext context) {
    final lock = context.watch<AppLock>();
    if (lock.enabled && lock.locked) return const LockScreen();
    return widget.child;
  }
}
