import 'package:firebase_messaging/firebase_messaging.dart';

import 'api.dart';

/// Top-level background handler (must be a top-level or static function for FCM isolates).
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // No-op: the system tray displays the notification. Hook deep-linking here later if needed.
}

/// Requests notification permission, registers the FCM token with the backend, and keeps it fresh.
class MessagingService {
  MessagingService(this._api);
  final Api _api;

  Future<void> init() async {
    try {
      final fm = FirebaseMessaging.instance;
      await fm.requestPermission();

      final token = await fm.getToken();
      if (token != null) {
        await _safeRegister(token);
      }
      fm.onTokenRefresh.listen(_safeRegister);
    } catch (_) {
      // Push is unavailable under stubbed Firebase / dev bypass — skip silently so the
      // home screen still loads.
    }
  }

  Future<void> _safeRegister(String token) async {
    try {
      await _api.registerFcmToken(token);
    } catch (_) {
      // Best-effort: a failed registration must not block app startup.
    }
  }
}
