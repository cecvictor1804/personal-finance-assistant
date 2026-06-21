import '../models.dart';
import 'api_client.dart';

/// Typed wrapper over [ApiClient] mapping endpoints to domain models. Mirrors the web API client.
class Api {
  Api(this._c);
  final ApiClient _c;

  Future<List<Transaction>> listTransactions({int limit = 100, String? category}) async {
    final q = StringBuffer('/transactions?limit=$limit');
    if (category != null && category.isNotEmpty) q.write('&category=$category');
    final data = await _c.get(q.toString()) as List;
    return data.map((e) => Transaction.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Transaction> createManualTransaction({
    required String accountId,
    required int amountCents,
    required String date,
    String merchant = '',
    Category? category,
    String notes = '',
  }) async {
    final body = {
      'account_id': accountId,
      'amount_cents': amountCents,
      'date': date,
      'merchant': merchant,
      'notes': notes,
      if (category != null) 'category': categoryWire(category),
    };
    return Transaction.fromJson(await _c.post('/transactions', body) as Map<String, dynamic>);
  }

  Future<Transaction> recategorize(String id, Category category, {bool remember = true}) async {
    final body = {'category': categoryWire(category), 'remember': remember};
    return Transaction.fromJson(
      await _c.post('/transactions/$id/recategorize', body) as Map<String, dynamic>,
    );
  }

  Future<List<Account>> listAccounts() async {
    final data = await _c.get('/accounts') as List;
    return data.map((e) => Account.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<PlaidItem>> listItems() async {
    final data = await _c.get('/items') as List;
    return data.map((e) => PlaidItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> syncNow() => _c.post('/items/sync');

  Future<String> reauthLinkToken(String itemId) async {
    final data = await _c.post('/items/$itemId/reauth-link-token') as Map<String, dynamic>;
    return data['link_token'] as String;
  }

  Future<Budget> getBudget(String month) async =>
      Budget.fromJson(await _c.get('/budgets/$month') as Map<String, dynamic>);

  Future<Budget> setBudgetCaps(String month, Map<String, int> capsCents) async => Budget.fromJson(
        await _c.put('/budgets/$month', {'caps_cents': capsCents}) as Map<String, dynamic>,
      );

  Future<List<Alert>> listAlerts({bool unreadOnly = false}) async {
    final data = await _c.get('/alerts${unreadOnly ? '?unread_only=true' : ''}') as List;
    return data.map((e) => Alert.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> markAlertRead(String id) => _c.post('/alerts/$id/read');

  Future<List<RecurringStream>> listRecurring() async {
    final data = await _c.get('/recurring') as List;
    return data.map((e) => RecurringStream.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<CashFlowForecast> getForecast({int horizonDays = 30}) async => CashFlowForecast.fromJson(
        await _c.get('/forecast?horizon_days=$horizonDays') as Map<String, dynamic>,
      );

  Future<void> registerFcmToken(String token) => _c.post('/settings/fcm-token', {'token': token});
}
