import 'package:flutter/material.dart';
import '../services/api_service.dart';

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
    try {
      final data = await ApiService.get('/api/mobile/properties/');
      if (data['status'] == 'success') {
        setState(() {
          _properties = data['properties'];
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
