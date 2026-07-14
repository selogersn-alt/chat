import 'package:flutter/material.dart';
import '../services/api_service.dart';

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
    try {
      final data = await ApiService.get('/api/visits/list/');
      setState(() {
        _visits = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _updateVisitStatus(String visitId, String status) async {
    try {
      await ApiService.post('/api/visits/update/', {
        'visit_id': visitId,
        'status': status,
      });
      _loadVisits();
    } catch (e) {
      // Error handling
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
                final isPlanned = v['status'] == 'PLANNED';

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
                        if (isPlanned) ...[
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton(
                                  onPressed: () => _updateVisitStatus(v['id'].toString(), 'CANCELED'),
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
                                  onPressed: () => _updateVisitStatus(v['id'].toString(), 'COMPLETED'),
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

    if (status == 'PLANNED') {
      color = Colors.orange;
      label = 'Planifiée';
    } else if (status == 'COMPLETED') {
      color = Colors.green;
      label = 'Effectuée';
    } else if (status == 'CANCELED') {
      color = Colors.red;
      label = 'Annulée';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(6)),
      child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
    );
  }
}
