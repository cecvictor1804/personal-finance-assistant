import 'dart:ui' show FontFeature;

import 'package:flutter/material.dart';

import 'models.dart';

class MoneyText extends StatelessWidget {
  const MoneyText(this.cents, {super.key, this.colorize = false, this.style});
  final int cents;
  final bool colorize;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    Color? color;
    if (colorize) {
      color = cents < 0
          ? const Color(0xFFDC2626)
          : cents > 0
              ? const Color(0xFF16A34A)
              : null;
    }
    return Text(
      formatCents(cents),
      style: (style ?? const TextStyle()).copyWith(
        color: color,
        fontFeatures: const [FontFeature.tabularFigures()],
      ),
    );
  }
}

class CategoryChip extends StatelessWidget {
  const CategoryChip(this.category, {super.key});
  final Category category;

  @override
  Widget build(BuildContext context) {
    final color = categoryColor(category);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 6),
          Text(categoryLabel(category), style: TextStyle(fontSize: 12, color: color)),
        ],
      ),
    );
  }
}

/// Renders a Future of data with loading / error / success states and pull-to-refresh.
class AsyncView<T> extends StatelessWidget {
  const AsyncView({super.key, required this.future, required this.builder, this.onRefresh});
  final Future<T> future;
  final Widget Function(T data) builder;
  final Future<void> Function()? onRefresh;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<T>(
      future: future,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator()));
        }
        if (snap.hasError) {
          return _ErrorState(message: '${snap.error}', onRefresh: onRefresh);
        }
        final content = builder(snap.data as T);
        if (onRefresh == null) return content;
        return RefreshIndicator(onRefresh: onRefresh!, child: content);
      },
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, this.onRefresh});
  final String message;
  final Future<void> Function()? onRefresh;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, color: Colors.grey),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey)),
            if (onRefresh != null) ...[
              const SizedBox(height: 12),
              FilledButton.tonal(onPressed: onRefresh, child: const Text('Retry')),
            ],
          ],
        ),
      ),
    );
  }
}
