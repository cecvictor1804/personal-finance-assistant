import 'dart:io';

import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../services/api.dart';
import '../services/auth_service.dart';

class AddTransactionScreen extends StatefulWidget {
  const AddTransactionScreen({super.key});

  @override
  State<AddTransactionScreen> createState() => _AddTransactionScreenState();
}

class _AddTransactionScreenState extends State<AddTransactionScreen> {
  final _merchant = TextEditingController();
  final _amount = TextEditingController();
  final _account = TextEditingController(text: 'cash');
  DateTime _date = DateTime.now();
  bool _expense = true;
  Category? _category; // null = auto-categorize
  XFile? _receipt;
  bool _saving = false;

  @override
  void dispose() {
    _merchant.dispose();
    _amount.dispose();
    _account.dispose();
    super.dispose();
  }

  Future<void> _pickReceipt() async {
    final file = await ImagePicker().pickImage(source: ImageSource.camera, imageQuality: 70);
    if (file != null) setState(() => _receipt = file);
  }

  Future<void> _save() async {
    final value = double.tryParse(_amount.text.trim());
    if (value == null || value <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Enter a valid amount')));
      return;
    }
    setState(() => _saving = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final cents = (value * 100).round();
      await context.read<Api>().createManualTransaction(
            accountId: _account.text.trim().isEmpty ? 'cash' : _account.text.trim(),
            amountCents: _expense ? -cents : cents,
            date: DateFormat('yyyy-MM-dd').format(_date),
            merchant: _merchant.text.trim(),
            category: _category,
          );
      // Receipt upload (OCR + matching happens in Phase 6 via a Storage trigger).
      if (_receipt != null) {
        final uid = context.read<AuthService>().uid;
        if (uid != null) {
          final ref = FirebaseStorage.instance
              .ref('receipts/$uid/${DateTime.now().millisecondsSinceEpoch}.jpg');
          await ref.putFile(File(_receipt!.path));
        }
      }
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Failed: $e')));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add transaction')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _merchant,
            decoration: const InputDecoration(labelText: 'Merchant'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _amount,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Amount', prefixText: '\$ '),
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: SegmentedButton<bool>(
                segments: const [
                  ButtonSegment(value: true, label: Text('Expense')),
                  ButtonSegment(value: false, label: Text('Income')),
                ],
                selected: {_expense},
                onSelectionChanged: (s) => setState(() => _expense = s.first),
              ),
            ),
          ]),
          const SizedBox(height: 12),
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Date'),
            trailing: Text(DateFormat.yMMMd().format(_date)),
            onTap: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: _date,
                firstDate: DateTime(2015),
                lastDate: DateTime.now(),
              );
              if (picked != null) setState(() => _date = picked);
            },
          ),
          DropdownButtonFormField<Category?>(
            value: _category,
            decoration: const InputDecoration(labelText: 'Category'),
            items: [
              const DropdownMenuItem<Category?>(value: null, child: Text('Auto-categorize')),
              ...Category.values.map(
                (c) => DropdownMenuItem<Category?>(value: c, child: Text(categoryLabel(c))),
              ),
            ],
            onChanged: (c) => setState(() => _category = c),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: _pickReceipt,
            icon: const Icon(Icons.camera_alt_outlined),
            label: Text(_receipt == null ? 'Attach receipt' : 'Receipt attached'),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Save'),
          ),
        ],
      ),
    );
  }
}
