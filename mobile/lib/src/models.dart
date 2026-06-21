import 'dart:ui' show Color;

import 'package:intl/intl.dart';

/// Money is integer cents everywhere (matching the backend). Negative = outflow/spending.
final _currency = NumberFormat.simpleCurrency(locale: 'en_US');

String formatCents(int cents) => _currency.format(cents / 100.0);

String formatDateIso(String iso) {
  try {
    final d = DateTime.parse(iso.length <= 10 ? '${iso}T00:00:00' : iso);
    return DateFormat.yMMMd().format(d);
  } catch (_) {
    return iso;
  }
}

/// Internal category taxonomy (mirrors backend `Category`).
enum Category {
  income,
  transfer,
  foodDining,
  groceries,
  shopping,
  transport,
  travel,
  billsUtilities,
  rentMortgage,
  healthcare,
  entertainment,
  personalCare,
  education,
  feesCharges,
  loanPayment,
  taxesGov,
  giftsDonations,
  businessServices,
  uncategorized,
}

const _categoryWire = {
  Category.income: 'INCOME',
  Category.transfer: 'TRANSFER',
  Category.foodDining: 'FOOD_DINING',
  Category.groceries: 'GROCERIES',
  Category.shopping: 'SHOPPING',
  Category.transport: 'TRANSPORT',
  Category.travel: 'TRAVEL',
  Category.billsUtilities: 'BILLS_UTILITIES',
  Category.rentMortgage: 'RENT_MORTGAGE',
  Category.healthcare: 'HEALTHCARE',
  Category.entertainment: 'ENTERTAINMENT',
  Category.personalCare: 'PERSONAL_CARE',
  Category.education: 'EDUCATION',
  Category.feesCharges: 'FEES_CHARGES',
  Category.loanPayment: 'LOAN_PAYMENT',
  Category.taxesGov: 'TAXES_GOV',
  Category.giftsDonations: 'GIFTS_DONATIONS',
  Category.businessServices: 'BUSINESS_SERVICES',
  Category.uncategorized: 'UNCATEGORIZED',
};

final _wireToCategory = {for (final e in _categoryWire.entries) e.value: e.key};

String categoryWire(Category c) => _categoryWire[c]!;

Category categoryFromWire(String? wire) =>
    _wireToCategory[wire] ?? Category.uncategorized;

const _categoryLabels = {
  'INCOME': 'Income',
  'TRANSFER': 'Transfer',
  'FOOD_DINING': 'Food & Dining',
  'GROCERIES': 'Groceries',
  'SHOPPING': 'Shopping',
  'TRANSPORT': 'Transport',
  'TRAVEL': 'Travel',
  'BILLS_UTILITIES': 'Bills & Utilities',
  'RENT_MORTGAGE': 'Rent / Mortgage',
  'HEALTHCARE': 'Healthcare',
  'ENTERTAINMENT': 'Entertainment',
  'PERSONAL_CARE': 'Personal Care',
  'EDUCATION': 'Education',
  'FEES_CHARGES': 'Fees & Charges',
  'LOAN_PAYMENT': 'Loan Payment',
  'TAXES_GOV': 'Taxes & Government',
  'GIFTS_DONATIONS': 'Gifts & Donations',
  'BUSINESS_SERVICES': 'Business Services',
  'UNCATEGORIZED': 'Uncategorized',
};

String categoryLabel(Category c) => _categoryLabels[categoryWire(c)] ?? categoryWire(c);

const _categoryColors = {
  'INCOME': Color(0xFF16A34A),
  'TRANSFER': Color(0xFF64748B),
  'FOOD_DINING': Color(0xFFF97316),
  'GROCERIES': Color(0xFF84CC16),
  'SHOPPING': Color(0xFFEC4899),
  'TRANSPORT': Color(0xFF0EA5E9),
  'TRAVEL': Color(0xFF6366F1),
  'BILLS_UTILITIES': Color(0xFFEAB308),
  'RENT_MORTGAGE': Color(0xFFEF4444),
  'HEALTHCARE': Color(0xFF14B8A6),
  'ENTERTAINMENT': Color(0xFFA855F7),
  'PERSONAL_CARE': Color(0xFFF43F5E),
  'EDUCATION': Color(0xFF3B82F6),
  'FEES_CHARGES': Color(0xFF9CA3AF),
  'LOAN_PAYMENT': Color(0xFFDC2626),
  'TAXES_GOV': Color(0xFF78716C),
  'GIFTS_DONATIONS': Color(0xFFD946EF),
  'BUSINESS_SERVICES': Color(0xFF0891B2),
  'UNCATEGORIZED': Color(0xFFCBD5E1),
};

Color categoryColor(Category c) => _categoryColors[categoryWire(c)] ?? const Color(0xFFCBD5E1);

const budgetableCategories = <Category>[
  Category.foodDining,
  Category.groceries,
  Category.shopping,
  Category.transport,
  Category.travel,
  Category.billsUtilities,
  Category.rentMortgage,
  Category.healthcare,
  Category.entertainment,
  Category.personalCare,
  Category.education,
  Category.feesCharges,
  Category.loanPayment,
  Category.taxesGov,
  Category.giftsDonations,
  Category.businessServices,
];

class Account {
  final String id;
  final String name;
  final String type;
  final String? mask;
  final int balanceCents;
  final bool isLiability;

  Account.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        name = (j['name'] ?? '') as String,
        type = (j['type'] ?? '') as String,
        mask = j['mask'] as String?,
        balanceCents = (j['balance_cents'] ?? 0) as int,
        isLiability = (j['is_liability'] ?? false) as bool;
}

class Transaction {
  final String id;
  final String accountId;
  final int amountCents;
  final String date;
  final String merchant;
  final String rawName;
  final Category category;
  final String source;
  final bool pending;
  final String? possibleDuplicateOf;

  Transaction.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        accountId = (j['account_id'] ?? '') as String,
        amountCents = (j['amount_cents'] ?? 0) as int,
        date = (j['date'] ?? '') as String,
        merchant = (j['merchant'] ?? '') as String,
        rawName = (j['raw_name'] ?? '') as String,
        category = categoryFromWire(j['category'] as String?),
        source = (j['source'] ?? 'plaid') as String,
        pending = (j['pending'] ?? false) as bool,
        possibleDuplicateOf = j['possible_duplicate_of'] as String?;

  String get title => merchant.isNotEmpty ? merchant : (rawName.isNotEmpty ? rawName : '—');
}

class Budget {
  final String month;
  final Map<String, int> capsCents;
  final Map<String, int> spentCents;

  Budget.fromJson(Map<String, dynamic> j)
      : month = j['month'] as String,
        capsCents = _intMap(j['caps_cents']),
        spentCents = _intMap(j['spent_cents']);

  static Map<String, int> _intMap(dynamic v) {
    final m = (v as Map?) ?? {};
    return m.map((k, val) => MapEntry(k as String, (val as num).toInt()));
  }
}

class Alert {
  final String id;
  final String type;
  final String severity;
  final String title;
  final String message;
  final bool read;
  final String createdAt;

  Alert.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        type = (j['type'] ?? '') as String,
        severity = (j['severity'] ?? 'info') as String,
        title = (j['title'] ?? '') as String,
        message = (j['message'] ?? '') as String,
        read = (j['read'] ?? false) as bool,
        createdAt = (j['created_at'] ?? '') as String;
}

class RecurringStream {
  final String id;
  final String merchant;
  final String frequency;
  final String flow; // inflow | outflow
  final int averageAmountCents;
  final Category category;
  final bool isActive;
  final String? lastDate;

  RecurringStream.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        merchant = (j['merchant'] ?? '') as String,
        frequency = (j['frequency'] ?? 'UNKNOWN') as String,
        flow = (j['flow'] ?? 'outflow') as String,
        averageAmountCents = (j['average_amount_cents'] ?? 0) as int,
        category = categoryFromWire(j['category'] as String?),
        isActive = (j['is_active'] ?? true) as bool,
        lastDate = j['last_date'] as String?;
}

class UpcomingCashFlow {
  final String date;
  final String merchant;
  final int amountCents;
  final String flow;

  UpcomingCashFlow.fromJson(Map<String, dynamic> j)
      : date = (j['date'] ?? '') as String,
        merchant = (j['merchant'] ?? '') as String,
        amountCents = (j['amount_cents'] ?? 0) as int,
        flow = (j['flow'] ?? 'outflow') as String;
}

class CashFlowForecast {
  final int horizonDays;
  final int currentBalanceCents;
  final int projectedInflowCents;
  final int projectedOutflowCents;
  final int netCents;
  final int projectedEndBalanceCents;
  final List<UpcomingCashFlow> upcoming;

  CashFlowForecast.fromJson(Map<String, dynamic> j)
      : horizonDays = (j['horizon_days'] ?? 0) as int,
        currentBalanceCents = (j['current_balance_cents'] ?? 0) as int,
        projectedInflowCents = (j['projected_inflow_cents'] ?? 0) as int,
        projectedOutflowCents = (j['projected_outflow_cents'] ?? 0) as int,
        netCents = (j['net_cents'] ?? 0) as int,
        projectedEndBalanceCents = (j['projected_end_balance_cents'] ?? 0) as int,
        upcoming = ((j['upcoming'] ?? []) as List)
            .map((e) => UpcomingCashFlow.fromJson(e as Map<String, dynamic>))
            .toList();
}

class PlaidItem {
  final String id;
  final String institutionName;
  final String status;
  final String? lastSyncAt;

  PlaidItem.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        institutionName = (j['institution_name'] ?? '') as String,
        status = (j['status'] ?? 'active') as String,
        lastSyncAt = j['last_sync_at'] as String?;
}
