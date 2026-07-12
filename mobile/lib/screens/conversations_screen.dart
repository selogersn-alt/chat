import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import 'chat_detail_screen.dart';

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
    try {
      final data = await ApiService.get('/api/mobile/conversations/');
      if (data['status'] == 'success') {
        setState(() {
          _allConversations = data['conversations'];
          _isLoading = false;
        });
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
        title: const Text(
          'Loger Sénégal',
          style: TextStyle(fontWeight: FontWeight.w800, color: Colors.white, fontSize: 22),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search, color: Colors.white),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.more_vert, color: Colors.white),
            onPressed: () {},
          ),
        ],
        backgroundColor: AppColors.primary,
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: Colors.white,
          indicatorWeight: 3,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold),
          tabs: const [
            Tab(text: 'ACTIVES'),
            Tab(text: 'EN ATTENTE'),
            Tab(text: 'FERMÉES'),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary)))
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
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppColors.primary,
        onPressed: _loadConversations,
        child: const Icon(Icons.refresh, color: Colors.white),
      ),
    );
  }

  Widget _buildConversationList(String status) {
    final list = _filterConversations(status);

    if (list.isEmpty) {
      return Center(
        child: Text(
          'Aucune discussion $status.',
          style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
        ),
      );
    }

    return ListView.separated(
      padding: EdgeInsets.zero,
      itemCount: list.length,
      separatorBuilder: (context, index) => const Divider(height: 1, indent: 80),
      itemBuilder: (context, index) {
        final c = list[index];
        final unreadCount = c['unread_count'] ?? 0;
        final isWhatsApp = c['is_whatsapp'] ?? false;

        return ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          leading: CircleAvatar(
            radius: 26,
            backgroundColor: isWhatsApp ? const Color(0xFF25D366) : const Color(0xFFE1EFE7),
            child: isWhatsApp
                ? const Icon(Icons.phone_iphone, color: Colors.white, size: 24)
                : const Icon(Icons.person, color: AppColors.primary, size: 26),
          ),
          title: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  c['client_name'] ?? 'Client',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.black87),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Text(
                c['last_message_time'] ?? '',
                style: TextStyle(
                  color: unreadCount > 0 ? AppColors.primary : Colors.grey.shade600,
                  fontSize: 12,
                  fontWeight: unreadCount > 0 ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          ),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 4.0),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    c['last_message'] ?? 'Aucun message.',
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (c['pipeline_stage_display'] != null && unreadCount == 0)
                  _buildBadge(c['pipeline_stage_display'], _getPipelineColor(c['pipeline_stage'])),
                if (unreadCount > 0)
                  Container(
                    margin: const EdgeInsets.only(left: 8),
                    padding: const EdgeInsets.all(6),
                    decoration: const BoxDecoration(
                      color: AppColors.primary,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      unreadCount.toString(),
                      style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ),
              ],
            ),
          ),
          onTap: () async {
            await Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => ChatDetailScreen(conversationId: c['id'].toString()),
              ),
            );
            _loadConversations();
          },
        );
      },
    );
  }

  Widget _buildBadge(String label, Color color) {
    return Container(
      margin: const EdgeInsets.only(left: 8),
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold),
      ),
    );
  }

  Color _getPipelineColor(String? stage) {
    switch (stage?.toLowerCase()) {
      case 'new': return Colors.blue;
      case 'qualification': return Colors.orange;
      case 'proposition': return Colors.teal;
      case 'visit_scheduled': return Colors.indigo;
      case 'visit_done': return Colors.purple;
      case 'negociation': return Colors.amber.shade900;
      case 'won': return AppColors.primary;
      case 'lost': return Colors.red;
      default: return Colors.grey;
    }
  }
}
