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

  User? get user => _auth.currentUser;
  bool get isSignedIn => _auth.currentUser != null;
  String? get email => _auth.currentUser?.email;
  String? get uid => _auth.currentUser?.uid;

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
    await _googleSignIn.signOut();
    await _auth.signOut();
  }

  /// A current Firebase ID token for the Authorization header (null if signed out).
  Future<String?> idToken() => _auth.currentUser?.getIdToken() ?? Future<String?>.value(null);
}
