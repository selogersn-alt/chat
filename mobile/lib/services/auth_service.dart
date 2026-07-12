import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class AuthService {
  static Future<Map<String, dynamic>> login(String username, String password, String serverUrl) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('server_url', serverUrl); // Save selected server URL first
      
      final data = await ApiService.post('/api/mobile/login/', {
        'username': username,
        'password': password,
      });

      if (data['status'] == 'success') {
        await prefs.setString('token', data['token']);
        await prefs.setString('username', data['username']);
        await prefs.setString('full_name', data['full_name']);
        await prefs.setString('role', data['role']);
        return {'success': true};
      } else {
        return {'success': false, 'error': data['error'] ?? 'Identifiants invalides.'};
      }
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    final serverUrl = prefs.getString('server_url');
    await prefs.clear();
    // Keep server URL memory
    if (serverUrl != null) {
      await prefs.setString('server_url', serverUrl);
    }
  }
  
  static Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token') != null;
  }
}
