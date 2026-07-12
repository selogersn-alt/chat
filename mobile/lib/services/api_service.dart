import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';

class ApiService {
  static Future<String> getServerUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('server_url') ?? AppConstants.defaultServerUrl;
  }

  static Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Token $token',
    };
  }

  static Future<dynamic> get(String endpoint) async {
    final serverUrl = await getServerUrl();
    final headers = await _getHeaders();
    try {
      final response = await http.get(Uri.parse('$serverUrl$endpoint'), headers: headers);
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return jsonDecode(response.body);
      } else {
        try {
          return jsonDecode(response.body); // Try to parse error JSON
        } catch (_) {
          throw Exception('Erreur serveur (Code: ${response.statusCode}). L\'API n\'existe pas ou le serveur est en panne.');
        }
      }
    } catch (e) {
      if (e is FormatException) {
        throw Exception('Erreur de format. Le serveur n\'a pas renvoyé de JSON.');
      }
      throw Exception('Erreur réseau : Impossible de contacter le serveur ($e).');
    }
  }

  static Future<dynamic> post(String endpoint, Map<String, dynamic> body) async {
    final serverUrl = await getServerUrl();
    final headers = await _getHeaders();
    try {
      final response = await http.post(Uri.parse('$serverUrl$endpoint'), headers: headers, body: jsonEncode(body));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return jsonDecode(response.body);
      } else {
        try {
          return jsonDecode(response.body); // Try to parse error JSON
        } catch (_) {
          throw Exception('Erreur serveur (Code: ${response.statusCode}). L\'API n\'existe pas ou le serveur est en panne.');
        }
      }
    } catch (e) {
      if (e is FormatException) {
        throw Exception('Erreur de format. Le serveur n\'a pas renvoyé de JSON.');
      }
      throw Exception('Erreur réseau : Impossible de contacter le serveur ($e).');
    }
  }
}
