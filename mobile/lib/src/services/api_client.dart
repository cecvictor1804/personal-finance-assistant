import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import 'auth_service.dart';

class ApiException implements Exception {
  ApiException(this.status, this.message);
  final int status;
  final String message;
  @override
  String toString() => 'ApiException($status): $message';
}

/// Thin HTTP client that attaches the Firebase ID token to every request and decodes JSON.
class ApiClient {
  ApiClient(this._auth);
  final AuthService _auth;

  Future<Map<String, String>> _headers() async {
    final token = await _auth.idToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Uri _uri(String path) => Uri.parse('${Config.apiBaseUrl}$path');

  Future<dynamic> get(String path) async =>
      _decode(await http.get(_uri(path), headers: await _headers()));

  Future<dynamic> post(String path, [Object? body]) async => _decode(
        await http.post(_uri(path), headers: await _headers(), body: jsonEncode(body ?? {})),
      );

  Future<dynamic> put(String path, [Object? body]) async => _decode(
        await http.put(_uri(path), headers: await _headers(), body: jsonEncode(body ?? {})),
      );

  Future<dynamic> delete(String path) async =>
      _decode(await http.delete(_uri(path), headers: await _headers()));

  dynamic _decode(http.Response res) {
    if (res.statusCode < 200 || res.statusCode >= 300) {
      throw ApiException(res.statusCode, res.body);
    }
    if (res.body.isEmpty) return null;
    return jsonDecode(res.body);
  }
}
