import 'package:flutter/material.dart';
import '../utils/constants.dart';

class ChatBubble extends StatelessWidget {
  final Map<String, dynamic> message;
  
  const ChatBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isSelf = message['sender_is_self'] ?? false;
    final isSystem = message['content'].toString().startsWith('[SYSTEME]') ||
                     message['content'].toString().startsWith('[PARTENAIRE]');

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
            message['content'],
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
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isSelf ? AppColors.bubbleSelf : AppColors.bubbleOther,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(12),
            topRight: const Radius.circular(12),
            bottomLeft: isSelf ? const Radius.circular(12) : Radius.zero,
            bottomRight: isSelf ? Radius.zero : const Radius.circular(12),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 1,
              offset: const Offset(0, 1),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message['content'],
              style: const TextStyle(fontSize: 15, color: Colors.black87),
            ),
            const SizedBox(height: 2),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Spacer(),
                Text(
                  message['created_at'] ?? '',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
                if (isSelf) ...[
                  const SizedBox(width: 4),
                  Icon(Icons.done_all, size: 14, color: Colors.blue.shade400),
                ]
              ],
            ),
          ],
        ),
      ),
    );
  }
}
