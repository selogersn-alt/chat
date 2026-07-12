import 'package:flutter/material.dart';
import '../services/api_service.dart';

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
                        color: _getMeteoColor(p['meteo']).withOpacity(0.1),
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
