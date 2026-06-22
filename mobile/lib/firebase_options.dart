// DEBUG STUB — these are NOT real Firebase credentials. They are well-formed dummy values that let
// `Firebase.initializeApp` succeed offline so a debug APK can be built and launched WITHOUT a real
// Firebase project. Auth / push / functions will not work at runtime.
//
// To restore real functionality, run `flutterfire configure` (it overwrites this file with the real
// values for your Firebase project) — that reverts the stub.

import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart' show defaultTargetPlatform, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      default:
        throw UnsupportedError(
          'No Firebase options for $defaultTargetPlatform. Run `flutterfire configure`.',
        );
    }
  }

  // Well-formed dummy values (valid shapes, fake content): appId = 1:<senderId>:android:<hex>,
  // apiKey = AIza... so initializeApp validation passes locally.
  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyDEBUGSTUB0000000000000000000000000',
    appId: '1:123456789012:android:0000000000000000000000',
    messagingSenderId: '123456789012',
    projectId: 'pfa-debug-stub',
    storageBucket: 'pfa-debug-stub.appspot.com',
  );
}
