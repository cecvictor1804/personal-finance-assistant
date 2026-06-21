import 'package:flutter/foundation.dart';
import 'package:local_auth/local_auth.dart';

/// Biometric app lock. The app locks when sent to the background and requires a biometric (or
/// device-credential) unlock on return. Enabled by default when the device supports it.
class AppLock extends ChangeNotifier {
  final LocalAuthentication _localAuth = LocalAuthentication();

  bool enabled = true;
  bool locked = false;

  Future<bool> deviceSupported() async {
    try {
      return await _localAuth.isDeviceSupported();
    } catch (_) {
      return false;
    }
  }

  void lock() {
    if (!enabled) return;
    locked = true;
    notifyListeners();
  }

  Future<bool> authenticate() async {
    try {
      final ok = await _localAuth.authenticate(
        localizedReason: 'Unlock Personal Finance Assistant',
        options: const AuthenticationOptions(stickyAuth: true),
      );
      if (ok) {
        locked = false;
        notifyListeners();
      }
      return ok;
    } catch (_) {
      return false;
    }
  }

  void setEnabled(bool value) {
    enabled = value;
    if (!value) locked = false;
    notifyListeners();
  }
}
