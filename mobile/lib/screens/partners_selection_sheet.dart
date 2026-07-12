import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';

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
    try {
      final data = await ApiService.get('/api/mobile/partners/');
      if (data['status'] == 'success') {
        setState(() {
          _partners = data['partners'];
          _isLoading = false;
        });
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

                if (visitorName.isEmpty || visitorPhone.isEmpty || price.isEmpty || zone.isEmpty) return;

                Navigator.pop(context); // Close dialog

                try {
                  final response = await ApiService.post('/api/mobile/partners/match/', {
                    'conversation_id': widget.conversationId,
                    'partner_id': partner['id'],
                    'visitor_name': visitorName,
                    'visitor_phone': visitorPhone,
                    'price': double.parse(price),
                    'zone': zone,
                  });

                  final waLink = response['wa_link'];
                  if (waLink != null) {
                    await launchUrl(Uri.parse(waLink), mode: LaunchMode.externalApplication);
                  }
                  if (mounted) Navigator.pop(context);
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
