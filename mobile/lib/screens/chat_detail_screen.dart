import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/chat_bubble.dart';
import 'catalogue_selection_sheet.dart';
import 'partners_selection_sheet.dart';

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
    try {
      final data = await ApiService.get('/api/mobile/conversations/${widget.conversationId}/messages/');
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

    try {
      await ApiService.post('/api/send/', {
        'conversation_id': widget.conversationId,
        'content': content,
      });
      _loadMessages();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Erreur lors de l\'envoi du message.')),
        );
      }
    }
  }

  void _showTemplatesSelector() {
    final templates = [
      "Bonjour, j'espère que vous allez bien. Je vous contacte de la part de Loger Sénégal.",
      "Voici les propriétés correspondant à votre recherche. N'hésitez pas à me donner votre avis.",
      "Nous pouvons programmer une visite de bien immobilier. Quel jour vous conviendrait ?",
      "Votre visite a été planifiée avec succès. Notre agent sera présent sur place.",
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
        backgroundColor: AppColors.primary,
        iconTheme: const IconThemeData(color: Colors.white),
        title: Row(
          children: [
            const CircleAvatar(
              backgroundColor: Colors.white24,
              child: Icon(Icons.person, color: Colors.white),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(clientName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white)),
                  Text(clientPhone, style: const TextStyle(fontSize: 12, color: Colors.white70)),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.maps_home_work_outlined),
            onPressed: () {
              showModalBottomSheet(
                context: context,
                isScrollControlled: true,
                backgroundColor: Colors.white,
                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
                builder: (context) => const CatalogueSelectionSheet(),
              ).then((result) {
                if (result != null && result is String) {
                  setState(() {
                    _messageController.text = result;
                  });
                }
              });
            },
            tooltip: 'Catalogue',
          ),
          IconButton(
            icon: const Icon(Icons.people_outline),
            onPressed: () {
              showModalBottomSheet(
                context: context,
                isScrollControlled: true,
                backgroundColor: Colors.white,
                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
                builder: (context) => PartnersSelectionSheet(conversationId: widget.conversationId),
              );
            },
            tooltip: 'Associer Partenaire',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary)))
          : _errorMessage != null
              ? Center(child: Text(_errorMessage!))
              : Container(
                  color: AppColors.background,
                  child: Column(
                    children: [
                      Expanded(
                        child: ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.all(16),
                          itemCount: _messages.length,
                          itemBuilder: (context, index) {
                            return ChatBubble(message: _messages[index]);
                          },
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.all(8.0),
                        color: Colors.transparent,
                        child: SafeArea(
                          child: Row(
                            children: [
                              IconButton(
                                icon: const Icon(Icons.add, color: AppColors.primary, size: 28),
                                onPressed: _showTemplatesSelector,
                              ),
                              Expanded(
                                child: Container(
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(24),
                                    boxShadow: [
                                      BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, 2)),
                                    ],
                                  ),
                                  child: TextField(
                                    controller: _messageController,
                                    maxLines: 5,
                                    minLines: 1,
                                    decoration: const InputDecoration(
                                      hintText: 'Message',
                                      border: InputBorder.none,
                                      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              CircleAvatar(
                                radius: 24,
                                backgroundColor: AppColors.primary,
                                child: IconButton(
                                  icon: const Icon(Icons.send, color: Colors.white, size: 20),
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
