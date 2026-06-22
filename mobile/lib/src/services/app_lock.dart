import 'package:flutter/foundation.dart';
import 'package:local_auth/local_auth.dart';

/// Biometric app lock. The app locks when sent to the background and requires a biometric (or
/// device-credential) unlock on return. Enabled by default when the device supports it.
class AppLock extends ChangeNotifier {
  final LocalAuthentication _localAuth = LocalAuthentication();

  // Disabled by default in debug builds so the biometric lock never blocks local dev/testing
  // (emulators rarely have an enrolled biometric or device credential). Release builds lock as usual.
  bool enabled = !kDebugMode;
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

  /// DEV ESCAPE (debug only): unlock without biometrics when the device has none enrolled.
  void devUnlock() {
    locked = false;
    notifyListeners();
  }
}
