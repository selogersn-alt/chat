import 'dart:convert';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

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
        fontFamily: 'Outfit',
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0F4F2C),
          primary: const Color(0xFF0F4F2C),
          secondary: const Color(0xFF1B6B3E),
          surface: Colors.white,
        ),
        scaffoldBackgroundColor: const Color(0xFFF4F8F6),
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
        body: Center(
          child: CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0F4F2C)),
          ),
        ),
      );
    }
    return _token == null ? const LoginScreen() : const MainLayoutScreen();
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
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _login() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();
    const serverUrl = 'https://chat.logersenegal.com';

    if (username.isEmpty || password.isEmpty) {
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
            MaterialPageRoute(builder: (context) => const MainLayoutScreen()),
          );
        }
      } else {
        setState(() {
          _errorMessage = data['error'] ?? 'Identifiants invalides.';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur réseau : Impossible de connecter le serveur.';
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
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF052212), Color(0xFF0F4F2C), Color(0xFF1B6B3E)],
              ),
            ),
          ),
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(30),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                  child: Container(
                    padding: const EdgeInsets.all(32.0),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.85),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(color: Colors.white.withValues(alpha: 0.3)),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: const BoxDecoration(
                            color: Color(0xFFE1EFE7),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.maps_home_work, size: 48, color: Color(0xFF0F4F2C)),
                        ),
                        const SizedBox(height: 20),
                        const Text(
                          'Loger Sénégal',
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.w800,
                            color: Color(0xFF052212),
                            letterSpacing: 0.5,
                          ),
                        ),
                        const Text(
                          'Console Mobile Agent',
                          style: TextStyle(color: Color(0xFF1B6B3E), fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 32),
                        if (_errorMessage != null) ...[
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.red.shade50,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.red.shade100),
                            ),
                            child: Text(
                              _errorMessage!,
                              textAlign: TextAlign.center,
                              style: TextStyle(color: Colors.red.shade800, fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                          ),
                          const SizedBox(height: 20),
                        ],
                        TextField(
                          controller: _usernameController,
                          decoration: InputDecoration(
                            labelText: "Nom d'utilisateur",
                            labelStyle: const TextStyle(color: Color(0xFF0F4F2C)),
                            filled: true,
                            fillColor: Colors.white.withValues(alpha: 0.6),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16),
                              borderSide: BorderSide.none,
                            ),
                            prefixIcon: const Icon(Icons.person, color: Color(0xFF0F4F2C)),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _passwordController,
                          obscureText: true,
                          decoration: InputDecoration(
                            labelText: 'Mot de passe',
                            labelStyle: const TextStyle(color: Color(0xFF0F4F2C)),
                            filled: true,
                            fillColor: Colors.white.withValues(alpha: 0.6),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16),
                              borderSide: BorderSide.none,
                            ),
                            prefixIcon: const Icon(Icons.lock, color: Color(0xFF0F4F2C)),
                          ),
                        ),
                        const SizedBox(height: 32),
                        _isLoading
                            ? const CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0F4F2C)))
                            : ElevatedButton(
                                onPressed: _login,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF0F4F2C),
                                  foregroundColor: Colors.white,
                                  minimumSize: const Size(double.infinity, 56),
                                  elevation: 2,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                                ),
                                child: const Text(
                                  'Se Connecter',
                                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                                ),
                              ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class MainLayoutScreen extends StatefulWidget {
  const MainLayoutScreen({super.key});

  @override
  State<MainLayoutScreen> createState() => _MainLayoutScreenState();
}

class _MainLayoutScreenState extends State<MainLayoutScreen> {
  int _currentIndex = 0;
  final List<Widget> _screens = [
    const ConversationsScreen(),
    const CatalogueScreen(),
    const VisitesScreen(),
    const PartnersScreen(),
    const ProfilScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, -2)),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() {
              _currentIndex = index;
            });
          },
          type: BottomNavigationBarType.fixed,
          backgroundColor: Colors.white,
          selectedItemColor: const Color(0xFF0F4F2C),
          unselectedItemColor: Colors.grey.shade500,
          selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
          unselectedLabelStyle: const TextStyle(fontSize: 12),
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.chat_bubble_outline),
              activeIcon: Icon(Icons.chat_bubble),
              label: 'Chats',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.menu_book_outlined),
              activeIcon: Icon(Icons.menu_book),
              label: 'Catalogue',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.calendar_month_outlined),
              activeIcon: Icon(Icons.calendar_month),
              label: 'Visites',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.people_outline),
              activeIcon: Icon(Icons.people),
              label: 'Partenaires',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline),
              activeIcon: Icon(Icons.person),
              label: 'Profil',
            ),
          ],
        ),
      ),
    );
  }
}

class ConversationsScreen extends StatefulWidget {
  const ConversationsScreen({super.key});

  @override
  State<ConversationsScreen> createState() => _ConversationsScreenState();
}

class _ConversationsScreenState extends State<ConversationsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _allConversations = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadConversations();
  }

  Future<void> _loadConversations() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/mobile/conversations/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          setState(() {
            _allConversations = data['conversations'];
            _isLoading = false;
          });
        }
      } else {
        setState(() {
          _errorMessage = 'Erreur lors du chargement des conversations.';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur réseau : Impossible de contacter le serveur.';
        _isLoading = false;
      });
    }
  }

  List<dynamic> _filterConversations(String status) {
    return _allConversations.where((c) => c['status'].toString().toLowerCase() == status.toLowerCase()).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: const Color(0xFFE1EFE7), borderRadius: BorderRadius.circular(10)),
              child: const Icon(Icons.maps_home_work, color: Color(0xFF0F4F2C)),
            ),
            const SizedBox(width: 12),
            const Text(
              'Loger Sénégal',
              style: TextStyle(fontWeight: FontWeight.w800, color: Color(0xFF052212), fontSize: 20),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() {
                _isLoading = true;
              });
              _loadConversations();
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF0F4F2C),
          unselectedLabelColor: Colors.grey,
          indicatorColor: const Color(0xFF0F4F2C),
          labelStyle: const TextStyle(fontWeight: FontWeight.bold),
          tabs: const [
            Tab(text: 'Actives'),
            Tab(text: 'En Attente'),
            Tab(text: 'Fermées'),
          ],
        ),
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0F4F2C))))
          : _errorMessage != null
              ? Center(child: Text(_errorMessage!, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)))
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildConversationList('active'),
                    _buildConversationList('pending'),
                    _buildConversationList('closed'),
                  ],
                ),
    );
  }

  Widget _buildConversationList(String status) {
    final list = _filterConversations(status);

    if (list.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey.shade400),
            const SizedBox(height: 16),
            Text(
              'Aucune discussion $status.',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 16, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: list.length,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final c = list[index];
        final unreadCount = c['unread_count'] ?? 0;
        final isWhatsApp = c['is_whatsapp'] ?? false;

        return Card(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: Colors.grey.shade100),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: CircleAvatar(
              radius: 26,
              backgroundColor: isWhatsApp ? const Color(0xFF25D366) : const Color(0xFFE1EFE7),
              child: isWhatsApp
                  ? const Icon(Icons.phone_iphone, color: Colors.white, size: 24)
                  : const Icon(Icons.person, color: Color(0xFF0F4F2C), size: 26),
            ),
            title: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    c['client_name'] ?? 'Client',
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: Color(0xFF052212)),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Text(
                  c['last_message_time'] ?? '',
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                ),
              ],
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 8.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    c['last_message'] ?? 'Aucun message.',
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      if (c['pipeline_stage_display'] != null)
                        _buildBadge(
                          c['pipeline_stage_display'],
                          _getPipelineColor(c['pipeline_stage']),
                        ),
                      const Spacer(),
                      if (unreadCount > 0)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0F4F2C),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            unreadCount.toString(),
                            style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
            onTap: () async {
              await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ChatDetailScreen(conversationId: c['id']),
                ),
              );
              _loadConversations();
            },
          ),
        );
      },
    );
  }

  Widget _buildBadge(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
      ),
    );
  }

  Color _getPipelineColor(String? stage) {
    switch (stage?.toLowerCase()) {
      case 'new':
        return Colors.blue;
      case 'qualification':
        return Colors.orange;
      case 'proposition':
        return Colors.teal;
      case 'visit_scheduled':
        return Colors.indigo;
      case 'visit_done':
        return Colors.purple;
      case 'negociation':
        return Colors.amber.shade900;
      case 'won':
        return const Color(0xFF0F4F2C);
      case 'lost':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}

class ChatDetailScreen extends StatefulWidget {
  final String conversationId;
  const ChatDetailScreen({super.key, required this.conversationId});

  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  Map<String, dynamic> _convInfo = {};
  List<dynamic> _messages = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadMessages();
  }

  Future<void> _loadMessages() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/mobile/conversations/${widget.conversationId}/messages/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          setState(() {
            _convInfo = {
              'id': widget.conversationId,
              'client_name': data['client_name'],
              'client_phone': data['client_phone'],
              'pipeline_stage': data['pipeline_stage'],
              'client_project': data['client_project'] ?? '',
              'client_property_type': data['client_property_type'] ?? '',
              'client_zone': data['client_zone'] ?? '',
              'notes': data['notes'] ?? '',
            };
            _messages = data['messages'];
            _isLoading = false;
          });
          _scrollToBottom();
        }
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Impossible de charger la conversation.';
        _isLoading = false;
      });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final content = _messageController.text.trim();
    if (content.isEmpty) return;

    _messageController.clear();

    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/send/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'conversation_id': widget.conversationId,
          'content': content,
        }),
      );

      if (response.statusCode == 200) {
        _loadMessages();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Erreur lors de l\'envoi du message.')),
        );
      }
    }
  }

  Future<void> _updateProspectField(String field, String value) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/mobile/conversations/update/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'conversation_id': widget.conversationId,
          field: value,
        }),
      );

      if (response.statusCode == 200) {
        _loadMessages();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Prospect mis à jour !'), duration: Duration(seconds: 1)),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Erreur lors de la mise à jour.')),
        );
      }
    }
  }

  void _showFicheProspectDrawer() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) {
        final pipelineOptions = [
          {'val': 'new', 'disp': 'Nouveau'},
          {'val': 'qualification', 'disp': 'Qualification'},
          {'val': 'proposition', 'disp': 'Proposition'},
          {'val': 'visit_scheduled', 'disp': 'Visite Programmée'},
          {'val': 'visit_done', 'disp': 'Visite Faite'},
          {'val': 'negociation', 'disp': 'Négociation'},
          {'val': 'won', 'disp': 'Gagné (Vendu)'},
          {'val': 'lost', 'disp': 'Perdu'},
        ];

        final projectController = TextEditingController(text: _convInfo['client_project']);
        final typeController = TextEditingController(text: _convInfo['client_property_type']);
        final zoneController = TextEditingController(text: _convInfo['client_zone']);
        final notesController = TextEditingController(text: _convInfo['notes']);

        return Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(context).viewInsets.bottom,
            top: 24,
            left: 24,
            right: 24,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Fiche Prospect', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                    IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                  ],
                ),
                const Divider(),
                const SizedBox(height: 16),
                const Text('Étape du Pipeline', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _convInfo['pipeline_stage'],
                  decoration: InputDecoration(
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                  ),
                  items: pipelineOptions.map((opt) {
                    return DropdownMenuItem(value: opt['val'], child: Text(opt['disp']!));
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      _updateProspectField('pipeline_stage', val);
                    }
                  },
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: projectController,
                  decoration: const InputDecoration(labelText: 'Projet Client'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: typeController,
                  decoration: const InputDecoration(labelText: 'Type de bien'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: zoneController,
                  decoration: const InputDecoration(labelText: 'Zone souhaitée'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: notesController,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: 'Notes de l\'Agent'),
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () {
                    _updateProspectField('client_project', projectController.text);
                    _updateProspectField('client_property_type', typeController.text);
                    _updateProspectField('client_zone', zoneController.text);
                    _updateProspectField('notes', notesController.text);
                    Navigator.pop(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0F4F2C),
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 50),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: const Text('Enregistrer les modifications'),
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showCatalogueShare() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) {
        return const CatalogueSelectionSheet();
      },
    ).then((result) {
      if (result != null && result is String) {
        setState(() {
          _messageController.text = result;
        });
      }
    });
  }

  void _showPartnersSelection() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) {
        return PartnersSelectionSheet(conversationId: widget.conversationId);
      },
    );
  }

  void _showTemplatesSelector() {
    final templates = [
      "Bonjour, j'espère que vous allez bien. Je vous contacte de la part de Loger Sénégal.",
      "Voici les propriétés correspondant à votre recherche. N'hésitez pas à me donner votre avis.",
      "Nous pouvons programmer une visite de bien immobilier. Quel jour vous conviendrait ?",
      "Votre visite a été planifiée avec succès. Notre agent sera présent sur place.",
      "Merci de votre confiance en Loger Sénégal. Notre équipe reste à votre disposition.",
    ];

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Modèles de Messages', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const Divider(),
              Expanded(
                child: ListView.builder(
                  itemCount: templates.length,
                  itemBuilder: (context, index) {
                    final t = templates[index];
                    return ListTile(
                      title: Text(t, style: const TextStyle(fontSize: 14)),
                      onTap: () {
                        setState(() {
                          _messageController.text = t;
                        });
                        Navigator.pop(context);
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final clientName = _convInfo['client_name'] ?? 'Chat';
    final clientPhone = _convInfo['client_phone'] ?? 'N/A';

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(clientName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            Text(clientPhone, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.people_outline, color: Color(0xFF0F4F2C)),
            onPressed: _showPartnersSelection,
            tooltip: 'Associer Partenaire',
          ),
          IconButton(
            icon: const Icon(Icons.list_alt, color: Color(0xFF0F4F2C)),
            onPressed: _showFicheProspectDrawer,
            tooltip: 'Fiche Prospect',
          ),
        ],
        backgroundColor: Colors.white,
        elevation: 1,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0F4F2C))))
          : _errorMessage != null
              ? Center(child: Text(_errorMessage!))
              : Container(
                  color: const Color(0xFFECE5DD), // Classic WhatsApp Background Color
                  child: Column(
                    children: [
                      Expanded(
                        child: ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.all(16),
                          itemCount: _messages.length,
                          itemBuilder: (context, index) {
                            final msg = _messages[index];
                            final isSelf = msg['sender_is_self'] ?? false;
                            final isSystem = msg['content'].toString().startsWith('[SYSTEME]') ||
                                             msg['content'].toString().startsWith('[PARTENAIRE]');

                            if (isSystem) {
                              return Center(
                                child: Container(
                                  margin: const EdgeInsets.symmetric(vertical: 8),
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: Colors.yellow.shade100,
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: Colors.yellow.shade200),
                                  ),
                                  child: Text(
                                    msg['content'],
                                    style: TextStyle(color: Colors.grey.shade800, fontSize: 12),
                                    textAlign: TextAlign.center,
                                  ),
                                ),
                              );
                            }

                            return Align(
                              alignment: isSelf ? Alignment.centerRight : Alignment.centerLeft,
                              child: Container(
                                margin: const EdgeInsets.symmetric(vertical: 4),
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                                decoration: BoxDecoration(
                                  color: isSelf ? const Color(0xFFDCF8C6) : Colors.white,
                                  borderRadius: BorderRadius.only(
                                    topLeft: const Radius.circular(12),
                                    topRight: const Radius.circular(12),
                                    bottomLeft: isSelf ? const Radius.circular(12) : Radius.zero,
                                    bottomRight: isSelf ? Radius.zero : const Radius.circular(12),
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withValues(alpha: 0.05),
                                      blurRadius: 2,
                                      offset: const Offset(0, 1),
                                    ),
                                  ],
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      msg['content'],
                                      style: const TextStyle(fontSize: 15, color: Colors.black87),
                                    ),
                                    const SizedBox(height: 4),
                                    Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        const Spacer(),
                                        Text(
                                          msg['created_at'] ?? '',
                                          style: TextStyle(fontSize: 10, color: Colors.grey.shade500),
                                        ),
                                      ],
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
                        child: SafeArea(
                          child: Row(
                            children: [
                              IconButton(
                                icon: const Icon(Icons.flash_on, color: Color(0xFF0F4F2C)),
                                onPressed: _showTemplatesSelector,
                                tooltip: 'Modèles',
                              ),
                              IconButton(
                                icon: const Icon(Icons.maps_home_work_outlined, color: Color(0xFF0F4F2C)),
                                onPressed: _showCatalogueShare,
                                tooltip: 'Catalogue',
                              ),
                              Expanded(
                                child: TextField(
                                  controller: _messageController,
                                  maxLines: null,
                                  decoration: InputDecoration(
                                    hintText: 'Message...',
                                    border: OutlineInputBorder(
                                      borderRadius: BorderRadius.circular(24),
                                      borderSide: BorderSide.none,
                                    ),
                                    fillColor: Colors.grey.shade100,
                                    filled: true,
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 4),
                              CircleAvatar(
                                radius: 22,
                                backgroundColor: const Color(0xFF0F4F2C),
                                child: IconButton(
                                  icon: const Icon(Icons.send, color: Colors.white, size: 18),
                                  onPressed: _sendMessage,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}

class CatalogueScreen extends StatefulWidget {
  const CatalogueScreen({super.key});

  @override
  State<CatalogueScreen> createState() => _CatalogueScreenState();
}

class _CatalogueScreenState extends State<CatalogueScreen> {
  List<dynamic> _properties = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProperties();
  }

  Future<void> _loadProperties() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/mobile/properties/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          setState(() {
            _properties = data['properties'];
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Catalogue Immobilier', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: 0.75,
              ),
              itemCount: _properties.length,
              itemBuilder: (context, index) {
                final prop = _properties[index];
                return Card(
                  elevation: 2,
                  color: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: ClipRRect(
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                          child: Image.network(
                            prop['image_url'],
                            width: double.infinity,
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) =>
                                const Icon(Icons.image, size: 50, color: Colors.grey),
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              prop['title'],
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${prop['price']} FCFA',
                              style: const TextStyle(color: Color(0xFF0F4F2C), fontWeight: FontWeight.bold, fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }
}

class CatalogueSelectionSheet extends StatefulWidget {
  const CatalogueSelectionSheet({super.key});

  @override
  State<CatalogueSelectionSheet> createState() => _CatalogueSelectionSheetState();
}

class _CatalogueSelectionSheetState extends State<CatalogueSelectionSheet> {
  List<dynamic> _properties = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProperties();
  }

  Future<void> _loadProperties() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/mobile/properties/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          setState(() {
            _properties = data['properties'];
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      height: MediaQuery.of(context).size.height * 0.7,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Sélectionner une Propriété', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
            ],
          ),
          const Divider(),
          _isLoading
              ? const Expanded(child: Center(child: CircularProgressIndicator()))
              : Expanded(
                  child: ListView.builder(
                    itemCount: _properties.length,
                    itemBuilder: (context, index) {
                      final prop = _properties[index];
                      return ListTile(
                        leading: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(prop['image_url'], width: 50, height: 50, fit: BoxFit.cover),
                        ),
                        title: Text(prop['title']),
                        subtitle: Text('${prop['price']} FCFA'),
                        trailing: ElevatedButton(
                          onPressed: () {
                            Navigator.pop(context, 'Je vous propose ce bien immobilier : ${prop['title']} - ${prop['url']}');
                          },
                          child: const Text('Partager'),
                        ),
                      );
                    },
                  ),
                ),
        ],
      ),
    );
  }
}

class PartnersScreen extends StatefulWidget {
  const PartnersScreen({super.key});

  @override
  State<PartnersScreen> createState() => _PartnersScreenState();
}

class _PartnersScreenState extends State<PartnersScreen> {
  List<dynamic> _partners = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPartners();
  }

  Future<void> _loadPartners() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/mobile/partners/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          setState(() {
            _partners = data['partners'];
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Partenaires', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _partners.length,
              itemBuilder: (context, index) {
                final p = _partners[index];
                return Card(
                  color: Colors.white,
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: Colors.grey.shade200),
                  ),
                  child: ListTile(
                    title: Text(p['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('Zone : ${p['zone']} | Type : ${p['property_type']}'),
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: _getMeteoColor(p['meteo']).withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        p['meteo_display'] ?? '',
                        style: TextStyle(color: _getMeteoColor(p['meteo']), fontWeight: FontWeight.bold, fontSize: 11),
                      ),
                    ),
                  ),
                );
              },
            ),
    );
  }

  Color _getMeteoColor(String? meteo) {
    switch (meteo?.toLowerCase()) {
      case 'soleil':
        return Colors.green;
      case 'nuageux':
        return Colors.orange;
      case 'pluie':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}

class PartnersSelectionSheet extends StatefulWidget {
  final String conversationId;
  const PartnersSelectionSheet({super.key, required this.conversationId});

  @override
  State<PartnersSelectionSheet> createState() => _PartnersSelectionSheetState();
}

class _PartnersSelectionSheetState extends State<PartnersSelectionSheet> {
  List<dynamic> _partners = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPartners();
  }

  Future<void> _loadPartners() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/mobile/partners/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          setState(() {
            _partners = data['partners'];
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _createMatch(Map<String, dynamic> partner) async {
    final visitorNameController = TextEditingController();
    final visitorPhoneController = TextEditingController();
    final priceController = TextEditingController();
    final zoneController = TextEditingController(text: partner['zone']);

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: Colors.white,
          title: Text('Match avec ${partner['name']}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: visitorNameController, decoration: const InputDecoration(labelText: 'Nom du Visiteur')),
                TextField(controller: visitorPhoneController, decoration: const InputDecoration(labelText: 'Téléphone du Visiteur')),
                TextField(controller: priceController, decoration: const InputDecoration(labelText: 'Prix proposé (FCFA)')),
                TextField(controller: zoneController, decoration: const InputDecoration(labelText: 'Zone de visite')),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
            ElevatedButton(
              onPressed: () async {
                final visitorName = visitorNameController.text;
                final visitorPhone = visitorPhoneController.text;
                final price = priceController.text;
                final zone = zoneController.text;

                if (visitorName.isEmpty || visitorPhone.isEmpty || price.isEmpty || zone.isEmpty) {
                  return;
                }

                Navigator.pop(context); // Close dialog

                final prefs = await SharedPreferences.getInstance();
                final token = prefs.getString('token');
                final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

                if (token == null) return;

                try {
                  final response = await http.post(
                    Uri.parse('$serverUrl/api/mobile/partners/match/'),
                    headers: {
                      'Authorization': 'Token $token',
                      'Content-Type': 'application/json',
                    },
                    body: jsonEncode({
                      'conversation_id': widget.conversationId,
                      'partner_id': partner['id'],
                      'visitor_name': visitorName,
                      'visitor_phone': visitorPhone,
                      'price': double.parse(price),
                      'zone': zone,
                    }),
                  );

                  if (response.statusCode == 200) {
                    final res = jsonDecode(response.body);
                    final waLink = res['wa_link'];
                    if (waLink != null) {
                      await launchUrl(Uri.parse(waLink), mode: LaunchMode.externalApplication);
                    }
                    if (mounted) {
                      Navigator.pop(context); // Close BottomSheet
                    }
                  }
                } catch (e) {
                  // Error
                }
              },
              child: const Text('Créer le Match'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      height: MediaQuery.of(context).size.height * 0.7,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Associer un Partenaire', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
            ],
          ),
          const Divider(),
          _isLoading
              ? const Expanded(child: Center(child: CircularProgressIndicator()))
              : Expanded(
                  child: ListView.builder(
                    itemCount: _partners.length,
                    itemBuilder: (context, index) {
                      final p = _partners[index];
                      return ListTile(
                        title: Text(p['name']),
                        subtitle: Text('Zone : ${p['zone']}'),
                        trailing: ElevatedButton(
                          onPressed: () => _createMatch(p),
                          child: const Text('Associer'),
                        ),
                      );
                    },
                  ),
                ),
        ],
      ),
    );
  }
}

class VisitesScreen extends StatefulWidget {
  const VisitesScreen({super.key});

  @override
  State<VisitesScreen> createState() => _VisitesScreenState();
}

class _VisitesScreenState extends State<VisitesScreen> {
  List<dynamic> _visits = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadVisits();
  }

  Future<void> _loadVisits() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/visits/list/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _visits = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _updateVisitStatus(String visitId, String status) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final serverUrl = prefs.getString('server_url') ?? 'https://chat.logersenegal.com';

    if (token == null) return;

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/visits/update/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'visit_id': visitId,
          'status': status,
        }),
      );

      if (response.statusCode == 200) {
        _loadVisits();
      }
    } catch (e) {
      // Error
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Visites Planifiées', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _visits.length,
              itemBuilder: (context, index) {
                final v = _visits[index];
                final isPending = v['status'] == 'PENDING';

                return Card(
                  color: Colors.white,
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: Colors.grey.shade200),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              v['property_title'] ?? 'Bien inconnu',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                            _buildStatusBadge(v['status']),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text('Client : ${v['client_name']}'),
                        Text('Date : ${v['visit_date']}'),
                        if (isPending) ...[
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton(
                                  onPressed: () => _updateVisitStatus(v['id'].toString(), 'CANCELLED'),
                                  style: OutlinedButton.styleFrom(
                                    foregroundColor: Colors.red,
                                    side: const BorderSide(color: Colors.red),
                                  ),
                                  child: const Text('Annuler'),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: ElevatedButton(
                                  onPressed: () => _updateVisitStatus(v['id'].toString(), 'DONE'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: const Color(0xFF0F4F2C),
                                    foregroundColor: Colors.white,
                                  ),
                                  child: const Text('Valider'),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color color = Colors.grey;
    String label = status;

    if (status == 'PENDING') {
      color = Colors.orange;
      label = 'En Attente';
    } else if (status == 'DONE') {
      color = Colors.green;
      label = 'Faite';
    } else if (status == 'CANCELLED') {
      color = Colors.red;
      label = 'Annulée';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(6)),
      child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
    );
  }
}

class ProfilScreen extends StatefulWidget {
  const ProfilScreen({super.key});

  @override
  State<ProfilScreen> createState() => _ProfilScreenState();
}

class _ProfilScreenState extends State<ProfilScreen> {
  String _fullName = 'Agent';
  String _role = 'AGENT';
  String _username = '';

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _fullName = prefs.getString('full_name') ?? 'Agent';
      _role = prefs.getString('role') ?? 'AGENT';
      _username = prefs.getString('username') ?? '';
    });
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
        title: const Text('Mon Profil', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const CircleAvatar(
              radius: 50,
              backgroundColor: Color(0xFF0F4F2C),
              child: Icon(Icons.person, size: 60, color: Colors.white),
            ),
            const SizedBox(height: 20),
            Text(_fullName, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            Text('@$_username', style: const TextStyle(fontSize: 16, color: Colors.grey)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(color: const Color(0xFFE1EFE7), borderRadius: BorderRadius.circular(12)),
              child: Text(
                _role,
                style: const TextStyle(color: Color(0xFF0F4F2C), fontWeight: FontWeight.bold),
              ),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: _logout,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 50),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('Se Déconnecter', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }
}
