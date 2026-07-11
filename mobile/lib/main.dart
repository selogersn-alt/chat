import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(const LogerSenegalApp());
}

class LogerSenegalApp extends StatelessWidget {
  const LogerSenegalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Loger Sénégal CRM',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0F4F2C),
          primary: const Color(0xFF0F4F2C),
          secondary: const Color(0xFF1B6B3E),
        ),
        scaffoldBackgroundColor: const Color(0xFFF2F8F5),
        useMaterial3: true,
      ),
      home: const AuthWrapper(),
    );
  }
}

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  bool _isLoading = true;
  String? _token;

  @override
  void initState() {
    super.initState();
    _checkLoginStatus();
  }

  Future<void> _checkLoginStatus() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _token = prefs.getString('token');
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    return _token == null ? const LoginScreen() : const DashboardScreen();
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _serverUrlController = TextEditingController(text: 'https://chat.logersenegal.com');
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _login() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();
    final serverUrl = _serverUrlController.text.trim();

    if (username.isEmpty || password.isEmpty || serverUrl.isEmpty) {
      setState(() {
        _isLoading = false;
        _errorMessage = 'Veuillez remplir tous les champs.';
      });
      return;
    }

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/mobile/login/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['status'] == 'success') {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('token', data['token']);
        await prefs.setString('username', data['username']);
        await prefs.setString('full_name', data['full_name']);
        await prefs.setString('role', data['role']);
        await prefs.setString('server_url', serverUrl);

        if (mounted) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const DashboardScreen()),
          );
        }
      } else {
        setState(() {
          _errorMessage = data['error'] ?? 'Connexion échouée.';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur réseau : Impossible de contacter le serveur.';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF052212), Color(0xFF0F4F2C)],
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Card(
              color: Colors.white.withOpacity(0.95),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
              elevation: 8,
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.maps_home_work, size: 64, color: Color(0xFF0F4F2C)),
                    const SizedBox(height: 16),
                    const Text(
                      'Loger Sénégal',
                      style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF052212)),
                    ),
                    const Text('Console Mobile Agent', style: TextStyle(color: Colors.grey)),
                    const SizedBox(height: 32),
                    if (_errorMessage != null) ...[
                      Text(_errorMessage!, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 16),
                    ],
                    TextField(
                      controller: _serverUrlController,
                      decoration: const InputDecoration(
                        labelText: 'Adresse Serveur',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.dns),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _usernameController,
                      decoration: const InputDecoration(
                        labelText: 'Identifiant',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.person),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: 'Mot de passe',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.lock),
                      ),
                    ),
                    const SizedBox(height: 32),
                    _isLoading
                        ? const CircularProgressIndicator()
                        : ElevatedButton(
                            onPressed: _login,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF0F4F2C),
                              foregroundColor: Colors.white,
                              minimumSize: const Size(double.infinity, 50),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                            child: const Text('Se Connecter', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<dynamic> _conversations = [];
  bool _isLoading = true;
  String _activeTab = 'ACTIVE'; // ACTIVE, PENDING, CLOSED
  String? _fullName;

  @override
  void initState() {
    super.initState();
    _loadProfileAndData();
  }

  Future<void> _loadProfileAndData() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _fullName = prefs.getString('full_name');
    });
    _fetchConversations();
  }

  Future<void> _fetchConversations() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');
      final serverUrl = prefs.getString('server_url');

      final response = await http.get(
        Uri.parse('$serverUrl/api/mobile/conversations/?status=$_activeTab'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $token',
        },
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 200 && data['status'] == 'success') {
        setState(() {
          _conversations = data['conversations'];
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur lors du chargement des conversations.')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_fullName ?? 'Dashboard'),
        backgroundColor: const Color(0xFF0F4F2C),
        foregroundColor: Colors.white,
        actions: [
          IconButton(onPressed: _fetchConversations, icon: const Icon(Icons.refresh)),
          IconButton(onPressed: _logout, icon: const Icon(Icons.logout)),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _activeTab == 'ACTIVE' ? 0 : (_activeTab == 'PENDING' ? 1 : 2),
        onTap: (index) {
          setState(() {
            _activeTab = index == 0 ? 'ACTIVE' : (index == 1 ? 'PENDING' : 'CLOSED');
          });
          _fetchConversations();
        },
        selectedItemColor: const Color(0xFF0F4F2C),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.chat), label: 'Actives'),
          BottomNavigationBarItem(icon: Icon(Icons.hourglass_empty), label: 'En attente'),
          BottomNavigationBarItem(icon: Icon(Icons.archive), label: 'Fermées'),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _conversations.isEmpty
              ? const Center(child: Text('Aucune discussion.'))
              : ListView.builder(
                  padding: const EdgeInsets.all(8),
                  itemCount: _conversations.length,
                  itemBuilder: (context, index) {
                    final c = _conversations[index];
                    return Card(
                      color: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: const Color(0xFFE1EFE7),
                          foregroundColor: const Color(0xFF0F4F2C),
                          child: Text(c['client_name'].substring(0, 1).toUpperCase()),
                        ),
                        title: Text(
                          c['client_name'],
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(c['last_message_text'], maxLines: 1, overflow: TextOverflow.ellipsis),
                            const SizedBox(height: 4),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFFE1EFE7),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                c['pipeline_stage'],
                                style: const TextStyle(fontSize: 10, color: Color(0xFF0F4F2C), fontWeight: FontWeight.bold),
                              ),
                            )
                          ],
                        ),
                        trailing: c['unread_count'] > 0
                            ? CircleAvatar(
                                radius: 10,
                                backgroundColor: Colors.red,
                                child: Text(
                                  c['unread_count'].toString(),
                                  style: const TextStyle(color: Colors.white, fontSize: 10),
                                ),
                              )
                            : null,
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => ChatScreen(conversationId: c['id']),
                            ),
                          ).then((_) => _fetchConversations());
                        },
                      ),
                    );
                  },
                ),
    );
  }
}

class ChatScreen extends StatefulWidget {
  final String conversationId;
  const ChatScreen({super.key, required this.conversationId});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  List<dynamic> _messages = [];
  bool _isLoading = true;
  String? _clientName;
  final _messageController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchMessages();
  }

  Future<void> _fetchMessages() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');
      final serverUrl = prefs.getString('server_url');

      final response = await http.get(
        Uri.parse('$serverUrl/api/mobile/conversations/${widget.conversationId}/messages/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $token',
        },
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 200 && data['status'] == 'success') {
        setState(() {
          _messages = data['messages'];
          _clientName = data['client_name'];
          _isLoading = false;
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur lors du chargement des messages.')),
      );
    }
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    _messageController.clear();

    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');
      final serverUrl = prefs.getString('server_url');

      final response = await http.post(
        Uri.parse('$serverUrl/api/send/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $token',
        },
        body: jsonEncode({
          'conversation_id': widget.conversationId,
          'message': text,
        }),
      );

      if (response.statusCode == 200) {
        _fetchMessages();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur d\'envoi.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_clientName ?? 'Discussions'),
        backgroundColor: const Color(0xFF0F4F2C),
        foregroundColor: Colors.white,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final m = _messages[index];
                      final isMe = m['sender_role'] != 'CLIENT';
                      return Align(
                        alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.symmetric(vertical: 4),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: isMe ? const Color(0xFF0F4F2C) : Colors.white,
                            borderRadius: BorderRadius.only(
                              topLeft: const Radius.circular(16),
                              topRight: const Radius.circular(16),
                              bottomLeft: isMe ? const Radius.circular(16) : Radius.zero,
                              bottomRight: isMe ? Radius.zero : const Radius.circular(16),
                            ),
                            boxShadow: [
                              BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, 2))
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                m['text'],
                                style: TextStyle(color: isMe ? Colors.white : Colors.black87),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(8.0),
                  color: Colors.white,
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _messageController,
                          decoration: const InputDecoration(
                            hintText: 'Tapez votre message...',
                            border: InputBorder.none,
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.send, color: Color(0xFF0F4F2C)),
                        onPressed: _sendMessage,
                      ),
                    ],
                  ),
                )
              ],
            ),
    );
  }
}
