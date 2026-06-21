import 'dart:async';

import 'package:cloud_functions/cloud_functions.dart';
import 'package:plaid_flutter/plaid_flutter.dart';

import 'api.dart';

/// Plaid Link flows: add a new bank, or re-authenticate a broken one (update mode).
///
/// NOTE: `plaid_flutter`'s API surface (LinkTokenConfiguration / PlaidLink streams) varies between
/// major versions. This targets the v4 stream-based API; validate against the version resolved by
/// `flutter pub get` and adjust if the analyzer flags it.
class PlaidService {
  PlaidService(this._api);
  final Api _api;
  final FirebaseFunctions _functions = FirebaseFunctions.instance;

  /// Calls the Cloud Function that mints a Link token for adding a new institution.
  Future<String> _createLinkToken() async {
    final res = await _functions.httpsCallable('create_link_token').call();
    return (res.data as Map)['link_token'] as String;
  }

  Future<void> _exchange(String publicToken, {String? institutionId, String? name}) async {
    await _functions.httpsCallable('exchange_public_token').call({
      'public_token': publicToken,
      'institution': {'institution_id': institutionId, 'name': name},
    });
  }

  /// Opens Plaid Link to add a new bank. Returns true if a connection was established.
  Future<bool> addBank() async {
    final token = await _createLinkToken();
    return _runLink(token, exchange: true);
  }

  /// Opens Plaid Link in update mode to repair a broken connection (no token exchange needed).
  Future<bool> reauth(String itemId) async {
    final token = await _api.reauthLinkToken(itemId);
    return _runLink(token, exchange: false);
  }

  Future<bool> _runLink(String linkToken, {required bool exchange}) async {
    final completer = Completer<bool>();
    late final StreamSubscription<dynamic> successSub;
    late final StreamSubscription<dynamic> exitSub;

    Future<void> cleanup() async {
      await successSub.cancel();
      await exitSub.cancel();
    }

    successSub = PlaidLink.onSuccess.listen((LinkSuccess event) async {
      try {
        if (exchange) {
          final inst = event.metadata.institution;
          await _exchange(event.publicToken, institutionId: inst?.id, name: inst?.name);
        }
        if (!completer.isCompleted) completer.complete(true);
      } catch (_) {
        if (!completer.isCompleted) completer.complete(false);
      } finally {
        await cleanup();
      }
    });

    exitSub = PlaidLink.onExit.listen((LinkExit event) async {
      if (!completer.isCompleted) completer.complete(false);
      await cleanup();
    });

    PlaidLink.create(configuration: LinkTokenConfiguration(token: linkToken));
    PlaidLink.open();
    return completer.future;
  }
}
