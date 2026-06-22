import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';

/// Owns Firebase Auth + Google Sign-In and exposes the current user and a fresh ID token.
class AuthService extends ChangeNotifier {
  AuthService() {
    _auth.authStateChanges().listen((_) => notifyListeners());
  }

  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();

  /// DEV BYPASS: when true, the app treats the session as signed-in without Firebase.
  /// Pairs with the backend running in AUTH_DISABLED=true mode (no ID token required;
  /// requests run as DEV_UID, which defaults to 'dev-user').
  bool _devBypass = false;
  bool get isDevBypass => _devBypass;

  /// Enters dev mode: no real auth and no ID token. Lets you explore the UI locally.
  void continueAsDev() {
    _devBypass = true;
    notifyListeners();
  }

  User? get user => _auth.currentUser;
  bool get isSignedIn => _devBypass || _auth.currentUser != null;
  String? get email => _devBypass ? 'dev@localhost' : _auth.currentUser?.email;
  String? get uid => _devBypass ? 'dev-user' : _auth.currentUser?.uid;

  Future<void> signInWithGoogle() async {
    final googleUser = await _googleSignIn.signIn();
    if (googleUser == null) return; // user cancelled
    final googleAuth = await googleUser.authentication;
    final credential = GoogleAuthProvider.credential(
      accessToken: googleAuth.accessToken,
      idToken: googleAuth.idToken,
    );
    await _auth.signInWithCredential(credential);
  }

  Future<void> signOut() async {
    _devBypass = false;
    await _googleSignIn.signOut();
    await _auth.signOut();
    notifyListeners();
  }

  /// A current Firebase ID token for the Authorization header (null if signed out or in dev mode).
  Future<String?> idToken() {
    if (_devBypass) return Future<String?>.value(null);
    return _auth.currentUser?.getIdToken() ?? Future<String?>.value(null);
  }
}
