import 'package:flutter/foundation.dart';

/// Bumped after a global action (e.g. "Sync now") so every screen reloads its data.
class RefreshBus extends ChangeNotifier {
  int version = 0;

  void bump() {
    version++;
    notifyListeners();
  }
}
