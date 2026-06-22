import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/app_lock.dart';

class LockScreen extends StatefulWidget {
  const LockScreen({super.key});

  @override
  State<LockScreen> createState() => _LockScreenState();
}

class _LockScreenState extends State<LockScreen> {
  @override
  void initState() {
    super.initState();
    // Prompt for biometrics as soon as the lock screen appears.
    WidgetsBinding.instance.addPostFrameCallback((_) => context.read<AppLock>().authenticate());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.lock_outline, size: 56, color: Color(0xFF0F172A)),
            const SizedBox(height: 16),
            const Text('Locked', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => context.read<AppLock>().authenticate(),
              icon: const Icon(Icons.fingerprint),
              label: const Text('Unlock'),
            ),
            if (kDebugMode) ...[
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => context.read<AppLock>().devUnlock(),
                child: const Text('Skip (dev)'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
