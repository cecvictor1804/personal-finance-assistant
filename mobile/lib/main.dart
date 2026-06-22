import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';

import 'firebase_options.dart';
import 'src/app.dart';
import 'src/services/api.dart';
import 'src/services/api_client.dart';
import 'src/services/auth_service.dart';
import 'src/services/messaging_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // DEBUG STUB: tolerate Firebase init failing so a no-Firebase debug build still launches.
  // Restore by running `flutterfire configure` (real google-services.json + options).
  try {
    await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
  } catch (e) {
    debugPrint('Firebase init skipped (debug stub, no real project): $e');
  }

  final auth = AuthService();
  final api = Api(ApiClient(auth));
  runApp(PfaApp(auth: auth, api: api));
}
